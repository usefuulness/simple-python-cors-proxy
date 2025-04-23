# simple-python-cors-proxy

**A lightweight Python reverse proxy with built-in CORS support and cookie rewriting, implemented using only the standard library.**

## Description

This repository provides a minimal HTTP(S) proxy server in pure Python (no third-party dependencies). It forwards requests from your frontend to a configured target API, handles Cross-Origin Resource Sharing (CORS) automatically, and rewrites `Set-Cookie` headers so that session cookies appear to come from the proxy’s own domain. No Dependencies.

Key features:

- Full support for CORS preflight (`OPTIONS`) and credentialed requests
- Automatic forwarding of request headers and bodies
- Strips upstream `Domain`/`Path` attributes and enforces `SameSite=None; Secure` on cookies
- Whitelists allowed origins via environment variable
- No dependencies beyond Python 3’s standard library

## Prerequisites

- Python 3.7 or newer

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/simple-python-cors-proxy.git
   cd simple-python-cors-proxy
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

## Configuration

Configure the proxy by setting environment variables:

- `TARGET_API` (required): Base URL of the API you want to proxy to. Example:
  ```bash
  export TARGET_API="https://api.example.com"
  ```

- `ALLOWED_ORIGINS` (optional): Comma-separated list of allowed origins for CORS. Defaults to `http://localhost:5173`.
  ```bash
  export ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000"
  ```

- `PORT` (optional): Port on which to run the proxy. Defaults to `8000`.
  ```bash
  export PORT=8000
  ```

## Usage

Start the proxy server:

```bash
python proxy.py
```

Example fetch from a React app:

```js
fetch('http://localhost:8000/api/users/@me', {
  credentials: 'include',
}).then(res => res.json()).then(data => console.log(data));
```

## Directory Structure

```
├── proxy.py       # Main proxy implementation
└── README.md      # This documentation
```

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests for bug fixes, new features, or documentation improvements.

## License

This project is licensed under the [MIT License](LICENSE).

powered by UsefulMedia
