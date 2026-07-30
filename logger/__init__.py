"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./logger/__init__.py

Description:

    Logging utilities for the Viewline application.

    This module configures the application's logging system and provides a reusable logger instance with a consistent output format.
    It also includes small helper utilities used during development and debugging.

Responsibilities:
    - Create configured logger instances.
    - Apply a consistent log format.
    - Prevent duplicate log handlers.
    - Output log messages to the console.
    - Provide simple debugging helpers.

Features:
    - Named logger creation.
    - Standardized timestamp formatting.
    - Console logging.
    - Duplicate handler protection.
    - Propagation disabled.
    - Blank line helper.

Architecture:
    getLogger()
        └── logging.Logger

    nextline()

Nodes:
    getLogger
    nextline
"""

from __future__ import absolute_import

import sys
import logging


def getLogger(name):
    """Create and return a configured logger instance.

    This function creates a standardized logger used throughout the
    Review Player framework.

    If the logger already contains handlers, new handlers will not
    be added again. This prevents duplicate logging output.

    The logger output format includes:
        - Timestamp
        - Log level
        - Module name
        - Source line number
        - Message

    Args:
        name (str):
            Logger name, typically ``__name__``.

    Returns:
        logging.Logger:
            Configured logger instance.

    Example:
        >>> import logger
        >>> LOGGER = logger.getLogger(__name__)
        >>> LOGGER.info("Viewer initialized")

    Output:
        # 2026/05/20 10:15:12:PM    INFO:
        playback.player-line: 45 | Playback started

    Notes:
        - Logging level defaults to ``logging.INFO``.
        - Output stream uses ``sys.stdout``.
        - Logger propagation is disabled.
    """

    # Create or retrieve the named logger.
    logger = logging.getLogger(name)

    # Set the minimum logging level.
    logger.setLevel(logging.INFO)

    # Configure the logger only once.
    if not logger.handlers:
        # Log message format.
        format = "# %(asctime)s%(levelname)8s: %(name)s-line: %(lineno)d | %(message)s"

        # Timestamp format.
        date = "%Y/%m/%d %I:%M:%S:%p"

        # Create the formatter.
        formatter = logging.Formatter(fmt=format, datefmt=date)

        # Create a console output handler.
        handler = logging.StreamHandler(stream=sys.stdout)

        # Apply the formatter.
        handler.setFormatter(formatter)

        # Attach the handler to the logger.
        logger.addHandler(handler)

        # Prevent duplicate logging from parent loggers.
        logger.propagate = False

    # Return the configured logger.
    return logger


def nextline():
    """Print a blank line to the console.

    This helper is primarily used during debugging to visually separate groups of console output, making log messages easier to read.

    Returns:
        None
    """

    # Print an empty line.
    print("\n")


if __name__ == "__main__":
    pass
