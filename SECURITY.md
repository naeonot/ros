# Security Policy

## Supported version

Security fixes are applied to the latest code on the `main` branch. There are no formal stable releases yet.

## Reporting a vulnerability

Please do not publish exploitable security details in a public issue.

If GitHub's private vulnerability reporting is enabled for this repository, use the repository's **Security → Report a vulnerability** flow. Otherwise, contact the maintainer through the GitHub profile and request a private reporting channel.

Include:
- A concise description and potential impact.
- Steps to reproduce or a proof of concept that does not expose real credentials or user data.
- The affected commit or file, if known.

Do not include real API keys, passwords, access tokens, private data or other people's information.

## Security notes

- Review installer and updater code before running it.
- Keep ORACLE API keys in the local Termux configuration; never commit them.
- ROS's downloader checks are best-effort and are not a malware scanner.
- Reported vulnerabilities will be triaged as time and maintainer capacity allow.
