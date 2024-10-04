"""
Author: Ian Young
Purpose: Set a unified logger across all scripts.
"""

import logging
from time import time

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


def logging_decorator(func):
    """Decorator that logs the execution of a function.

    This decorator logs the function name and its arguments before
    execution, and logs a message upon completion. It is useful for
    tracking the flow of function calls and debugging.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        Callable: The wrapped function with logging functionality.
    """

    def wrapper(*args, **kwargs):
        """Logs the execution of a decorated function.

        This function logs the name of the function being executed along
        with its arguments before calling the function. It also logs a
        message upon the function's completion, providing insight into
        the function's execution flow.

        Args:
            *args: Variable length argument list for the decorated
                function.
            **kwargs: Arbitrary keyword arguments for the decorated
                function.
        Returns:
            None
        """
        log.debug("Running %s with argument(s): %.15s", func.__name__, args)
        result = func(*args, **kwargs)
        log.debug(
            "%s finished its task with return value(s) of: %.15s",
            func.__name__,
            str(result),
        )
        return result

    return wrapper


def time_function(func):
    """Decorator that measures the execution time of a function.

    This decorator records the time taken for a function to execute and
    logs the duration upon completion. It is useful for performance
    monitoring and optimization.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        Callable: The wrapped function with timing functionality.
    """

    def wrapper(*args, **kwargs):
        """Measures and logs the execution time of a decorated function.

        This function captures the start time before executing the
        decorated function and logs the time taken for the function to
        complete. It provides insight into the performance of the function
        being executed.

        Args:
            *args: Variable length argument list for the decorated function.
            **kwargs: Arbitrary keyword arguments for the decorated function.
        Returns:
            None
        """
        start_time = time()
        result = func(*args, **kwargs)
        log.debug(
            "%s's process completed in %.2f milliseconds.",
            func.__name__,
            (time() - start_time) * 1000,
        )
        return result

    return wrapper
