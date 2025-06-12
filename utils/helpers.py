import yaml
import json
import csv
from pathlib import Path
import datetime as datetime

def load_config(path: Path = None) -> dict:
    if path is None:
        path = Path(__file__).parent.parent / "config.yaml"

    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Config file not found: {path}")
    except Exception as e:
        raise RuntimeError(f"Error loading config: {str(e)}")
    
def ensure_folder_exists(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def parse_date(date_str, fmt="%Y-%m-%dT%H:%M:%S.%fZ") -> datetime.datetime:
    return datetime.strptime(date_str, fmt)