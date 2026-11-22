# RANA OS

A lightweight terminal system dashboard for Termux.

## Features

- Custom RANA banner
- Android and Termux system information
- Configurable banner name and HEX theme colour
- Built with Python and Rich

## Requirements

- Termux on Android
- Python 3
- Python package: `rich`

## Run from source

```bash
pkg update
pkg install python git
pip install rich
git clone https://github.com/naeonot/ros.git
cd ros
python main.py
```

## Customization

```bash
python setname.py YOURNAME
python setcolor.py 00ffff
```

Configuration is stored in `~/.config/rana-os/config.json`.

## License

MIT. See [LICENSE](LICENSE).

> The one-command `pkg install ros` package is not published yet. This source installation method works now.