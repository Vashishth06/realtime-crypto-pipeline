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

@dataclass
class MinIOConfig:
    endpoint: str
    access_key: str
    secret_key: str
    warehouse_path: str

@dataclass
class PostgresConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

class Config:
    def __init__(self, env: str = "dev"):
        self.env = env
        config_dir = Path("config")

        # Load base config
        base_config = self._load_yaml(config_dir / "base.yaml")

        # Load secrets
        merged_config = base_config.copy()
        secrets_path = config_dir / "secrets.yaml"
        if secrets_path.exists():
            secrets = self._load_yaml(secrets_path)
            merged_config = self._deep_merge(merged_config, secrets)

        # Load env config (takes precedence over secrets)
        env_config_path = config_dir / f"{env}.yaml"
        if env_config_path.exists():
            env_config = self._load_yaml(env_config_path)
            merged_config = self._deep_merge(merged_config, env_config)

        # Create typed objects
        self.api_config = APIConfig(**merged_config.get("api", {}))
        self.logging_config = LoggingConfig(**merged_config.get("logging", {}))
        self.minio_config = MinIOConfig(**merged_config.get("minio", {}))
        self.postgres = PostgresConfig(**merged_config.get('postgres', {}))

    def _load_yaml(self, path: Path) -> dict:
        """Load YAML file and return as dict"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """ Recursively merge two dictionaries, with override taking precedence """
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result:
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

