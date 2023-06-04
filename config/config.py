from pathlib import Path

from dynaconf import LazySettings

SETTINGS_TOML_PATH = Path(__file__).parent.joinpath("settings.toml")

settings = LazySettings(SETTINGS_FILE_FOR_DYNACONF=[SETTINGS_TOML_PATH])
