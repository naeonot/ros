# RANA OS

A lightweight terminal system dashboard for Termux.

## Install on Termux

### Option 1: Download ZIP (no install URL command)

1. Open the [RANA OS repository](https://github.com/naeonot/ros).
2. Tap **Code → Download ZIP**.
3. Extract `ros-main.zip` using your file manager.
4. In Termux, install Python and allow storage access:

   ```bash
   pkg install python
   termux-setup-storage
   ```

5. Run the installer from the extracted folder (usually named `ros-main`):

   ```bash
   cd ~/storage/downloads/ros-main && python install.py
   ```

6. Start RANA OS:

   ```bash
   ros
   ```

The installer installs the required `rich` library and sets up the `ros` command automatically. No Git installation is required.

### Option 2: Install directly with one command

First install Python:

```bash
pkg install python
```

Then run:

```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/naeonot/ros/main/install.py').read())"
```

Start RANA OS with:

```bash
ros
```

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
