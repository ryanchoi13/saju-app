// Same-origin account calls use HttpOnly cookies. No access/session token in localStorage.
(() => {
    const send = window.fetch.bind(window);
    window.fetch = (input, options = {}) => {
        const url = new URL(typeof input === 'string' ? input : input.url, location.href);
        if (url.origin !== location.origin || !url.pathname.startsWith('/api/')) return send(input, options);
        const headers = new Headers(options.headers || (input instanceof Request ? input.headers : undefined));
        const method = (options.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
        if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers.set('X-Dalha-Request', '1');
        return send(input, {...options, headers, credentials:'same-origin', cache:'no-store'});
    };
})();
