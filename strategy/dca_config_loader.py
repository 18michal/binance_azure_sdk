""" Module to load and manage DCA configuration settings for multiple users. """

from typing import Any, Dict

import yaml


class DCAConfigLoader:
    """
    A class to load and manage Dollar-Cost Averaging (DCA) configuration
    settings for multiple users from a YAML file.

    The configuration file is expected to contain user-specific DCA strategies.
    """

    def __init__(self, config_path: str = "data/config.yaml"):
        """
        Initializes the DCAConfigLoader.

        Args:
            config_path (str): Path to the YAML configuration file. Defaults to "data/config.yaml".

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the YAML content is invalid.
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads the configuration file into memory.

        Returns:
            Dict[str, Any]: The full configuration dictionary.

        Raises:
            FileNotFoundError: If the file is not found at the given path.
            ValueError: If the YAML content cannot be parsed.
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(  # pylint: disable=W0707
                f"Missing config file at {self.config_path}"
            )
        except yaml.YAMLError as e:
            raise ValueError(  # pylint: disable=W0707
                f"Invalid YAML in config file: {e}"
            )
        return config

    def get_user_config(self, user_id: str) -> Dict[str, Any]:
        """Return the DCA config for a specific user."""
        if user_id not in self.config:
            raise KeyError(f"User '{user_id}' not found in config.yaml")

        user_config = self.config[user_id]

        # Validate essential keys
        required_fields = [
            "assets",
            "amount_usd",
            "drop_percent",
            "frequency",
            "email",
            "azure_vault",
        ]
        for field in required_fields:
            if field not in user_config:
                raise ValueError(f"Missing '{field}' in config for user '{user_id}'")

        return user_config
