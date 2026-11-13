// Host-only redirects keep old product links useful after the domain move.
const canonicalOrigin = "__CANONICAL_ORIGIN__";
const legacyHosts = new Set(["app.pdos.work", "videoload-app.pages.dev"]);

export default {
  async fetch(request, env) {
    const source = new URL(request.url);
    if (
      legacyHosts.has(source.hostname) &&
      !source.pathname.startsWith("/.well-known/acme-challenge/")
    ) {
      const target = new URL(canonicalOrigin);
      target.pathname = source.pathname;
      target.search = source.search;
      return Response.redirect(target.toString(), 301);
    }
    return env.ASSETS.fetch(request);
  },
};
