"""
Different utilites to be used in moderngl programs.
"""
from typing import Tuple
from PIL import ImageOps, Image

def resize_with_padding(img: Image, expected_size: Tuple[int, int],
                        fill: Tuple[int, int, int, int] = (0, 0, 0, 255)) -> Image:
    """
    Resizes and pads input image using fill color.
    """
    img.thumbnail((expected_size[0], expected_size[1]))
    delta_width = expected_size[0] - img.size[0]
    delta_height = expected_size[1] - img.size[1]
    pad_width = delta_width // 2
    pad_height = delta_height // 2
    padding = (pad_width, pad_height, delta_width - pad_width, delta_height - pad_height)
    return ImageOps.expand(img, padding, fill)