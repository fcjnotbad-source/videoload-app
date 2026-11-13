// Preserve legacy product links and support seeking in the public product film.
const canonicalOrigin = "__CANONICAL_ORIGIN__";
const legacyHosts = new Set(["app.pdos.work", "videoload-app.pages.dev"]);

function sliceStream(body, start, end) {
  const reader = body.getReader();
  let offset = 0;
  return new ReadableStream({
    async pull(controller) {
      while (true) {
        const { value, done } = await reader.read();
        if (done) { controller.close(); return; }
        const chunkStart = offset;
        offset += value.byteLength;
        if (offset <= start) continue;
        const from = Math.max(0, start - chunkStart);
        const to = Math.min(value.byteLength, end + 1 - chunkStart);
        if (to > from) controller.enqueue(value.subarray(from, to));
        if (offset > end) { controller.close(); await reader.cancel(); }
        return;
      }
    },
    cancel(reason) { return reader.cancel(reason); },
  });
}

async function serveMedia(request, assets, ctx) {
  const response = await assets.fetch(request);
  const total = Number(response.headers.get("Content-Length"));
  if (response.status !== 200 || !Number.isSafeInteger(total) || total <= 0) return response;
  const headers = new Headers(response.headers);
  headers.set("Accept-Ranges", "bytes");
  const range = request.headers.get("Range");
  const ifRange = request.headers.get("If-Range");
  const sameVersion = !ifRange || (!ifRange.startsWith("W/")
    && (ifRange === headers.get("ETag") || ifRange === headers.get("Last-Modified")));
  const match = range && /^bytes=(\d*)-(\d*)$/.exec(range);
  if (request.method !== "GET" || !match || !sameVersion) {
    return new Response(response.body, { status: response.status, headers });
  }
  let start, end;
  if (match[1]) {
    start = Number(match[1]);
    end = match[2] ? Math.min(Number(match[2]), total - 1) : total - 1;
  } else {
    const suffix = Number(match[2]);
    start = Math.max(0, total - suffix);
    end = total - 1;
  }
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || start >= total || end < start || (!match[1] && Number(match[2]) <= 0)) {
    await response.body?.cancel();
    headers.set("Content-Range", `bytes */${total}`);
    headers.set("Content-Length", "0");
    return new Response(null, { status: 416, headers });
  }
  headers.set("Content-Range", `bytes ${start}-${end}/${total}`);
  headers.set("Content-Length", String(end - start + 1));
  // Workers derives Content-Length from a fixed-length body, not a manual header.
  const { readable, writable } = new FixedLengthStream(end - start + 1);
  ctx.waitUntil(sliceStream(response.body, start, end).pipeTo(writable));
  return new Response(readable, { status: 206, headers });
}

export default {
  async fetch(request, env, ctx) {
    const source = new URL(request.url);
    if (legacyHosts.has(source.hostname) && !source.pathname.startsWith("/.well-known/acme-challenge/")) {
      const target = new URL(canonicalOrigin);
      target.pathname = source.pathname;
      target.search = source.search;
      return Response.redirect(target.toString(), 301);
    }
    if (source.pathname.endsWith(".mp4")) return serveMedia(request, env.ASSETS, ctx);
    return env.ASSETS.fetch(request);
  },
};
