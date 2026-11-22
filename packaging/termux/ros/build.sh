TERMUX_PKG_HOMEPAGE=https://github.com/naeonot/ros
TERMUX_PKG_DESCRIPTION="Lightweight personal system dashboard for Termux"
TERMUX_PKG_LICENSE="MIT"
TERMUX_PKG_MAINTAINER="naeonot"
TERMUX_PKG_VERSION=1.0.0
TERMUX_PKG_SRCURL=git+https://github.com/naeonot/ros
TERMUX_PKG_GIT_BRANCH=ros-v1.0.0
TERMUX_PKG_DEPENDS="python, python-pip"
TERMUX_PKG_PYTHON_RUNTIME_DEPS="rich==15.0.0"
TERMUX_PKG_PLATFORM_INDEPENDENT=true

termux_step_make_install() {
    local appdir="$TERMUX_PREFIX/lib/rana-os"

    install -Dm644 "$TERMUX_PKG_SRCDIR/main.py" "$appdir/main.py"
    install -Dm644 "$TERMUX_PKG_SRCDIR/core/__init__.py" "$appdir/core/__init__.py"
    install -Dm644 "$TERMUX_PKG_SRCDIR/core/banner.py" "$appdir/core/banner.py"
    install -Dm644 "$TERMUX_PKG_SRCDIR/core/system.py" "$appdir/core/system.py"
    install -Dm644 "$TERMUX_PKG_SRCDIR/setname.py" "$appdir/setname.py"
    install -Dm644 "$TERMUX_PKG_SRCDIR/setcolor.py" "$appdir/setcolor.py"

    cat > "$TERMUX_PREFIX/bin/ros" <<EOF
#!$TERMUX_PREFIX/bin/sh
exec "$TERMUX_PREFIX/bin/python" "$appdir/main.py" "\$@"
EOF
    chmod 0755 "$TERMUX_PREFIX/bin/ros"

    cat > "$TERMUX_PREFIX/bin/ros-setname" <<EOF
#!$TERMUX_PREFIX/bin/sh
exec "$TERMUX_PREFIX/bin/python" "$appdir/setname.py" "\$@"
EOF
    chmod 0755 "$TERMUX_PREFIX/bin/ros-setname"

    cat > "$TERMUX_PREFIX/bin/ros-setcolor" <<EOF
#!$TERMUX_PREFIX/bin/sh
exec "$TERMUX_PREFIX/bin/python" "$appdir/setcolor.py" "\$@"
EOF
    chmod 0755 "$TERMUX_PREFIX/bin/ros-setcolor"
}
