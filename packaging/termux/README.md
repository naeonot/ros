# Termux package draft

This directory contains a **draft** Termux package recipe for review.

- Package name: `ros`
- Intended install: `pkg install ros`
- Runtime dependency: Python
- Python runtime dependency: Rich 15.0.0, declared through Termux's Python runtime-dependency mechanism.
- Source is pinned to commit `52cb360c2f4fcf15e5515761892266007d6ec148` for reproducibility.

## Status

This is not yet an installable Termux package and does not make `pkg install ros` available. The recipe still needs to be built and tested with the official Termux packaging system, checked against current packaging policy, and submitted to the Termux maintainers. Only after acceptance and publication in a configured Termux repository will users be able to run `pkg install ros` directly.

The official Termux contribution guide cautions against submitting untested or low-quality package pull requests. Do not treat this draft as approved.
