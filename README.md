# RANA OS

A lightweight terminal system dashboard for Termux.

## Install on Termux

First install Python:

```bash
pkg install python
```

Then install RANA OS with this single command:

```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/naeonot/ros/main/install.py').read())"
```

After installation, launch it with:

```bash
ros
```

The installer downloads the app files and installs the required `rich` Python library automatically. No Git installation is required.

## Features

- Custom RANA banner
- Android and Termux system information
- Configurable banner name and HEX theme colour
- Built with Python and Rich

## Customization

From the project source folder, run:

```bash
python setname.py YOURNAME
python setcolor.py 00ffff
```

Configuration is stored in `~/.config/rana-os/config.json`.

## License

MIT. See [LICENSE](LICENSE).
