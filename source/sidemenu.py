# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import wx

from icons import draw_glyph
from utilities import Canvas
from utilities import get_font
from utilities import mix


class SideMenu(Canvas):

    WIDTH = 200
    ITEM_HEIGHT = 36
    SEPARATOR_HEIGHT = 9
    MARGIN = 6
    RADIUS = 5
    ICON_SIZE = 17
    ICON_LEFT = 24
    LABEL_LEFT = 44

    STEP = 12
    EASING = 0.34

    def __init__(self, parent, theme, items, on_select):
        super().__init__(parent, theme)
        self.items = items
        self.on_select = on_select
        self.selected = 0
        self.hovered = -1
        self.opened = False
        self.shift = float(self.WIDTH)
        self.top = 0

        self.timer = wx.Timer(self)
        self.Hide()
        self.Bind(wx.EVT_TIMER, self.on_slide)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.on_capture_lost)

    def get_height(self):
        total = self.MARGIN * 2
        for item in self.items:
            total += self.ITEM_HEIGHT if item else self.SEPARATOR_HEIGHT
        return total

    def place(self, top):
        self.top = top
        self.SetSize(-round(self.shift), top, self.WIDTH, self.get_height())

    def is_open(self):
        return self.opened

    def toggle(self):
        self.close() if self.opened else self.open()

    def open(self):
        if self.opened:
            return
        self.opened = True
        self.Show()
        self.Raise()
        if not self.HasCapture():
            self.CaptureMouse()
        self.timer.Start(self.STEP)

    def close(self):
        if not self.opened:
            return
        self.opened = False
        self.hovered = -1
        if self.HasCapture():
            self.ReleaseMouse()
        self.timer.Start(self.STEP)

    def set_selection(self, index):
        if index != self.selected:
            self.selected = index
            self.Refresh()

    def on_slide(self, event):
        target = 0.0 if self.opened else float(self.WIDTH)
        self.shift += (target - self.shift) * self.EASING
        if abs(target - self.shift) < 1:
            self.shift = target
            self.timer.Stop()
            if not self.opened:
                self.Hide()
        self.SetPosition(wx.Point(-round(self.shift), self.top))

    def contains(self, position):
        width, height = self.GetClientSize()
        return 0 <= position.x < width and 0 <= position.y < height

    def get_page(self, index):
        return sum(1 for item in self.items[:index] if item)

    def get_item_rect(self, index):
        top = self.MARGIN
        for item in self.items[:index]:
            top += self.ITEM_HEIGHT if item else self.SEPARATOR_HEIGHT
        return wx.Rect(self.MARGIN, top, self.WIDTH - self.MARGIN * 2, self.ITEM_HEIGHT)

    def hit_test(self, position):
        if not self.contains(position):
            return -1
        for index, item in enumerate(self.items):
            if item and self.get_item_rect(index).Contains(position):
                return index
        return -1

    def on_down(self, event):
        if not self.contains(event.GetPosition()):
            self.close()

    def on_up(self, event):
        index = self.hit_test(event.GetPosition())
        if index < 0:
            return
        self.set_selection(index)
        self.close()
        self.on_select(self.get_page(index))

    def on_motion(self, event):
        index = self.hit_test(event.GetPosition())
        if index != self.hovered:
            self.hovered = index
            self.Refresh()

    def on_leave(self, event):
        if self.hovered != -1:
            self.hovered = -1
            self.Refresh()

    def on_capture_lost(self, event):
        # releasing a lost capture asserts
        if self.opened:
            self.opened = False
            self.hovered = -1
            self.timer.Start(self.STEP)

    def draw(self, gc, width, height):
        theme = self.theme
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.SetBrush(wx.Brush(wx.Colour(theme['bg'])))
        gc.DrawRectangle(0, 0, width, height)

        # 1px fills, a pen draws the left and top edges thicker
        gc.SetBrush(wx.Brush(wx.Colour(theme['rim'])))
        gc.DrawRectangle(0, 0, 1, height)
        gc.DrawRectangle(width - 1, 0, 1, height)
        gc.DrawRectangle(0, 0, width, 1)
        gc.DrawRectangle(0, height - 1, width, 1)

        for index, item in enumerate(self.items):
            if item:
                self.draw_item(gc, index, *item)
            else:
                self.draw_separator(gc, index)

    def draw_separator(self, gc, index):
        rect = self.get_item_rect(index)
        middle = rect.y + self.SEPARATOR_HEIGHT / 2
        gc.SetPen(wx.Pen(wx.Colour(self.theme['rim']), 1))
        gc.StrokeLine(rect.x + 4, middle, rect.x + rect.width - 4, middle)

    def draw_item(self, gc, index, label, glyph):
        theme = self.theme
        rect = self.get_item_rect(index)
        active = index == self.selected

        if active:
            fill = theme['control']
        elif index == self.hovered:
            fill = mix(theme['bg'], theme['control'], 0.55)
        else:
            fill = None

        if fill:
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.SetBrush(wx.Brush(wx.Colour(fill)))
            gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, self.RADIUS)

        if active:
            bar = rect.height * 0.40
            gc.SetBrush(wx.Brush(wx.Colour(theme['accent'])))
            gc.DrawRoundedRectangle(rect.x + 2, rect.y + (rect.height - bar) / 2,
                                    3, bar, 1.5)

        colour = theme['text'] if active or index == self.hovered else theme['dim']
        draw_glyph(gc, glyph, rect.x + self.ICON_LEFT, rect.y + rect.height / 2,
                   self.ICON_SIZE, colour)

        gc.SetFont(get_font(10, bold=active), wx.Colour(colour))
        text_height = gc.GetTextExtent(label)[1]
        limit = rect.width - self.LABEL_LEFT - 8
        gc.DrawText(self.fit_text(gc, label, limit), rect.x + self.LABEL_LEFT,
                    rect.y + (rect.height - text_height) / 2)
