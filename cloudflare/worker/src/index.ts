export default {
  async fetch(request: Request, env: { API_ORIGIN: string }) {
    const url = new URL(request.url);
    // Only proxy API paths
    if (!url.pathname.startsWith('/api/')) {
      return new Response('Not found', { status: 404 });
    }
    const target = new URL(env.API_ORIGIN);
    target.pathname = url.pathname;
    target.search = url.search;

    const init: RequestInit = {
      method: request.method,
      headers: request.headers,
      body: request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.arrayBuffer(),
    };

    const res = await fetch(target.toString(), init);
    return new Response(res.body, { status: res.status, headers: res.headers });
  },
};
