from __future__ import annotations

import argparse
import sys

from loguru import logger
from PyQt5 import QtWidgets

from labelvid import __appname__
from labelvid import __version__
from labelvid.app import MainWindow


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=__appname__,
        description="Video Clipping Tool for Frame Extraction",
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="Video file or directory containing videos",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory for extracted frames",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"{__appname__} {__version__}",
    )
    args = parser.parse_args()

    logger.info("Starting {} version {}", __appname__, __version__)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__appname__)

    win = MainWindow(
        filename=args.filename,
        output_dir=args.output,
    )
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
