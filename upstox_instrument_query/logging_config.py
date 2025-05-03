"""Logging configuration for the Upstox Instrument Query package.

This module provides centralized logging configuration with support for
different log levels, log rotation, and log management features.
"""

import logging
import logging.handlers
import os
import shutil
from datetime import datetime
from typing import Dict, Optional, Union

DEFAULT_LOG_DIR = os.path.join(
    os.path.expanduser("~"), ".upstox_instrument_query", "logs"
)


LOG_FILES = {
    "main": "upstox_query.log",
    "database": "database.log",
    "api": "api_calls.log",
    "query": "queries.log",
}


DEFAULT_LOG_LEVEL = logging.INFO


MAX_LOG_SIZE = 5 * 1024 * 1024


BACKUP_COUNT = 10


ARCHIVE_RETENTION_DAYS = 30


def ensure_log_directory(log_dir: Optional[str] = None) -> str:
    """
    Ensure the log directory exists.

    Args:
        log_dir: Custom log directory path (uses default if None)

    Returns:
        str: Path to the log directory
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_log_file_path(log_name: str, log_dir: Optional[str] = None) -> str:
    """
    Get the full path to a log file.

    Args:
        log_name: Name of the log file ('main', 'database', 'api', 'query')
        log_dir: Custom log directory path (uses default if None)

    Returns:
        str: Full path to the log file
    """
    if log_name not in LOG_FILES:
        raise ValueError(
            f"Invalid log name: {log_name}. Valid names: {list(LOG_FILES.keys())}"
        )

    log_dir = ensure_log_directory(log_dir)
    return os.path.join(log_dir, LOG_FILES[log_name])


def configure_logging(
    log_dir: Optional[str] = None,
    log_level: Union[int, str] = DEFAULT_LOG_LEVEL,
    log_to_console: bool = False,
) -> Dict[str, logging.Logger]:
    """
    Configure the logging system for the package.

    Args:
        log_dir: Directory for log files (uses default if None)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to also log to console

    Returns:
        Dict[str, logging.Logger]: Dictionary of configured loggers
    """
    log_dir = ensure_log_directory(log_dir)

    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper())

    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"
    )
    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger("upstox_instrument_query")
    root_logger.setLevel(log_level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

    loggers = {}

    for log_name in LOG_FILES:
        logger_name = f"upstox_instrument_query.{log_name}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = False

        log_file = os.path.join(log_dir, LOG_FILES[log_name])
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(log_level)

        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        logger.addHandler(file_handler)

        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(simple_formatter)
            console_handler.setLevel(log_level)
            logger.addHandler(console_handler)

        loggers[log_name] = logger

    return loggers


def get_logger(
    logger_name: str = "main",
    log_dir: Optional[str] = None,
    log_level: Union[int, str] = DEFAULT_LOG_LEVEL,
) -> logging.Logger:
    """
    Get a configured logger by name.

    Args:
        logger_name: Name of the logger ('main', 'database', 'api', 'query')
        log_dir: Custom log directory path (uses default if None)
        log_level: Logging level

    Returns:
        logging.Logger: Configured logger instance
    """
    full_logger_name = f"upstox_instrument_query.{logger_name}"
    logger = logging.getLogger(full_logger_name)

    if not logger.handlers:
        log_dir = ensure_log_directory(log_dir)
        log_file = os.path.join(log_dir, LOG_FILES.get(logger_name, LOG_FILES["main"]))

        if isinstance(log_level, str):
            log_level = getattr(logging, log_level.upper())

        logger.setLevel(log_level)
        logger.propagate = False

        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"
        )
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)

    return logger


def clear_logs(log_name: Optional[str] = None, log_dir: Optional[str] = None) -> list:
    """
    Clear log files.

    Args:
        log_name: Specific log to clear (clears all if None)
        log_dir: Custom log directory path (uses default if None)

    Returns:
        list: List of cleared log files
    """
    log_dir = ensure_log_directory(log_dir)
    cleared_files = []

    if log_name:
        if log_name not in LOG_FILES:
            raise ValueError(
                f"Invalid log name: {log_name}. Valid names: {list(LOG_FILES.keys())}"
            )
        log_files = [LOG_FILES[log_name]]
    else:
        log_files = list(LOG_FILES.values())

    for log_file in log_files:
        file_path = os.path.join(log_dir, log_file)

        if os.path.exists(file_path):
            with open(file_path, "w") as _:
                pass
            cleared_files.append(file_path)

        for i in range(1, BACKUP_COUNT + 1):
            rotated_file = f"{file_path}.{i}"
            if os.path.exists(rotated_file):
                os.remove(rotated_file)
                cleared_files.append(rotated_file)

    return cleared_files


def archive_logs(log_dir: Optional[str] = None) -> str:
    """
    Archive all logs into a timestamped zip file.

    Args:
        log_dir: Custom log directory path (uses default if None)

    Returns:
        str: Path to the created archive
    """
    log_dir = ensure_log_directory(log_dir)
    archive_dir = os.path.join(log_dir, "archives")
    os.makedirs(archive_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"logs_archive_{timestamp}"
    archive_path = os.path.join(archive_dir, archive_name)

    logger = get_logger()
    logger.info(f"Archiving logs to {archive_path}.zip")
    shutil.make_archive(archive_path, "zip", log_dir)

    return f"{archive_path}.zip"


def clean_old_archives(
    log_dir: Optional[str] = None, days: int = ARCHIVE_RETENTION_DAYS
) -> list:
    """
    Remove archives older than the specified number of days.

    Args:
        log_dir: Custom log directory path (uses default if None)
        days: Number of days to keep archives

    Returns:
        list: List of removed archive files
    """
    log_dir = ensure_log_directory(log_dir)
    archive_dir = os.path.join(log_dir, "archives")

    if not os.path.exists(archive_dir):
        return []

    removed_files = []
    current_time = datetime.now().timestamp()
    max_age = days * 24 * 60 * 60

    for filename in os.listdir(archive_dir):
        if not filename.endswith(".zip"):
            continue

        file_path = os.path.join(archive_dir, filename)
        file_age = current_time - os.path.getmtime(file_path)

        if file_age > max_age:
            os.remove(file_path)
            removed_files.append(file_path)

    return removed_files


def view_logs(
    log_name: Optional[str] = None,
    log_dir: Optional[str] = None,
    head: Optional[int] = None,
    tail: Optional[int] = None,
    search_pattern: Optional[str] = None,
    show_rotated: bool = False,
) -> list:
    """
    View log file contents with options for head, tail, and search.

    Args:
        log_name: Specific log to view (defaults to main log if None)
        log_dir: Custom log directory path (uses default if None)
        head: Number of lines to display from the beginning (if specified)
        tail: Number of lines to display from the end (if specified)
        search_pattern: String pattern to filter log lines (if specified)
        show_rotated: Whether to include rotated log files in the view

    Returns:
        list: List of log lines matching the criteria
    """
    import re

    log_dir = ensure_log_directory(log_dir)

    if log_name and log_name not in LOG_FILES:
        raise ValueError(
            f"Invalid log name: {log_name}. Valid names: {list(LOG_FILES.keys())}"
        )

    log_name = log_name or "main"
    log_file = LOG_FILES[log_name]
    log_path = os.path.join(log_dir, log_file)

    if not os.path.exists(log_path):
        return [f"Log file not found: {log_path}"]

    file_paths = [log_path]
    if show_rotated:
        for i in range(1, BACKUP_COUNT + 1):
            rotated_path = f"{log_path}.{i}"
            if os.path.exists(rotated_path):
                file_paths.append(rotated_path)

        file_paths.sort(key=os.path.getmtime, reverse=True)

    all_lines = []
    pattern = re.compile(search_pattern) if search_pattern else None

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                if pattern:
                    lines = [line for line in lines if pattern.search(line)]

                if show_rotated and len(file_paths) > 1:
                    file_indicator = f"\n--- {os.path.basename(file_path)} ---\n"
                    all_lines.append(file_indicator)

                all_lines.extend(lines)
        except Exception as e:
            all_lines.append(f"Error reading {file_path}: {str(e)}\n")

    if head is not None and tail is not None:

        result = all_lines[:head]
    elif head is not None:
        result = all_lines[:head]
    elif tail is not None:
        result = all_lines[-tail:] if len(all_lines) > tail else all_lines
    else:
        result = all_lines

    return result


def list_available_logs(log_dir: Optional[str] = None) -> Dict[str, list]:
    """
    List all available log files including rotated logs.

    Args:
        log_dir: Custom log directory path (uses default if None)

    Returns:
        Dict[str, list]: Dictionary of log files with their rotated versions
    """
    log_dir = ensure_log_directory(log_dir)
    result = {}

    for log_name, log_file in LOG_FILES.items():
        log_path = os.path.join(log_dir, log_file)
        log_files = []

        if os.path.exists(log_path):
            log_size = os.path.getsize(log_path)
            log_mtime = os.path.getmtime(log_path)
            mtime_str = datetime.fromtimestamp(log_mtime).strftime("%Y-%m-%d %H:%M:%S")
            log_files.append(
                {"path": log_path, "size": log_size, "modified": mtime_str}
            )

            for i in range(1, BACKUP_COUNT + 1):
                rotated_path = f"{log_path}.{i}"
                if os.path.exists(rotated_path):
                    rot_size = os.path.getsize(rotated_path)
                    rot_mtime = os.path.getmtime(rotated_path)
                    rot_mtime_str = datetime.fromtimestamp(rot_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    log_files.append(
                        {
                            "path": rotated_path,
                            "size": rot_size,
                            "modified": rot_mtime_str,
                        }
                    )

        result[log_name] = log_files

    return result
