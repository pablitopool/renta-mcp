# Security Policy

## Supported Versions

This project is under active development. Security fixes are applied to the latest version in `master`.

## Reporting a Vulnerability

Please do not open public GitHub issues for suspected vulnerabilities.

- Preferred: use GitHub private vulnerability reporting (Security tab -> Report a vulnerability).
- Alternative: contact the maintainer directly and include:
  - a clear description of the issue,
  - impact and attack scenario,
  - reproduction steps or proof of concept,
  - affected commit/version if known.

## Response Process

- Initial acknowledgment target: within 72 hours.
- Triage and severity assessment after acknowledgment.
- Patch and coordinated disclosure timeline depends on severity and exploitability.

## Scope

In scope:
- vulnerabilities in server endpoints (`/mcp`, `/health`),
- input validation and tool execution paths,
- dependency vulnerabilities with practical impact.

Out of scope:
- purely theoretical issues without reproducible impact,
- social engineering and physical attacks,
- issues in third-party services outside this repository.
