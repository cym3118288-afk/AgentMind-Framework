# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :x:                |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

We take the security of AgentMind seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please do NOT:

- Open a public GitHub issue
- Discuss the vulnerability in public forums or social media

### Please DO:

1. Email the details to: security@agentmind.dev (or cym3118288@gmail.com)
2. Include the following information:
   - Type of vulnerability
   - Full paths of source file(s) related to the vulnerability
   - Location of the affected source code (tag/branch/commit or direct URL)
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### What to Expect

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will send a more detailed response within 7 days indicating the next steps
- We will keep you informed of the progress towards a fix
- We may ask for additional information or guidance

### Disclosure Policy

- We will coordinate with you on the disclosure timeline
- We prefer to fully remediate vulnerabilities before public disclosure
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

- [Your name could be here!]

Thank you to all researchers who help keep AgentMind secure.

## Security Best Practices for Users

When using AgentMind:

1. **API Keys**: Never commit API keys to version control. Use environment variables.
2. **Input Validation**: Always validate and sanitize user inputs before passing to agents.
3. **Tool Permissions**: Be cautious when giving agents access to tools that can modify system state.
4. **LLM Providers**: Use trusted LLM providers and keep credentials secure.
5. **Dependencies**: Keep AgentMind and its dependencies up to date.
6. **Sandboxing**: Consider running agents in isolated environments for sensitive operations.

## Known Security Considerations

- **LLM Prompt Injection**: Agents may be susceptible to prompt injection attacks. Validate inputs.
- **Tool Execution**: Tools executed by agents run with the permissions of the Python process.
- **Memory Storage**: Conversation history may contain sensitive information. Secure storage appropriately.

## Security Updates

Security updates will be released as patch versions and announced via:
- GitHub Security Advisories
- Release notes
- README updates

Thank you for helping keep AgentMind and its users safe!
