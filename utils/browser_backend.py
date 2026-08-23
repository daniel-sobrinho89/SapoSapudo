import io

import pygame

from utils.config import AUDIO_HABILITADO

IS_BROWSER = True

SRCALPHA = pygame.SRCALPHA
MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
MOUSEBUTTONUP = pygame.MOUSEBUTTONUP
MOUSEMOTION = pygame.MOUSEMOTION
KEYDOWN = pygame.KEYDOWN
QUIT = pygame.QUIT
FINGERDOWN = getattr(pygame, "FINGERDOWN", -1)
FINGERUP = getattr(pygame, "FINGERUP", -1)


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    @property
    def left(self):
        return int(self.x)

    @left.setter
    def left(self, v):
        self.x = int(v)

    @property
    def right(self):
        return int(self.x + self.w)

    @right.setter
    def right(self, v):
        self.x = int(v) - self.w

    @property
    def top(self):
        return int(self.y)

    @top.setter
    def top(self, v):
        self.y = int(v)

    @property
    def bottom(self):
        return int(self.y + self.h)

    @bottom.setter
    def bottom(self, v):
        self.y = int(v) - self.h

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
        x, y = args[0] if len(args) == 1 else args
        return self.left <= x < self.right and self.top <= y < self.bottom

    def update(self, *args):
        x, y, w, h = args[0] if len(args) == 1 else args
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)


class Surface:
    def __init__(self, size, flags=None, _surface=None):
        if _surface is not None:
            self._img = _surface
        else:
            flags = pygame.SRCALPHA if flags is None else flags
            self._img = pygame.Surface((int(size[0]), int(size[1])), flags)
            if flags & pygame.SRCALPHA:
                self._img.fill((0, 0, 0, 0))

    def get_width(self):
        return self._img.get_width()

    def get_height(self):
        return self._img.get_height()

    def get_size(self):
        return self._img.get_size()

    @property
    def width(self):
        return self._img.get_width()

    @property
    def height(self):
        return self._img.get_height()

    def blit(self, src, pos, area=None):
        raw = src._img if isinstance(src, Surface) else src
        dest = (pos.x, pos.y) if isinstance(pos, Rect) else pos
        self._img.blit(raw, dest, area)

    def copy(self):
        return Surface(self.get_size(), _surface=self._img.copy())

    def subsurface(self, rect):
        r = (rect.x, rect.y, rect.w, rect.h) if isinstance(rect, Rect) else rect
        sub = self._img.subsurface(r).copy()
        return Surface(sub.get_size(), _surface=sub)

    def get_bounding_rect(self):
        r = self._img.get_bounding_rect()
        return Rect(r.x, r.y, r.w, r.h)

    def convert_alpha(self):
        return self

    def set_alpha(self, a):
        self._img.set_alpha(max(0, min(255, int(a))))

    def get_rect(self, **kwargs):
        r = self._img.get_rect()
        if "center" in kwargs:
            r.center = kwargs["center"]
        elif "topleft" in kwargs:
            r.topleft = kwargs["topleft"]
        return Rect(r.x, r.y, r.w, r.h)

    def multiplicar_cor(self, cor):
        overlay = pygame.Surface(self._img.get_size(), pygame.SRCALPHA)
        overlay.fill((*cor, 255))
        self._img.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def fill(self, color):
        self._img.fill(color)


class image:
    @staticmethod
    def load(path):
        img = pygame.image.load(path).convert_alpha()
        return Surface(img.get_size(), _surface=img)

    @staticmethod
    def load_raw(path):
        with open(path, "rb") as f:
            return f.read()

    @staticmethod
    def from_raw(raw_data, ext="webp"):
        img = pygame.image.load(io.BytesIO(raw_data), ext).convert_alpha()
        return Surface(img.get_size(), _surface=img)


class transform:
    @staticmethod
    def smoothscale(surf, size):
        img = pygame.transform.smoothscale(surf._img, (int(size[0]), int(size[1])))
        return Surface(img.get_size(), _surface=img.convert_alpha())

    @staticmethod
    def scale(surf, size):
        img = pygame.transform.scale(surf._img, (int(size[0]), int(size[1])))
        return Surface(img.get_size(), _surface=img.convert_alpha())

    @staticmethod
    def rotate(surf, angle):
        img = pygame.transform.rotate(surf._img, angle)
        return Surface(img.get_size(), _surface=img.convert_alpha())

    @staticmethod
    def flip(surf, flip_x, flip_y):
        img = pygame.transform.flip(surf._img, flip_x, flip_y)
        return Surface(img.get_size(), _surface=img.convert_alpha())


class draw:
    @staticmethod
    def circle(surface, color, center, radius, width=0):
        pygame.draw.circle(surface._img, color, center, radius, width)

    @staticmethod
    def ellipse(surface, color, rect):
        r = (rect.x, rect.y, rect.w, rect.h) if isinstance(rect, Rect) else rect
        pygame.draw.ellipse(surface._img, color, r)

    @staticmethod
    def rect(surface, color, rect, width=0):
        r = (rect.x, rect.y, rect.w, rect.h) if isinstance(rect, Rect) else rect
        pygame.draw.rect(surface._img, color, r, width)

    @staticmethod
    def rounded_rect(surface, color, rect, radius=0, width=0):
        r = (rect.x, rect.y, rect.w, rect.h) if isinstance(rect, Rect) else rect
        pygame.draw.rect(surface._img, color, r, width, border_radius=int(radius))

    @staticmethod
    def line(surface, color, start_pos, end_pos, width=1):
        pygame.draw.line(surface._img, color, start_pos, end_pos, width)

    @staticmethod
    def text(surface, texto, posicao, cor=(255, 255, 255), tamanho=20, fonte=None):
        f = fonte or pygame.font.Font(None, int(tamanho))
        surface._img.blit(f.render(str(texto), True, cor), posicao)


class font:
    @staticmethod
    def load(path, tamanho):
        return pygame.font.Font(path, int(tamanho))


class display:
    class InfoObj:
        def __init__(self):
            w, h = pygame.display.get_window_size()
            self.current_w, self.current_h = int(w), int(h)

    @staticmethod
    def Info():
        return display.InfoObj()

    @staticmethod
    def set_mode(size):
        return Surface(size, _surface=pygame.display.set_mode(size))

    @staticmethod
    def set_caption(caption):
        pygame.display.set_caption(caption)

    @staticmethod
    def flip():
        pygame.display.flip()


class time:
    class Clock:
        def __init__(self):
            self._clock = pygame.time.Clock()

        def tick(self, fps=0):
            return self._clock.tick(fps)


class mixer:
    class _Music:
        def __init__(self):
            self._volume = 1.0

        def load(self, path):
            if not AUDIO_HABILITADO:
                return
            pygame.mixer.music.load(str(path))

        def set_volume(self, v):
            self._volume = float(v)
            if not AUDIO_HABILITADO or pygame.mixer.get_init() is None:
                return
            pygame.mixer.music.set_volume(self._volume)

        def play(self, loops=0):
            if not AUDIO_HABILITADO or pygame.mixer.get_init() is None:
                return
            pygame.mixer.music.play(loops)

        def pause(self):
            if not AUDIO_HABILITADO or pygame.mixer.get_init() is None:
                return
            pygame.mixer.music.pause()

        def stop(self):
            if not AUDIO_HABILITADO or pygame.mixer.get_init() is None:
                return
            pygame.mixer.music.stop()

        def unpause(self):
            if not AUDIO_HABILITADO or pygame.mixer.get_init() is None:
                return
            pygame.mixer.music.unpause()

        def get_busy(self):
            if not AUDIO_HABILITADO or pygame.mixer.get_init() is None:
                return False
            return pygame.mixer.music.get_busy()

    music = _Music()

    @staticmethod
    def init():
        # No browser: the game is configured with AUDIO_HABILITADO=False.
        # Do not touch SDL audio before a user gesture. Browsers may block it.
        if not AUDIO_HABILITADO:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            pass


class mouse:
    @staticmethod
    def get_pos():
        try:
            return tuple(map(int, pygame.mouse.get_pos()))
        except Exception:
            return (0, 0)


Clock = time.Clock
