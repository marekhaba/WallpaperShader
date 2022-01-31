import logging
import json
from typing import Any, Tuple, List

import moderngl_window as mglw
from moderngl_window import geometry
import moderngl
import numpy as np
from PIL import Image
from pydantic import BaseSettings, ValidationError, validator

from wallpaper_shaders.common import image_path, RESOURCES_DIRECTORY, CONFIG_DIRECTORY
from wallpaper_shaders.wallpaper_shader_win import WallpaperWindow
from wallpaper_shaders.utils import resize_with_padding

class Config(BaseSettings):
    image: str = "mask.png"
    color_treshold: Tuple[int, int, int, int] = (10, 10, 10, 255)
    pull: float = 0.5
    push: float = 1.0
    close_treshold: float = 1.0
    drag: float = 0.99

    @validator("color_treshold")
    @classmethod
    def color_4_elements(cls, variable):
        if len(variable) != 4:
            raise ValueError("Color must be set as rgba")
        return tuple(variable)
    
    @validator("image")
    @classmethod
    def image_exists(cls, variable):
        try:
            Image.open(image_path(variable)).close()
        except FileNotFoundError:
            raise ValueError("Image not found.")
        except (OSError, ValueError, TypeError):
            raise ValueError("Error while loading the Image")
        return variable

class ComputeRender(WallpaperWindow):
    """
    Windowed Compute Shader Renderer.
    To set a value to a uniform use set_value(name, value)
    Some values are set by default: u_resolution, u_time, u_mouse
    """
    gl_version = (4, 3)

    #COMPUTE_SIZE_X = 8

    resource_dir = RESOURCES_DIRECTORY

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            with open(CONFIG_DIRECTORY.joinpath("config_pixel_particles.json")) as file:
                config_json = json.load(file)
            self.config = Config(**config_json)
        except (ValidationError, json.JSONDecodeError) as error:
            logging.error("config.json is invalid", exc_info=error)
            raise

        self.count = 0  # number of agents
        self.STRUCT_SIZE = 12  # number of floats per agent

        self.ctx: moderngl.Context
        self.view_prog = self.load_program("view.glsl")

        self.pixel_shader = self.load_compute_shader(
            "pixel_particles.glsl",
            defines={
                "_pull_": self.config.pull,
                "_push_": self.config.push,
                "_close_treshold_": self.config.close_treshold,
                "_drag_": self.config.drag
            }
        )

        self.difuse_shader = self.load_compute_shader(
            "diffuse.glsl"
        )

        self.random_generator: np.random.Generator = np.random.default_rng()

        # Load Mask and generate afents from it
        mask_name = self.config.image

        mask_image = Image.open(image_path(mask_name))
        mask_image = resize_with_padding(mask_image, self.window_size)

        self.mask = np.asarray(mask_image)
        mask_proccesed = np.transpose(np.where(np.any(self.mask > self.config.color_treshold, axis=-1)))

        self.agents = []
        #hacky way to generate all agents
        [self.generate_initial_mask(cords) for cords in mask_proccesed]
        self.mask_texture = self.load_texture_2d(mask_name)

        mask_image.close()

        # Agent buffer
        agent_data = np.array(self.agents, dtype="f4")
        self.agent_buffer = self.ctx.buffer(agent_data)

        self.count = len(self.agents)//self.STRUCT_SIZE
        self.set_uniform("agents_count", self.count)

        self.set_uniform("u_resolution", self.window_size)

        # RGB_8 texture
        self.texture1 = self.ctx.texture(self.window_size, 4)
        self.texture1.filter = moderngl.NEAREST, moderngl.NEAREST
        self.texture2 = self.ctx.texture(self.window_size, 4)
        self.texture2.filter = moderngl.NEAREST, moderngl.NEAREST
        self.view_fs = geometry.quad_fs()

        #odd texture1 or even texture2
        self.odd = True


    def generate_initial_random(self):
        """Generator function creating agents ranomly on screen"""
        rng: np.random.Generator = np.random.default_rng()
        for _ in range(self.count):
            yield rng.integers(low=0, high=self.window_size[0]) # x
            yield rng.integers(low=0, high=self.window_size[1]) # y
            yield rng.random()*2*np.pi # angle
            yield 0.0 # padding

    def generate_initial_mask(self, cords: Tuple[int, int]):
        """
        Apply over a numpy array containing cords
        as a side effect appends agents to agent list
        """
        # this should be sped up
        # cords[1] = x cords[0] = y for some reason thx numpy
        y = self.window_size[1] - cords[0]
        self.agents.append(cords[1]) # x
        self.agents.append(y) # y
        self.agents.append(0.0) # padding 1
        self.agents.append(0.0) # padding 2
        self.agents.append(0.0) # velocity x
        self.agents.append(0.0) # velocity y
        self.agents.append(cords[1]) # original x
        self.agents.append(y) # original y
        self.agents.append(self.mask[cords[0]][cords[1]][0]/255) # r
        self.agents.append(self.mask[cords[0]][cords[1]][1]/255) # g
        self.agents.append(self.mask[cords[0]][cords[1]][2]/255) # b
        self.agents.append(self.mask[cords[0]][cords[1]][3]/255) # a
        # also add color

    def set_uniform(self, name, value: Any):
        """Method for inputting a value to a uniform."""
        try:
            self.pixel_shader[name].value = value
        except KeyError:
            pass

    def mouse_position_event(self, x, y, dx, dy):
        if abs(dx) + abs(dy) > 30:
            self.set_uniform("mouse", (x, self.window_size[1]-y))
            self.set_uniform("delta_mouse", (dx, -dy))
        else:
            self.set_uniform("mouse", (x, self.window_size[1]-y))
            self.set_uniform("delta_mouse", (0, 0))

    @classmethod
    def add_arguments(cls, parser):
        """Add commmand line arguments"""
        return

    def render(self, time, frame_time):
        super().render(time, frame_time)
        # This method is called every frame
        self.ctx.clear(0.2, 0.2, 0.2)

        #w, h = self.window_size
        #gw, gh = 16, 16
        #nx, ny, nz = int(w/gw), int(h/gh), 1

        self.set_uniform("time", time)

        #self.framebuffer.use()

        # Switch Previous Texture
        if self.odd:
            read_texture = self.texture1
            write_texture = self.texture2
        else:
            write_texture = self.texture1
            read_texture = self.texture2


        self.odd = not self.odd


        read_texture.bind_to_image(0, read=True, write=False)
        write_texture.bind_to_image(1, read=False, write=True)

        #diffuse pixels
        self.difuse_shader.run(self.window_size[0] // 32 +1, self.window_size[1] // 32 +1, 1)

        #bind angents
        self.agent_buffer.bind_to_storage_buffer(2)

        #self.mask_texture.bind_to_image(3, read=True, write=False)

        self.pixel_shader.run(self.count // 16 + 1, 1, 1)

        # Render texture
        #read_texture.use(location=0)
        read_texture.use(0)
        self.view_fs.render(self.view_prog)

    def close(self):
        self.view_prog.release()
        self.pixel_shader.release()
        self.difuse_shader.release()
        self.texture1.release()
        self.texture2.release()
        self.mask_texture.release()
        self.agent_buffer.release()
        self.view_fs.release()
        self.ctx.release()
        return super().close()

def main():
    """Function to run all stuff required by the shader"""
    mglw.run_window_config(ComputeRender)
