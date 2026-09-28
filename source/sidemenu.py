# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

햄버거로 여닫는 메뉴. 탭 바를 대신해 페이지를 고른다. 사이저에 담지 않고
페이지 위에 띄워 두었다가 왼쪽에서 밀어 넣는다.

★세로로 창 전체를 덮지 않는다. 높이는 항목이 정하고 헤더 바로 아래 왼쪽
끝에 붙는다 — 가리는 페이지 면적이 그만큼 줄어든다. 아래에 붙이던 항목은
구분선으로 갈라 놓는다(PyWinAgent 의 menubox 와 같은 짜임새).

열려 있는 동안 마우스를 잡아 둔다. 바깥을 누르면 닫히고, 그 누름은
아래로 넘기지 않는다. 햄버거를 다시 누르는 것도 바깥 누름이라 그대로 닫힌다.
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

    # 밀려 들어오는 속도. 남은 거리의 일정 비율씩 좁혀 끝에서 부드럽게 선다.
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
        '''구분선을 뺀 차례가 곧 페이지의 차례다.'''
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
        # 이미 놓친 캡처를 다시 놓으면 assertion 이 뜬다. 상태만 되돌린다.
        if self.opened:
            self.opened = False
            self.hovered = -1
            self.timer.Start(self.STEP)

    def draw(self, gc, width, height):
        theme = self.theme
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.SetBrush(wx.Brush(wx.Colour(theme['bg'])))
        gc.DrawRectangle(0, 0, width, height)

        # 창 전체를 덮지 않으니 서랍의 오른쪽 한 줄이 아니라 네 변으로 경계를 알린다.
        # ★선으로 그으면 왼쪽과 위가 두 픽셀에 반씩 걸쳐 오른쪽·아래보다 굵어
        # 보인다(안티에일리어싱). 1px 채우기로 네 변을 같은 굵기로 세운다.
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
            # 고른 줄을 알리는 왼쪽 짧은 막대. Windows 11 탐색 창과 같은 표시다.
            bar = rect.height * 0.40
            gc.SetBrush(wx.Brush(wx.Colour(theme['accent'])))
            gc.DrawRoundedRectangle(rect.x + 2, rect.y + (rect.height - bar) / 2,
                                    3, bar, 1.5)

        colour = theme['text'] if active or index == self.hovered else theme['dim']
        draw_glyph(gc, glyph, rect.x + self.ICON_LEFT, rect.y + rect.height / 2,
                   self.ICON_SIZE, colour)

        gc.SetFont(get_font(10, bold=active), wx.Colour(colour))
        text_height = gc.GetTextExtent(label)[1]
        # 항목 이름이 EDID 에서 오므로 길이를 앱이 정하지 못한다. 테두리 전에 자른다.
        limit = rect.width - self.LABEL_LEFT - 8
        gc.DrawText(self.fit_text(gc, label, limit), rect.x + self.LABEL_LEFT,
                    rect.y + (rect.height - text_height) / 2)
