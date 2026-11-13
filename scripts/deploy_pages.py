"""Deploy reviewed static files to Cloudflare Pages without persisting secrets."""
import argparse
import base64
import getpass
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

API = 'https://api.cloudflare.com/client/v4'


class Cloudflare:
    def __init__(self, token):
        self.token = token
        self.secrets = [token]

    def call(self, path, method='GET', data=None, token=None, content_type=None):
        headers = {'Authorization': 'Bearer ' + (token or self.token), 'User-Agent': 'VideoLoadDeployment/1.0'}
        if data is not None and not isinstance(data, bytes):
            data = json.dumps(data).encode()
            content_type = 'application/json'
        if content_type:
            headers['Content-Type'] = content_type
        req = urllib.request.Request(API + path, method=method, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                error = json.load(exc).get('errors', [])
            except (ValueError, AttributeError):
                error = [{'message': 'Non-JSON API error'}]
            message = json.dumps(error)
            for secret in self.secrets:
                message = message.replace(secret, '[redacted]')
            raise RuntimeError(f'Cloudflare HTTP {exc.code}: {message}') from None
        if not payload.get('success'):
            raise RuntimeError('Cloudflare reported failure; request was not completed')
        return payload.get('result')


def multipart(fields, files):
    boundary = 'videoload-' + uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for name, value in files.items():
        mime = 'application/javascript' if name == '_worker.js' else 'application/json' if name == '_routes.json' else 'text/plain'
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode() + value + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts), 'multipart/form-data; boundary=' + boundary


def source_commit(directory):
    # Deployment is tied to a clean, committed source snapshot.
    root = directory.parent
    clean = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True)
    if clean:
        raise RuntimeError('Commit reviewed source changes before deploying')
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--directory', type=Path, default=Path('dist'))
    parser.add_argument('--domain')
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '').strip()
    if not re.fullmatch(r'[a-f0-9]{32}', account):
        raise RuntimeError('Set CLOUDFLARE_ACCOUNT_ID to the target account ID')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', args.project):
        raise RuntimeError('Invalid Pages project name')
    if args.domain and not re.fullmatch(r'[a-z0-9.-]+', args.domain):
        raise RuntimeError('Invalid domain name')
    directory = args.directory.resolve()
    commit = None if args.status else source_commit(directory)
    token = os.environ.get('CLOUDFLARE_API_TOKEN') or getpass.getpass('Cloudflare API token (hidden): ')
    cf = Cloudflare(token)
    prefix = f'/accounts/{account}/pages/projects'
    projects = cf.call(prefix)
    project = next((p for p in projects if p['name'] == args.project), None)
    if project is None:
        if args.status:
            raise RuntimeError('Project not found')
        project = cf.call(prefix, 'POST', {'name': args.project, 'production_branch': 'main'})
        print('Created Pages project:', project['name'], flush=True)
    elif not args.status and (project.get('source') or project.get('production_branch') != 'main'):
        raise RuntimeError('Existing project uses different deployment settings; refusing to change it')
    endpoint = prefix + '/' + args.project
    if not args.status:
        if not (directory / 'index.html').is_file():
            raise RuntimeError('Build the website first; index.html is missing')
        jwt = cf.call(endpoint + '/upload-token')['jwt']
        cf.secrets.append(jwt)
        manifest, assets = {}, {}
        for file in sorted(directory.rglob('*')):
            if not file.is_file() or file.name in {'_headers', '_redirects', '_worker.js', '_routes.json'}:
                continue
            relative = file.relative_to(directory).as_posix()
            if file.is_symlink() or any(part.startswith('.') for part in Path(relative).parts):
                raise RuntimeError('Hidden files and symlinks are not deployable')
            if file.suffix not in {'.html', '.css', '.json', '.xml', '.txt', '.png'}:
                raise RuntimeError('Unexpected deployment asset type: ' + relative)
            raw = file.read_bytes()
            if len(raw) > 25 * 1024 * 1024:
                raise RuntimeError('Asset exceeds Pages upload limit')
            key = hashlib.sha256(raw + file.suffix.encode()).hexdigest()[:32]
            manifest['/' + relative] = key
            mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            if file.suffix in {'.html', '.css', '.txt', '.xml'}:
                mime += '; charset=utf-8'
            assets[key] = {'key': key, 'value': base64.b64encode(raw).decode(), 'base64': True, 'metadata': {'contentType': mime}}
        missing = cf.call('/pages/assets/check-missing', 'POST', {'hashes': list(assets)}, token=jwt)
        batch = [assets[key] for key in missing]
        # This product site is small; cap requests to ten files per upload.
        for start in range(0, len(batch), 10):
            cf.call('/pages/assets/upload', 'POST', batch[start:start+10], token=jwt)
        cf.call('/pages/assets/upsert-hashes', 'POST', {'hashes': list(assets)}, token=jwt)
        special = {name: (directory / name).read_bytes() for name in ('_headers', '_redirects', '_worker.js', '_routes.json') if (directory / name).is_file()}
        fields = {'manifest': json.dumps(manifest), 'branch': 'main', 'commit_hash': commit, 'commit_dirty': 'false', 'commit_message': 'Publish VideoLoad product website'}
        body, mime = multipart(fields, special)
        deployment = cf.call(endpoint + '/deployments', 'POST', body, content_type=mime)
        deployment_id = deployment['id']
        print('Deployment created:', deployment_id, flush=True)
        for _ in range(24):
            deployment = cf.call(endpoint + '/deployments/' + deployment_id)
            stage = deployment.get('latest_stage', {})
            print('Deployment stage:', stage.get('name'), stage.get('status'), flush=True)
            if stage.get('name') == 'deploy' and stage.get('status') == 'success':
                break
            if stage.get('status') in {'failure', 'canceled'}:
                raise RuntimeError('Deployment did not succeed')
            time.sleep(3)
        else:
            raise RuntimeError('Deployment still pending; inspect the existing deployment before retrying')
    else:
        deployment = project.get('canonical_deployment') or {}
    domain = None
    if args.domain:
        domains = cf.call(endpoint + '/domains')
        domain = next((d for d in domains if d['name'] == args.domain), None)
        if domain is None and not args.status:
            domain = cf.call(endpoint + '/domains', 'POST', {'name': args.domain})
    result = {'project': project['name'], 'pages_url': 'https://' + project['subdomain'], 'deployment_url': deployment.get('url'), 'deployment_id': deployment.get('id'), 'source_commit': commit or deployment.get('deployment_trigger', {}).get('metadata', {}).get('commit_hash'), 'domain': domain, 'dns_cname_target': project['subdomain']}
    # Includes only public deployment and DNS metadata, never tokens or account credentials.
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, urllib.error.URLError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
