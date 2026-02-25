import yaml
from pathlib import Path
from dataclasses import dataclass

@dataclass
class APIConfig:
    base_url: str
    requests_per_minute: int
    timeout: int

@dataclass
class LoggingConfig:
    level: str

class Config:
    def __init__(self, env: str = "dev"):
        # Load base config
        base_config_path = Path("config/base.yaml")
        with open(base_config_path, "r") as f:
            base_config = yaml.safe_load(f)

        # Load env config
        env_config_path = Path(f"config/{env}.yaml")
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                env_config = yaml.safe_load(f)

        # Merge them
        merged_config = self._deep_merge(base_config, env_config or {})

        # Create typed objects
        self.api_config = APIConfig(**merged_config.get("api", {}))
        self.logging_config = LoggingConfig(**merged_config.get("logging", {}))

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result:
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

