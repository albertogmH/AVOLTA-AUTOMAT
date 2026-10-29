# Security Checklist

Apply to sensitive changes regardless of path; filename patterns are only hints.

- Validate untrusted inputs at explicit trust boundaries.
- Enforce authentication and authorization on the server, including cross-user access.
- Use framework-safe database APIs, parameterized queries and output escaping.
- Review CSRF, XSS, SSRF, injection, deserialization, uploads and traversal as applicable.
- Preserve secure sessions, cookies, headers, CORS, rate limits and deployment defaults.
- Keep credentials out of code, client bundles and logs; minimize sensitive data exposure.
- Review dependency/supply-chain changes using available evidence and approved tools.
- Test unauthorized access, malformed data, abuse cases and security regressions.
- Do not run destructive tests, use production secrets or attack external systems.
- Distinguish confirmed vulnerabilities from hypotheses; record impact and preconditions.
- Report audit scope, remediation, verification and unexecuted checks.
- No identified vulnerability is not proof that the system is secure.