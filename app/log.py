"""
Author: Ian Young
Purpose: Set a unified logger across all scripts.
"""

import logging

LOG_LEVEL = logging.DEBUG

class CenterAlignFormatter(logging.Formatter):
    """Custom logging formatter that center-aligns the level name.

    This formatter modifies the level name of log records to be
        center-aligned within a width of 10 characters, enhancing the
        visual appearance of log messages.
    """

    def format(self, record):
        """Format the specified log record.

        Args:
            record: The log record to format.

        Returns:
            The formatted log message as a string.
        """
        # Center-align levelname within 10 characters
        levelname = record.levelname.center(8)
        record.levelname = levelname
        return super().format(record)


# Set logging
log = logging.getLogger()
log.setLevel(LOG_LEVEL)

# Set up the custom formatter
formatter = CenterAlignFormatter(
    fmt="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

# Add the handler to the logger
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
log.addHandler(console_handler)
