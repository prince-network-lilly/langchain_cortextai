# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.6.x   | :white_check_mark: |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in CortexChain, please report it responsibly:

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly with details of the vulnerability
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: Within 2 business days
- **Initial Assessment**: Within 5 business days
- **Fix/Patch**: Within 14 business days for critical issues

## Security Features

CortexChain includes several built-in security features:

### Prompt Injection Defense

```python
from cortexchain.security import sanitize_input, InputSanitizer

# Automatic detection and blocking
text = sanitize_input(user_input, check_injection=True)

# Wrap chains for automatic protection
sanitizer = InputSanitizer(check_injection=True)
safe_chain = sanitizer.wrap(my_chain)
```

### Input Sanitization

- HTML/script tag stripping
- Control character removal
- Length limiting
- Custom pattern blocking

### Sensitive Data Redaction

```python
from cortexchain.security import redact_sensitive

# Redacts emails, phone numbers, SSNs, API keys, tokens
safe_log = redact_sensitive(raw_output)
```

### Tool Safety

- `SQLDatabaseTool`: Read-only mode by default
- `ShellTool`: Command whitelist enforcement
- `HTTPRequestTool`: Domain whitelist support
- `WriteFileTool`: Path validation

### CI/CD Security

- **Dependabot**: Automatic dependency updates
- **pip-audit**: Vulnerability scanning
- **Bandit**: Static analysis for Python security issues
- **TruffleHog**: Secrets detection in commits
- **CodeQL**: GitHub's semantic code analysis

## Best Practices

When using CortexChain in production:

1. **Always sanitize user inputs** before passing to LLM chains
2. **Use rate limiting** to prevent abuse
3. **Enable logging** for audit trails
4. **Set tool restrictions** (read-only DB, command whitelists)
5. **Never log raw LLM responses** that may contain user PII — use `redact_sensitive()` first
6. **Keep dependencies updated** via Dependabot alerts
7. **Review agent actions** before deploying autonomous workflows
