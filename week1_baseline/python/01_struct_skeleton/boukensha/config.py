import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


class Config:
    # The .boukensha config directory is resolved in this order:
    #   1. BOUKENSHA_DIR environment variable (set before loading .env)
    #   2. ~/.boukensha  (default)
    DEFAULT_DIR = str(Path.home() / ".boukensha")

    def __init__(self):
        self._dir = self._resolve_dir()
        self._load_env()
        self._settings = self._load_settings()

    @property
    def dir(self):
        return self._dir

    @property
    def settings(self):
        return self._settings

    # ---------- tasks -----------------------------------------------------

    def tasks(self, name=None):
        """Full tasks dict, or one task's settings dict when a name is given."""
        all_tasks = self.dig("tasks") or {}
        return all_tasks.get(str(name)) if name is not None else all_tasks

    @property
    def user_prompts_dir(self):
        return os.path.join(self._dir, "prompts")

    # ---------- MUD connection --------------------------------------------

    @property
    def mud_host(self):
        value = self.dig("mud", "host")
        return "localhost" if value is None else value

    @property
    def mud_port(self):
        value = self.dig("mud", "port")
        return 4000 if value is None else value

    @property
    def mud_username(self):
        return self.dig("mud", "username")

    @property
    def mud_password(self):
        return self.dig("mud", "password")

    # ---------- low-level helpers -----------------------------------------

    def dig(self, *keys):
        """Fetch a nested key path from settings, e.g. dig("mud", "host")."""
        node = self._settings
        for key in keys:
            if not isinstance(node, dict):
                return None
            node = node.get(str(key))
        return node

    def __str__(self):
        return f"#<Boukensha::Config dir={self._dir} tasks={','.join(self.tasks().keys())}>"

    __repr__ = __str__

    def _resolve_dir(self):
        raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
        return str(Path(raw).expanduser().resolve())

    def _load_env(self):
        env_file = os.path.join(self._dir, ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file, override=False)

    def _load_settings(self):
        settings_file = os.path.join(self._dir, "settings.yaml")
        if os.path.exists(settings_file):
            with open(settings_file) as f:
                return yaml.safe_load(f) or {}
        return {}
