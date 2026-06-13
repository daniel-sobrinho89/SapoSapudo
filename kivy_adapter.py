"""
Note: implements a narrow subset used by the project: Surface, Rect,
transform (scale/rotate), image.load, display.set_mode/Info, time.Clock,
and a minimal mixer.music using Kivy SoundLoader.
"""
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO
from kivy.core.image import Image as CoreImage
import time as pytime

# mouse compatibility

_window_cache = None

def obter_window():
    global _window_cache

    if _window_cache is None:
        from kivy.core.window import Window
        _window_cache = Window

    return _window_cache

_soundloader_cache = None

def obter_soundloader():

    global _soundloader_cache

    if _soundloader_cache is None:
        from kivy.core.audio import SoundLoader

        _soundloader_cache = SoundLoader

    return _soundloader_cache

class mouse:

    @staticmethod
    def get_pos():
        try:
            return tuple(map(int, obter_window().mouse_pos))
        except Exception:
            return (0, 0)


# constants
SRCALPHA = 1

# simple event constants (not used extensively)
MOUSEBUTTONDOWN = 1
MOUSEBUTTONUP = 2
MOUSEMOTION = 3
KEYDOWN = 4
QUIT = 5


class Rect:
    def __init__(self, x, y, w, h):
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)

    @property
    def left(self):
        return int(self.x)

    @left.setter
    def left(self, value):
        self.x = int(value)

    @property
    def right(self):
        return int(self.x + self.w)

    @right.setter
    def right(self, value):
        self.x = int(value) - self.w

    @property
    def top(self):
        return int(self.y)

    @top.setter
    def top(self, value):
        self.y = int(value)

    @property
    def bottom(self):
        return int(self.y + self.h)

    @bottom.setter
    def bottom(self, value):
        self.y = int(value) - self.h

    @property
    def centerx(self):
        return int(self.x + self.w // 2)

    @property
    def centery(self):
        return int(self.y + self.h // 2)

    @property
    def center(self):
        return (self.centerx, self.centery)

    @property
    def width(self):
        return int(self.w)

    @property
    def height(self):
        return int(self.h)
    
    def collidepoint(self, *args):
        if len(args) == 1:
            x, y = args[0]
        else:
            x, y = args

        return (
            self.left <= x < self.right
            and self.top <= y < self.bottom
        )

    def update(self, *args):

        if len(args) == 1:
            x, y, w, h = args[0]
        else:
            x, y, w, h = args

        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)

class Surface:
    def __init__(self, size, flags=None):
        self.width, self.height = int(size[0]), int(size[1])
        # PIL image in RGBA
        self._img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        self._alpha = 255

    def get_width(self):
        return self._img.width

    def get_height(self):
        return self._img.height

    def get_size(self):
        return (self.get_width(), self.get_height())

    def blit(self, src, pos):
        # src can be another Surface or a PIL Image
        if isinstance(src, Surface):
            src_img = src._img
        elif isinstance(src, Image.Image):
            src_img = src
        else:
            raise TypeError("Unsupported blit source")

        # pos can be tuple (x,y) or Rect
        if isinstance(pos, Rect):
            x, y = pos.x, pos.y
        else:
            x, y = int(pos[0]), int(pos[1])

        # handle alpha
        base = self._img
        base.alpha_composite(src_img, (x, y))

    def copy(self):
        s = Surface(self.get_size())
        s._img = self._img.copy()
        return s

    def subsurface(self, rect):
        # rect can be Rect or tuple
        if isinstance(rect, Rect):
            x, y, w, h = rect.x, rect.y, rect.w, rect.h
        else:
            x, y, w, h = rect

        img = self._img.crop((x, y, x + w, y + h))
        s = Surface((w, h))
        s._img = img.copy()
        return s

    def get_bounding_rect(self):
        bbox = self._img.getbbox()
        if bbox is None:
            return Rect(0, 0, 0, 0)
        left, upper, right, lower = bbox
        return Rect(left, upper, right - left, lower - upper)

    def convert_alpha(self):
        return self

    def set_alpha(self, a):

        self._alpha = max(
            0,
            min(255, int(a))
        )

        img = self._img.copy()
        alpha = img.getchannel("A")

        alpha = alpha.point(
            lambda p: int(
                p * self._alpha / 255
            )
        )

        img.putalpha(alpha)
        self._img = img

    def get_rect(self, **kwargs):
        # support center=(x,y)
        if 'center' in kwargs:
            cx, cy = kwargs['center']
            w, h = self.get_size()
            return Rect(int(cx - w // 2), int(cy - h // 2), w, h)
        return Rect(0, 0, self.get_width(), self.get_height())

    # convenience to access underlying PIL image
    def pil_image(self):
        return self._img


# image module
class image:
    @staticmethod
    def load(path):
        core = CoreImage(path)

        if core.texture is None:
            raise RuntimeError(
                f"Falha ao carregar textura: {path}"
            )

        largura, altura = core.texture.size
        pixels = core.texture.pixels

        img = Image.frombytes(
            "RGBA",
            (largura, altura),
            pixels
        )

        s = Surface(img.size)
        s._img = img

        return s
    
    @staticmethod
    def load_raw(path):
        with open(path, "rb") as f:
            return f.read()
        
    @staticmethod
    def from_raw(raw_data, ext="webp"):

        core = CoreImage(
            BytesIO(raw_data),
            ext=ext
        )

        largura, altura = core.texture.size
        pixels = core.texture.pixels

        img = Image.frombytes(
            "RGBA",
            (largura, altura),
            pixels
        )

        s = Surface(img.size)
        s._img = img

        return s


# transform functions
class transform:

    @staticmethod
    def smoothscale(surf, size):

        if not isinstance(surf, Surface):
            raise TypeError("smoothscale requires Surface")

        w = int(size[0])
        h = int(size[1])

        resized = surf._img.resize(
            (w, h),
            resample=Image.BILINEAR
        )

        s = Surface((w, h))
        s._img = resized

        return s

    @staticmethod
    def scale(surf, size):
        return transform.smoothscale(
            surf,
            size
        )

    @staticmethod
    def rotate(surf, angle):

        if not isinstance(surf, Surface):
            raise TypeError("rotate requires Surface")

        rotated = surf._img.rotate(
            -angle,
            resample=Image.BILINEAR,
            expand=True
        )

        s = Surface(rotated.size)
        s._img = rotated

        return s

    @staticmethod
    def flip(surf, flip_x, flip_y):

        if not isinstance(surf, Surface):
            raise TypeError("flip requires Surface")

        img = surf._img

        if flip_x:
            img = ImageOps.mirror(img)

        if flip_y:
            img = ImageOps.flip(img)

        s = Surface(img.size)
        s._img = img

        return s

class draw:

    @staticmethod
    def circle(surface, color, center, radius):

        draw_ctx = ImageDraw.Draw(surface._img)

        x, y = center

        draw_ctx.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius
            ),
            fill=color
        )

    @staticmethod
    def ellipse(surface, color, rect):

        draw_ctx = ImageDraw.Draw(surface._img)

        if isinstance(rect, Rect):
            bbox = (
                rect.left,
                rect.top,
                rect.right,
                rect.bottom
            )
        else:
            x, y, w, h = rect
            bbox = (
                x,
                y,
                x + w,
                y + h
            )

        draw_ctx.ellipse(
            bbox,
            fill=color
        )

    @staticmethod
    def rect(surface, color, rect):

        draw_ctx = ImageDraw.Draw(surface._img)

        draw_ctx.rectangle(
            (
                rect.left,
                rect.top,
                rect.right,
                rect.bottom
            ),
            fill=color
        )

# display module
class display:
    _screen = None

    class InfoObj:
        def __init__(self):

            window = obter_window()

            self.current_w = int(window.width)
            self.current_h = int(window.height)

    @staticmethod
    def Info():
        return display.InfoObj()

    @staticmethod
    def set_mode(size):
        display._screen = Surface(size)
        return display._screen

    @staticmethod
    def set_caption(caption):
        pass

    @staticmethod
    def flip():
        pass


# time.Clock
class time:
    class Clock:
        def __init__(self):
            self._last = pytime.time()  # shadowing name

        def tick(self, fps=0):
            now = pytime.time()
            elapsed = now - self._last
            self._last = now
            if fps and elapsed > 0:
                target = 1.0 / fps
                sleep = max(0, target - elapsed)
                if sleep > 0:
                    pytime.sleep(sleep)
                    elapsed += sleep
            return int(elapsed * 1000)

# mixer (minimal using Kivy SoundLoader)
class mixer:
    @staticmethod
    def init():
        pass

    class _Music:
        def __init__(self):
            self._sound = None
            self._volume = 1.0

        def load(self, path):
            try:

                if self._sound:
                    try:
                        self._sound.stop()
                    except Exception:
                        pass

                self._sound = obter_soundloader().load(path)

            except Exception as ex:

                import traceback
                traceback.print_exc()

                print(ex)

        def set_volume(self, v):
            self._volume = v
            if self._sound:
                self._sound.volume = v

        def play(self, loops=0):
            if not self._sound:
                return
            # loops < 0 => infinite
            try:
                self._sound.loop = loops < 0
            except Exception:
                pass

            self._sound.volume = self._volume
            self._sound.play()

        def pause(self):
            if self._sound:
                try:
                    self._sound.stop()
                except Exception:
                    pass

        def unpause(self):
            if self._sound:
                self._sound.play()

    music = _Music()


# expose basic API at module level for compatibility
Clock = time.Clock
