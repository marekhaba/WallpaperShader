from os import path

RESOURCES_PATH = path.normpath(path.join(__file__, '../resources'))

#If I want to in the future seperate images in anouther file
IMAGES_PATH = RESOURCES_PATH

def image_path(name):
    """returns path to an image in RESOURCES_PATH"""
    return path.join(IMAGES_PATH, name)

def shader_path(name, base_path=RESOURCES_PATH):
    """returns path to shader relative to base_path"""
    with open(path.join(base_path, name), "r") as file:
        return file.read()    