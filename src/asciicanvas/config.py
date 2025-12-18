import json
import os
from pathlib import Path

APP_NAME = "AsciiCanvas"
CONFIG_DIR = Path.home() / f".{APP_NAME.lower()}"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_DOCS_DIR = Path.home() / APP_NAME

DEFAULT_CONFIG = {
    "document_folder": str(DEFAULT_DOCS_DIR)
}

def _get_default_config_path() -> Path:
    """Returns the path to the default document folder based on config."""
    # This function is designed to be called without triggering recursion
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                return Path(config_data.get("document_folder", str(DEFAULT_DOCS_DIR)))
        except json.JSONDecodeError:
            # If config file is corrupt, fall back to default
            pass
    return DEFAULT_DOCS_DIR

def ensure_config_and_dirs_exist():
    """Ensures the config directory, file, and document folder exist."""
    CONFIG_DIR.mkdir(exist_ok=True)
    
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
    
    # Ensure the document folder exists AFTER the config is guaranteed to be valid
    # and without causing recursion.
    doc_folder = _get_default_config_path()
    doc_folder.mkdir(exist_ok=True)

def load_config() -> dict:
    """Loads the configuration from the JSON file."""
    # ensure_config_and_dirs_exist() is called once at app startup
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_document_folder() -> Path:
    """Gets the document folder path from the config."""
    config = load_config() # This will now load from an existing config
    return Path(config.get("document_folder", str(DEFAULT_DOCS_DIR)))

def set_document_folder(path: Path):
    """Saves a new document folder path to the config."""
    config = load_config()
    config["document_folder"] = str(path)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
