# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import wx

from icons import draw_glyph
from utilities import CARD_RADIUS
from utilities import Canvas
from utilities import draw_card_rim
from utilities import get_font
from utilities import mix


class FolderList(Canvas):

    '''떨어뜨린 폴더를 한 줄에 하나씩. 끌어다 놓는 자리이기도 해서 파일이 위에
    떠 있는 동안 테두리가 밝아진다.

    디자인 툴의 레이어 목록처럼 줄마다 왼쪽에 눈이 있다. 누르면 그 폴더만
    숨기고 드러낸다. 숨긴 줄은 탐색기가 숨김 파일을 그리듯 흐리게 그린다 —
    색만이 아니라 눈의 사선으로도 갈린다. 손이 얹힌 줄에는 오른쪽 끝에 × 가
    떠서 목록에서 뺀다.'''

    ROW_HEIGHT = 34
    INSET = 6
    PADDING = 8
    GAP = 16
    BUTTON = 26
    BUTTON_RADIUS = 5
    EYE_SIZE = 16
    REMOVE_SIZE = 9
    BAR_WIDTH = 6
    BAR_INSET = 4
    BAR_MIN = 30
    WHEEL_ROWS = 3
    MIN_HEIGHT = 140
    # 숨긴 줄의 글자는 바탕 쪽으로 이만큼 물러난다.
    HIDDEN_FADE = 0.55

    def __init__(self, parent, theme, empty='', on_toggle=None, on_remove=None):
        super().__init__(parent, theme)
        self.items = []
        self.states = []
        self.empty = empty
        self.on_toggle = on_toggle
        self.on_remove = on_remove
        self.hot = False
        self.enabled = True
        self.working = ()
        self.hover = (-1, None)
        self.offset = 0
        self.dragging = False
        self.grip = 0
        self.SetMinSize(wx.Size(-1, self.MIN_HEIGHT))
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_wheel)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.on_capture_lost)

    def set_empty(self, empty):
        self.empty = empty
        self.Refresh()

    def set_hot(self, hot):
        if hot != self.hot:
            self.hot = hot
            self.Refresh()

    def set_enabled(self, enabled, working=()):
        '''돌고 있는 동안은 누름을 받지 않고, 돌고 있는 줄은 눈 대신 … 을 그린다.'''
        self.enabled = enabled
        self.working = tuple(working)
        self.Refresh()

    def set_items(self, items, states):
        self.items = list(items)
        self.states = list(states) + [''] * (len(self.items) - len(states))
        self.clamp()
        self.Refresh()

    def get_content_height(self):
        return len(self.items) * self.ROW_HEIGHT + self.INSET * 2

    def get_limit(self):
        return max(0, self.get_content_height() - self.GetClientSize().height)

    def clamp(self):
        self.offset = max(0, min(self.offset, self.get_limit()))

    def get_bar_rect(self):
        limit = self.get_limit()
        if not limit:
            return None
        width, height = self.GetClientSize()
        track = height - self.BAR_INSET * 2
        length = max(self.BAR_MIN, track * height / float(self.get_content_height()))
        top = self.BAR_INSET + (track - length) * (self.offset / float(limit))
        return wx.Rect(width - self.BAR_INSET - self.BAR_WIDTH, round(top),
                       self.BAR_WIDTH, round(length))

    def on_size(self, event):
        self.clamp()
        event.Skip()

    def on_wheel(self, event):
        limit = self.get_limit()
        if not limit:
            return
        notches = event.GetWheelRotation() / float(event.GetWheelDelta() or 120)
        offset = max(0, min(limit, self.offset -
                            round(notches * self.ROW_HEIGHT * self.WHEEL_ROWS)))
        if offset != self.offset:
            self.offset = offset
            self.Refresh()

    def set_from_position(self, y):
        limit = self.get_limit()
        bar = self.get_bar_rect()
        if not limit or bar is None:
            return
        track = self.GetClientSize().height - self.BAR_INSET * 2 - bar.height
        if track <= 0:
            return
        ratio = min(1.0, max(0.0, (y - self.grip - self.BAR_INSET) / float(track)))
        offset = round(limit * ratio)
        if offset != self.offset:
            self.offset = offset
            self.Refresh()

    def get_eye_rect(self, index):
        top = self.INSET + index * self.ROW_HEIGHT - self.offset
        return wx.Rect(self.PADDING, top + (self.ROW_HEIGHT - self.BUTTON) // 2,
                       self.BUTTON, self.BUTTON)

    def get_remove_rect(self, index):
        width = self.GetClientSize().width
        bar = self.get_bar_rect()
        right = width - self.PADDING - (self.BAR_WIDTH + self.BAR_INSET if bar else 0)
        top = self.INSET + index * self.ROW_HEIGHT - self.offset
        return wx.Rect(right - self.BUTTON, top + (self.ROW_HEIGHT - self.BUTTON) // 2,
                       self.BUTTON, self.BUTTON)

    def hit_test(self, position):
        index = (position.y + self.offset - self.INSET) // self.ROW_HEIGHT
        if position.y < 0 or not 0 <= index < len(self.items):
            return (-1, None)
        if self.get_eye_rect(index).Contains(position):
            return (index, 'eye')
        if self.get_remove_rect(index).Contains(position):
            return (index, 'remove')
        return (index, None)

    def set_hover(self, hover):
        if hover == self.hover:
            return
        self.hover = hover
        pointing = self.enabled and hover[1] is not None and self.can_press(*hover)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND if pointing else wx.CURSOR_ARROW))
        self.Refresh()

    def can_press(self, index, part):
        if part == 'eye':
            return self.states[index] in ('hidden', 'visible', 'mixed')
        return part == 'remove'

    def on_down(self, event):
        bar = self.get_bar_rect()
        if bar is not None and bar.Inflate(6, 0).Contains(event.GetPosition()):
            self.grip = event.GetPosition().y - bar.y
            self.dragging = True
            if not self.HasCapture():
                try:
                    self.CaptureMouse()
                except Exception:
                    self.dragging = False
            return

        index, part = self.hit_test(event.GetPosition())
        if not self.enabled or part is None or not self.can_press(index, part):
            return
        if part == 'eye' and self.on_toggle:
            self.on_toggle(index)
        elif part == 'remove' and self.on_remove:
            self.set_hover((-1, None))
            self.on_remove(index)

    def on_up(self, event):
        self.dragging = False
        if self.HasCapture():
            self.ReleaseMouse()

    def on_motion(self, event):
        if self.dragging:
            self.set_from_position(event.GetPosition().y)
        else:
            self.set_hover(self.hit_test(event.GetPosition()))
        event.Skip()

    def on_leave(self, event):
        self.set_hover((-1, None))
        event.Skip()

    def on_capture_lost(self, event):
        self.dragging = False

    def draw(self, gc, width, height):
        theme = self.theme
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.SetBrush(wx.Brush(wx.Colour(theme['face'])))
        gc.DrawRoundedRectangle(0, 0, width, height, CARD_RADIUS)
        draw_card_rim(gc, theme['accent' if self.hot else 'rim'], 0, 0, width, height)

        if not self.items:
            self.draw_empty(gc, width, height)
            return

        first = max(0, (self.offset - self.INSET) // self.ROW_HEIGHT)
        last = min(len(self.items), first + height // self.ROW_HEIGHT + 2)

        gc.Clip(1, 1, width - 2, height - 2)
        for index in range(first, last):
            self.draw_row(gc, index)
        gc.ResetClip()

        bar = self.get_bar_rect()
        if bar is not None:
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.SetBrush(wx.Brush(wx.Colour(theme['track'])))
            gc.DrawRoundedRectangle(bar.x, bar.y, bar.width, bar.height,
                                    self.BAR_WIDTH / 2.0)

    def draw_button(self, gc, rect, pressed_part, index):
        if self.hover != (index, pressed_part) or not self.enabled:
            return
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.SetBrush(wx.Brush(mix(self.theme['face'], self.theme['text'], 0.10)))
        gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, self.BUTTON_RADIUS)

    def draw_row(self, gc, index):
        theme = self.theme
        name, folder = self.items[index]
        state = self.states[index]
        top = self.INSET + index * self.ROW_HEIGHT - self.offset
        hovered = self.hover[0] == index

        text = theme['text']
        dim = theme['dim']
        if state in ('hidden', 'missing'):
            text = mix(theme['text'], theme['face'], self.HIDDEN_FADE)
            dim = mix(theme['dim'], theme['face'], self.HIDDEN_FADE)

        eye = self.get_eye_rect(index)
        self.draw_button(gc, eye, 'eye', index)
        cx, cy = eye.x + eye.width / 2.0, eye.y + eye.height / 2.0
        if index in self.working:
            gc.SetFont(get_font(10, bold=True), wx.Colour(theme['accent']))
            dots_width, dots_height = gc.GetTextExtent('…')[:2]
            gc.DrawText('…', cx - dots_width / 2, cy - dots_height / 2 - 3)
        elif state == 'hidden':
            draw_glyph(gc, 'eye_off', cx, cy, self.EYE_SIZE, theme['dim'])
        elif state == 'mixed':
            draw_glyph(gc, 'eye', cx, cy, self.EYE_SIZE, theme['warn'])
        elif state == 'visible':
            draw_glyph(gc, 'eye', cx, cy, self.EYE_SIZE, theme['text'])

        remove = self.get_remove_rect(index)
        right = remove.x if hovered and self.enabled else remove.x + remove.width
        if hovered and self.enabled:
            self.draw_button(gc, remove, 'remove', index)
            draw_glyph(gc, 'close', remove.x + remove.width / 2.0,
                       remove.y + remove.height / 2.0, self.REMOVE_SIZE, theme['dim'],
                       width=1.2)

        left = eye.x + eye.width + 8
        note = {'mixed': 'partly hidden', 'missing': 'not found', '': 'empty'}.get(state)
        gc.SetFont(get_font(9), wx.Colour(theme['warn'] if state == 'mixed' else dim))
        detail = note if note else folder
        limit = max(0, (right - left) * 0.5)
        detail = self.fit_tail(gc, detail, min(gc.GetTextExtent(detail)[0], limit))
        detail_width, detail_height = gc.GetTextExtent(detail)[:2]
        middle = top + (self.ROW_HEIGHT - detail_height) / 2
        gc.DrawText(detail, right - 6 - detail_width, middle)

        gc.SetFont(get_font(9), wx.Colour(text))
        room = max(0, right - 6 - detail_width - self.GAP - left)
        gc.DrawText(self.fit_text(gc, name, room), left, middle)

    def draw_empty(self, gc, width, height):
        if not self.empty:
            return
        gc.SetFont(get_font(9), wx.Colour(self.theme['dim']))
        text_width, text_height = gc.GetTextExtent(self.empty)[:2]
        gc.DrawText(self.empty, (width - text_width) / 2, (height - text_height) / 2)
