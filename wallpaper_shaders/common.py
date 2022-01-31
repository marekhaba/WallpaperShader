from os import path
import pathlib

CONFIG_DIRECTORY = pathlib.PurePath(__file__, "../../config")
RESOURCES_DIRECTORY = pathlib.PurePath(__file__, "../../resources")
RESOURCES_DIRECTORY = pathlib.PurePath(__file__, "../../resources")

#If I want to in the future seperate images in anouther file
IMAGES_DIRECTORY = RESOURCES_DIRECTORY

def image_path(name):
    """returns path to an image in RESOURCES_PATH"""
    return path.join(IMAGES_DIRECTORY, name)

def shader_path(name, base_path=RESOURCES_DIRECTORY):
    """returns path to shader relative to base_path"""
    with open(path.join(base_path, name), "r") as file:
        return file.read()
