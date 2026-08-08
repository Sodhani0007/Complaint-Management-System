# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately rather than
opening a public issue — email the maintainer or use GitHub's private vulnerability reporting
feature on this repository.

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce
- Any relevant logs or screenshots

## Known Security Considerations for This Project

This is a demo/assignment project, not a hardened production system. Notably:

- **No authentication is implemented.** Routers are structured so `Depends(get_current_user)`
  could be added without restructuring, but nothing gates access currently — do not deploy this
  publicly without adding auth first.
- **Secrets**: `GROQ_API_KEY` and `DATABASE_URL` must be supplied via environment variables /
  `.env` (never committed — see `.gitignore`). `.env.example` contains placeholders only.
- **File uploads**: validated for extension and size (`MAX_UPLOAD_SIZE_MB`), but not scanned for
  malicious content — don't accept uploads from untrusted sources in a production deployment
  without adding that.
- **CORS**: `CORS_ORIGINS` defaults to localhost dev origins; update this before deploying.

## Supported Versions

This project does not currently maintain multiple release branches — security fixes apply to the
latest `main` only.
