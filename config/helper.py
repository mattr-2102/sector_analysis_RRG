import os
import yaml
from pathlib import Path

# dynamic resolve the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_data_dir() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "data"

def key(source: str) -> str | None:
    try:
        project_root = Path(__file__).resolve().parents[1]
        config_path = project_root / "config" / "api_keys.yaml"

        with config_path.open("r") as f:
            api_keys = yaml.safe_load(f) or {}

        return api_keys.get(source)
    except:
        print("Error retrieving api key.")

    return None

def get_data_file(filename: str) -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "data" / filename


def get_sector_config() -> dict:
    config_path = Path(__file__).resolve().parent / "sectors.yaml"
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    return config