# TUR package preparation

This recipe targets the Termux User Repository (TUR), not the official
Termux package repository.

## Package

- Package name: `ros`
- Intended install after TUR is enabled: `pkg install ros`
- Runtime: Termux Python and Rich 15.0.0
- Source: the `ros-v1.0.0` branch of `naeonot/ros`

## User installation path

A user first enables TUR:

```sh
pkg install tur-repo
pkg update
pkg install ros
```

Then launch with:

```sh
ros
```

## Status

The recipe is prepared for TUR review. A successful build in the earlier
official Termux build workflow does not establish that this TUR recipe has
passed TUR CI or been accepted/merged. Do not announce it as installable
until the TUR pull request is accepted and the package appears in the repo.
