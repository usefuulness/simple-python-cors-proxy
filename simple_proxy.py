import http.server
import http.client
import urllib.parse
import os

# Configuration: target API base URL (e.g. "https://api.example.com")
TARGET_API = os.environ.get("TARGET_API", "https://api.example.com")
# Whitelisted origins (comma-separated), e.g. "http://localhost:5173"
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(',')

parsed_target = urllib.parse.urlparse(TARGET_API)
TARGET_SCHEME = parsed_target.scheme
TARGET_HOST = parsed_target.netloc

# Hop-by-hop headers that should not be forwarded
HOP_HEADERS = {
    'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
    'te', 'trailers', 'transfer-encoding', 'upgrade'
}

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def _get_request_origin(self):
        # Always take the first origin if multiple are comma-separated
        origin_header = self.headers.get('Origin', '')
        parts = [o.strip() for o in origin_header.split(',') if o.strip()]
        return parts[0] if parts else None

    def _send_cors_headers(self):
        origin = self._get_request_origin()
        # Use allowed origin or default to first
        allow = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
        # Indicate that responses vary by Origin
        self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Origin', allow)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, POST, PUT, DELETE, OPTIONS, PATCH')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept')
        self.send_header('Access-Control-Expose-Headers', 'Set-Cookie')

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_HEAD(self): return self._proxy_request()
    def do_GET(self): return self._proxy_request()
    def do_POST(self): return self._proxy_request()
    def do_PUT(self): return self._proxy_request()
    def do_DELETE(self): return self._proxy_request()
    def do_PATCH(self): return self._proxy_request()

    def _proxy_request(self):
        # Read request body if present
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else None

        # Prepare headers for forwarding to upstream
        forward_headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in HOP_HEADERS and k.lower() != 'host'
        }
        forward_headers['Host'] = TARGET_HOST

        # Forward any incoming cookies to the target API
        cookies = []
        try:
            cookies = self.headers.get_all('Cookie') or []
        except Exception:
            single = self.headers.get('Cookie')
            if single:
                cookies = [single]
        if cookies:
            forward_headers['Cookie'] = '; '.join(cookies)

        # Forward request to target API
        conn = (http.client.HTTPSConnection if TARGET_SCHEME == 'https' else http.client.HTTPConnection)(TARGET_HOST)
        conn.request(self.command, self.path, body=body, headers=forward_headers)
        res = conn.getresponse()
        res_body = res.read()

        # Send response status
        self.send_response(res.status, res.reason)
        # Send our own CORS headers
        self._send_cors_headers()
        # Forward upstream headers, excluding hop-by-hop and any CORS headers
        for header, value in res.getheaders():
            lk = header.lower()
            if lk in HOP_HEADERS:
                continue
            # Skip any upstream CORS headers to prevent duplicates
            if lk.startswith('access-control-') or lk == 'vary':
                continue
            if lk == 'set-cookie':
                # Strip Domain and Path from upstream cookie, then enforce global path and cross-site
                parts = [p for p in value.split(';') if not p.strip().lower().startswith(('domain=','path='))]
                # Preserve HttpOnly, Secure if present
                # Set cookie for all paths
                parts.append('Path=/')
                # Allow cross-site cookie
                parts.append('SameSite=None')
                parts.append('Secure')  # required for SameSite=None in modern browsers
                new_cookie = '; '.join(parts)
                self.send_header('Set-Cookie', new_cookie)
            else:
                self.send_header(header, value)
        self.end_headers()

        # Write response body for non-HEAD requests
        if self.command != 'HEAD':
            self.wfile.write(res_body)
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server_address = ('', port)
    httpd = http.server.ThreadingHTTPServer(server_address, ProxyHandler)
    print(f"Proxy server listening on port {port}, forwarding to {TARGET_API}")
    httpd.serve_forever()
