from pathlib import Path


class Base:
    """Abstract, stateless task. All behaviour is classmethods taking a settings dict."""

    task_name = None

    @classmethod
    def _task_name(cls):
        if cls.task_name is None:
            raise NotImplementedError(f"{cls.__name__} must define task_name")
        return cls.task_name

    @classmethod
    def provider(cls, settings):
        value = cls._fetch(settings, "provider")
        if value is None:
            raise ValueError(f"tasks.{cls._task_name()}.provider is required in settings.yaml")
        return value

    @classmethod
    def model(cls, settings):
        value = cls._fetch(settings, "model")
        if value is None:
            raise ValueError(f"tasks.{cls._task_name()}.model is required in settings.yaml")
        return value

    @classmethod
    def prompt_override(cls, settings, prompt="system"):
        node = cls._fetch(settings, "prompt_override")
        if not isinstance(node, dict):
            return False
        return node.get(str(prompt)) is True

    @classmethod
    def prompt(cls, settings, name="system", *, user_prompts_dir=None, default_prompts_dir=None):
        if cls.prompt_override(settings, name):
            text = cls._read_user_prompt(name, user_prompts_dir)
            if text is not None:
                return text
        return cls._read_default_prompt(name, default_prompts_dir)

    @classmethod
    def system_prompt(cls, settings, *, user_prompts_dir=None, default_prompts_dir=None):
        return cls.prompt(
            settings, "system",
            user_prompts_dir=user_prompts_dir,
            default_prompts_dir=default_prompts_dir,
        )

    @staticmethod
    def _fetch(settings, key):
        return (settings or {}).get(key)

    @classmethod
    def _read_user_prompt(cls, prompt_name, user_prompts_dir):
        if not user_prompts_dir:
            return None
        return cls._read_file(Path(user_prompts_dir) / cls._task_name() / f"{prompt_name}.md")

    @classmethod
    def _read_default_prompt(cls, prompt_name, default_prompts_dir):
        if not default_prompts_dir:
            return None
        return cls._read_file(Path(default_prompts_dir) / f"{prompt_name}.md")

    @staticmethod
    def _read_file(path):
        path = Path(path)
        return path.read_text().strip() if path.exists() else None
