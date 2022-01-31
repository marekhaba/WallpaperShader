"""
All shaders can define a custom config
that should placed in /config under {shader_name}_config.json
For config validation and parsing should be used pydantic with json
"""
import pathlib
import logging
import importlib
import json
from pydantic import BaseSettings, ValidationError

class Config(BaseSettings):
    script_name: str

#needs to be also changed in common.py
CONFIG_DIRECTORY = pathlib.PurePath(__file__, "../config/")
SCRIPT_DIRECTORY = pathlib.PurePath("wallpaper_shaders")

def main():
    try:
        with open(CONFIG_DIRECTORY.joinpath("config.json")) as file:
            config_json = json.load(file)
        config = Config(**config_json)
    except (ValidationError, json.JSONDecodeError) as error:
        logging.error("config.json is invalid", exc_info=error)
        raise
    script = importlib.import_module("." + config.script_name, str(SCRIPT_DIRECTORY))
    script.main()


if __name__ == "__main__":
    main()

# config:
# shader_script: name of python file to run
#   each script will have its own config that will be loaded - {script_name}_config.json
