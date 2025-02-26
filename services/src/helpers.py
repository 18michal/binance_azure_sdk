""" Helper functions for the services module. """

import logging
import os

import yaml


def load_config():
    """Loads configuration from a YAML file."""

    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../config.yaml")
    )

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def configure_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    if not logger.hasHandlers():  # Avoid adding multiple handlers
        logger.addHandler(console_handler)

    return logger
