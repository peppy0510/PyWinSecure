# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import ctypes
import json
import os
import sys
import wx

from ctypes import wintypes


APP_NAME = 'PyWinSecure'
APP_VERSION = '0.2.0'
APP_AUTHOR = 'Taehong Kim · peppy0510@hotmail.com'

CARD_HEIGHT = 54
CARD_RADIUS = 6

TITLEBAR_HEIGHT = 32
CAPTION_WIDTH = 46

GWL_STYLE = -16
WS_CAPTION = 0x00C00000
WS_CLIPSIBLINGS = 0x04000000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020

RDW_ALLCHILDREN = 0x0080
RDW_UPDATENOW = 0x0100

DWMWA_EXTENDED_FRAME_BOUNDS = 9
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35


THEMES = {
    'dark': {
        'bg': '#1b1d21',
        'face': '#25282d',
        'rim': '#3a3f46',
        'track': '#3a3f46',
        'text': '#e6e9ed',
        'dim': '#8b929b',
        'accent': '#4c9aff',
        'control': '#2f333a',
        'warn': '#e0a458',
        'done': '#4c9aff',
        'close': '#c42b1c',
        'titlebar_dark': True,
    },
    'light': {
        'bg': '#f4f5f7',
        'face': '#ffffff',
        'rim': '#d5d9df',
        'track': '#d5d9df',
        'text': '#1d2126',
        'dim': '#6b727c',
        'accent': '#2b6cb0',
        'control': '#e8eaee',
        'warn': '#a2661f',
        'done': '#2b6cb0',
        'close': '#c42b1c',
        'titlebar_dark': False,
    },
}


class WindowRect(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                ('right', ctypes.c_long), ('bottom', ctypes.c_long)]


def get_colour_ref(colour):
    value = wx.Colour(colour)
    return (value.Blue() << 16) | (value.Green() << 8) | value.Red()


def apply_titlebar_theme(window, theme):
    try:
        handle = wintypes.HWND(window.GetHandle())
        value = ctypes.c_int(1 if theme['titlebar_dark'] else 0)
        for attribute in (DWMWA_USE_IMMERSIVE_DARK_MODE,
                          DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                handle, attribute, ctypes.byref(value), ctypes.sizeof(value))

        value = ctypes.c_int(get_colour_ref(theme['bg']))
        for attribute in (DWMWA_CAPTION_COLOR, DWMWA_BORDER_COLOR):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                handle, attribute, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        return

    # a shown frame needs a resize to repaint the DWM frame
    if window.IsShown():
        width, height = window.GetSize()
        window.SetSize(width, height + 1)
        window.SetSize(width, height)


def apply_no_caption(window):
    # wxWidgets 3.3 keeps WS_CAPTION without wx.CAPTION
    try:
        handle = wintypes.HWND(window.GetHandle())
        style = ctypes.windll.user32.GetWindowLongW(handle, GWL_STYLE)
        ctypes.windll.user32.SetWindowLongW(handle, GWL_STYLE, style & ~WS_CAPTION)
        ctypes.windll.user32.SetWindowPos(handle, 0, 0, 0, 0, 0,
                                          SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER |
                                          SWP_NOACTIVATE | SWP_FRAMECHANGED)
    except Exception:
        pass


def apply_clip_siblings(window):
    # wx never sets WS_CLIPSIBLINGS, so siblings paint over an overlay
    try:
        handle = wintypes.HWND(window.GetHandle())
        style = ctypes.windll.user32.GetWindowLongW(handle, GWL_STYLE)
        ctypes.windll.user32.SetWindowLongW(handle, GWL_STYLE, style | WS_CLIPSIBLINGS)
    except Exception:
        pass


def paint_now(window):
    # WM_PAINT is only generated once the queue is empty, which a moving mouse never lets happen
    try:
        ctypes.windll.user32.RedrawWindow(wintypes.HWND(window.GetHandle()), None, None,
                                          RDW_UPDATENOW | RDW_ALLCHILDREN)
    except Exception:
        pass


def call_painted(window, function, *args):
    def run():
        function(*args)
        if window:
            paint_now(window)
    wx.CallAfter(run)


def get_frame_margins(window):
    rect = WindowRect()
    try:
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(
                wintypes.HWND(window.GetHandle()), DWMWA_EXTENDED_FRAME_BOUNDS,
                ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
            return (0, 0, 0, 0)
    except Exception:
        return (0, 0, 0, 0)

    outer = window.GetScreenRect()
    return (rect.left - outer.x, rect.top - outer.y,
            outer.x + outer.width - rect.right, outer.y + outer.height - rect.bottom)


def get_asset_path(*parts):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'assets', *parts)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'assets', *parts)


def get_settings_path():
    return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')),
                        APP_NAME, 'settings.json')


def get_legacy_settings_path():
    return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
                        APP_NAME, 'settings.json')


def load_legacy_settings():
    try:
        with open(get_legacy_settings_path(), encoding='utf-8') as file:
            legacy = json.load(file)
    except Exception:
        return {}

    settings = {}
    if legacy.get('alwaysontop') is not None:
        settings['on_top'] = bool(legacy['alwaysontop'])
    size, position = legacy.get('size'), legacy.get('position')
    if size and position and len(size) == 2 and len(position) == 2:
        settings['rect'] = list(position) + list(size)
    return settings


def load_settings():
    if not os.path.exists(get_settings_path()):
        return load_legacy_settings()
    try:
        with open(get_settings_path(), encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return {}


def save_settings(settings):
    try:
        path = get_settings_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=2)
    except Exception:
        pass


def mix(colour, other, ratio):
    first, second = wx.Colour(colour), wx.Colour(other)
    return wx.Colour(*[round(a + (b - a) * ratio) for a, b in
                       ((first.Red(), second.Red()),
                        (first.Green(), second.Green()),
                        (first.Blue(), second.Blue()))])


def shade(colour, factor):
    base = wx.Colour(colour)
    return wx.Colour(min(255, int(base.Red() * factor)),
                     min(255, int(base.Green() * factor)),
                     min(255, int(base.Blue() * factor)))


def draw_card_rim(gc, colour, x, y, width, height, radius=CARD_RADIUS):
    # a pen draws the left and top edges thicker, fill the ring instead
    path = gc.CreatePath()
    path.AddRoundedRectangle(x, y, width, height, radius)
    path.AddRoundedRectangle(x + 1, y + 1, width - 2, height - 2, max(0, radius - 1))
    gc.SetPen(wx.TRANSPARENT_PEN)
    gc.SetBrush(wx.Brush(wx.Colour(colour)))
    gc.FillPath(path, wx.ODDEVEN_RULE)


def get_font(size, bold=False):
    weight = wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL
    return wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                   weight, faceName='Segoe UI')


class Canvas(wx.Panel):

    def __init__(self, parent, theme):
        super().__init__(parent, style=wx.FULL_REPAINT_ON_RESIZE)
        self.theme = theme
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)

    def set_theme(self, theme):
        self.theme = theme
        self.Refresh()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(wx.Colour(self.theme['bg'])))
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        if gc is None:
            return
        gc.SetAntialiasMode(wx.ANTIALIAS_DEFAULT)
        width, height = self.GetClientSize()
        self.draw(gc, width, height)

    def draw(self, gc, width, height):
        pass

    def fit_text(self, gc, text, limit):
        if gc.GetTextExtent(text)[0] <= limit:
            return text
        while text and gc.GetTextExtent(text + '…')[0] > limit:
            text = text[:-1]
        return text + '…'

    def fit_tail(self, gc, text, limit):
        '''Cuts from the left. A path is told apart by its leaf, not its root.'''
        if gc.GetTextExtent(text)[0] <= limit:
            return text
        while text and gc.GetTextExtent('…' + text)[0] > limit:
            text = text[1:]
        return '…' + text
