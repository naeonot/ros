# Contributing to ROS

Thanks for considering a contribution.

## Before opening an issue

- Search existing issues to avoid duplicates.
- Include your Termux version, Android version, Python version and the exact ROS command involved.
- Never include API keys, passwords, tokens, private files or personal data in an issue.

## Reporting bugs

Use the Bug report issue template. Include:
- Steps to reproduce.
- Expected and actual behaviour.
- Relevant error output, with secrets and personal paths removed.
- Whether the issue is reproducible in a fresh Termux session.

## Suggesting features

Use the Feature request template. Explain the problem, the proposed behaviour and any security or privacy implications.

## Pull requests

1. Fork the repository and create a focused branch.
2. Keep changes scoped; avoid unrelated UI or behaviour changes.
3. Run the checks below before submitting.
4. Describe the change, its tests and any limitations.

### Local checks

```bash
python -m compileall -q .
python -m json.tool ros_manifest.json >/dev/null
bash -n install.sh
```

If you add or remove runtime files, update `ros_manifest.json` and verify that a fresh install includes the required files.

## Compatibility

ROS is designed for Termux on Android. Compatibility can vary with Android version, CPU architecture, Termux source and optional Termux:API packages. State the environment you tested; do not claim broad compatibility from a single device.
