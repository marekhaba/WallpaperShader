"""
Contains baseclass for all moderngl programs supposed to be run as the wallpaper.
"""
import ctypes
from typing import Tuple

import moderngl_window as mglw

user32 = ctypes.WinDLL("user32")

def find_workerw_handle() -> int:
    """
    Finds and returns WorkerW window handle.
    Children of this window will be drawn between the icons and the wallpaper.
    use ctypes.windll.user32.SetParent to set the window parent
    """
    # https://www.codeproject.com/Articles/856020/Draw-Behind-Desktop-Icons-in-Windows-plus

    # Find handle of progman window
    desktop_handle = user32.GetDesktopWindow()
    progman = user32.FindWindowExW(desktop_handle, 0, "Progman", 0)

    # Send message to progman to create WorkerW window
    # 0x0000 - SMTO_NORMAL
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0x0000, 1000, 0)

    # Find newly created WorkerW window
    workerw = []

    def enum_windows_proc(hwnd, _lparam):
        handle = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", 0)
        if handle != 0:
            # hacky way to get workerw value out of this function
            workerw.append(user32.FindWindowExW(0, hwnd, "WorkerW", 0))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,
                                     ctypes.wintypes.HWND,
                                     ctypes.wintypes.LPARAM)
    enum_windows_proc_winfunc = WNDENUMPROC(enum_windows_proc)

    user32.EnumWindows(enum_windows_proc_winfunc, 0)

    return workerw.pop()

# Get cursor position
# https://stackoverflow.com/a/24567802
class POINT(ctypes.Structure):
    """Structure to get x, y out of GetCursorPos"""
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_position() -> Tuple[int, int]:
    """Returns the curent mouse position using win api."""
    point = POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


class WallpaperWindow(mglw.WindowConfig):
    """
    ``Window Config`` class setup to render as a wallpaper.
    Subclasses should also call super() methods.
    """

    fullscreen = True
    window_size = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # This is a bit hacky
        user32.SetParent(self.wnd._window._hwnd, find_workerw_handle())
        self._prev_mouse_position = get_mouse_position()

    def render(self, time: float, frame_time: float):
        # support for all events should be added
        mouse_position = get_mouse_position()
        self.mouse_position_event(mouse_position[0],
                                  mouse_position[1],
                                  mouse_position[0] - self._prev_mouse_position[0],
                                  mouse_position[1] - self._prev_mouse_position[1])
        self._prev_mouse_position = mouse_position
