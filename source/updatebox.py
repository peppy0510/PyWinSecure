# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import wx

from controls import Pressable
from utilities import APP_NAME
from utilities import APP_VERSION
from utilities import CARD_RADIUS
from utilities import draw_card_rim
from utilities import get_font
from utilities import mix
from utilities import shade


MARGIN = 16
TOP_GAP = 8
PADDING = 14
TITLE_ROW = 20
NOTE_ROW = 16
LINE_ROW = 18
NOTES_GAP = 8
NOTES_LINES = 6
BUTTONS_GAP = 12
BUTTON_HEIGHT = 26
BUTTON_PADDING = 16
BUTTON_RADIUS = 5
BUTTON_GAP = 6
PROGRESS_HEIGHT = 2
SCROLL_WIDTH = 2

CAPTIONS = {'skip': 'Skip this version', 'later': 'Later', 'cancel': 'Cancel'}
UPDATE_CAPTIONS = {'installer': 'Update now', 'git': 'Update now', 'page': 'Release page'}


def get_text_width(font, text):
    dc = wx.MemoryDC(wx.Bitmap(1, 1))
    dc.SetFont(font)
    return dc.GetTextExtent(text)[0]


def wrap_text(font, text, width):
    # a word wider than the line keeps a line of its own and is cut when drawn
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            trial = f'{line} {word}' if line else word
            if not line or get_text_width(font, trial) <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


class UpdateBox(Pressable):

    def __init__(self, parent, theme, on_action, on_resize):
        super().__init__(parent, theme, self.choose)
        self.on_action = on_action
        self.on_resize = on_resize
        self.release = None
        # 'found', then 'busy' while updating and 'failed' with a message after an error
        self.state = 'found'
        self.message = ''
        self.progress = None
        self.lines = []
        self.top_line = 0
        self.wrapped_width = 0
        self.down_index = -1
        self.Bind(wx.EVT_MOTION, lambda event: self.Refresh())
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_wheel)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Hide()

    def show_release(self, release):
        self.release = release
        self.state = 'found'
        self.message = ''
        self.progress = None
        self.top_line = 0
        self.wrapped_width = 0
        self.relayout()

    def set_busy(self, message, progress=None):
        self.state = 'busy'
        self.message = message
        self.progress = progress
        self.relayout()

    def set_failed(self, message):
        self.state = 'failed'
        self.message = message
        self.progress = None
        self.relayout()

    def get_buttons(self):
        if self.state == 'busy':
            # a pull cannot stop halfway
            return [('cancel', CAPTIONS['cancel'])] if self.progress is not None else []
        update = 'Retry' if self.state == 'failed' else UPDATE_CAPTIONS[self.release['kind']]
        return [('skip', CAPTIONS['skip']), ('later', CAPTIONS['later']), ('update', update)]

    def get_card(self, width, height):
        return wx.Rect(MARGIN, TOP_GAP, max(0, width - MARGIN * 2), height - TOP_GAP)

    def get_notes_width(self, width):
        return self.get_card(width, 0).width - PADDING * 2 - SCROLL_WIDTH * 3

    def wrap(self, width):
        notes_width = self.get_notes_width(width)
        if notes_width != self.wrapped_width:
            self.wrapped_width = notes_width
            notes = self.release['notes'] if self.release else ''
            self.lines = wrap_text(get_font(9), notes, notes_width) if notes else []
            self.top_line = min(self.top_line, self.get_scroll_limit())

    def get_visible_lines(self):
        return min(len(self.lines), NOTES_LINES)

    def get_scroll_limit(self):
        return max(0, len(self.lines) - NOTES_LINES)

    def get_height(self, width):
        self.wrap(width)
        height = TOP_GAP + PADDING + TITLE_ROW + NOTE_ROW
        if self.lines:
            height += NOTES_GAP + LINE_ROW * self.get_visible_lines()
        if self.get_buttons() or self.progress is not None:
            height += BUTTONS_GAP + BUTTON_HEIGHT
        return height + PADDING

    def relayout(self):
        width = self.GetParent().GetClientSize()[0]
        height = self.get_height(width)
        if height != self.GetMinSize()[1]:
            self.SetMinSize(wx.Size(-1, height))
            self.on_resize()
        self.Refresh()

    def on_size(self, event):
        width = self.GetClientSize()[0]
        if self.release and self.get_notes_width(width) != self.wrapped_width:
            # the parent lays out again after this size settles
            wx.CallAfter(self.relayout)
        event.Skip()

    def get_button_rects(self, width, height):
        card = self.get_card(width, height)
        font = get_font(9)
        right = card.x + card.width - PADDING
        top = card.y + card.height - PADDING - BUTTON_HEIGHT
        rects = []
        for key, caption in reversed(self.get_buttons()):
            button = get_text_width(font, caption) + BUTTON_PADDING * 2
            right -= button
            rects.insert(0, (key, caption, wx.Rect(right, top, button, BUTTON_HEIGHT)))
            right -= BUTTON_GAP
        return rects

    def get_index(self, position):
        width, height = self.GetClientSize()
        for index, (key, caption, rect) in enumerate(self.get_button_rects(width, height)):
            if rect.Contains(position):
                return index
        return -1

    def get_hovered(self):
        if not self.hovered:
            return -1
        return self.get_index(self.ScreenToClient(wx.GetMousePosition()))

    def on_down(self, event):
        self.down_index = self.get_index(event.GetPosition())
        super().on_down(event)

    def choose(self):
        index = self.get_hovered()
        buttons = self.get_buttons()
        if 0 <= index < len(buttons) and index == self.down_index:
            self.on_action(buttons[index][0])

    def on_wheel(self, event):
        limit = self.get_scroll_limit()
        if not limit:
            return
        lines = int(round(event.GetWheelRotation() / float(event.GetWheelDelta())))
        top_line = min(limit, max(0, self.top_line - lines))
        if top_line != self.top_line:
            self.top_line = top_line
            self.Refresh()

    def draw(self, gc, width, height):
        if not self.release:
            return
        theme = self.theme
        card = self.get_card(width, height)
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.SetBrush(wx.Brush(wx.Colour(theme['face'])))
        gc.DrawRoundedRectangle(card.x, card.y, card.width, card.height, CARD_RADIUS)
        draw_card_rim(gc, theme['rim'], card.x, card.y, card.width, card.height)
        left = card.x + PADDING
        limit = card.width - PADDING * 2
        top = card.y + PADDING

        gc.SetFont(get_font(10, bold=True), wx.Colour(theme['text']))
        self.draw_row(gc, f'{APP_NAME} {self.release["version"]} is available', left, top,
                      TITLE_ROW, limit)
        top += TITLE_ROW

        colour = theme['warn'] if self.state == 'failed' else theme['dim']
        gc.SetFont(get_font(8), wx.Colour(colour))
        self.draw_row(gc, self.message or f'You have {APP_VERSION}', left, top, NOTE_ROW, limit)
        top += NOTE_ROW

        if self.lines:
            top += NOTES_GAP
            self.draw_notes(gc, left, top, limit)

        rects = self.get_button_rects(width, height)
        if self.progress is not None:
            self.draw_progress(gc, left, card.y + card.height - PADDING - BUTTON_HEIGHT,
                               (rects[0][2].x - BUTTONS_GAP if rects else left + limit) - left)
        hovered = self.get_hovered()
        for index, (key, caption, rect) in enumerate(rects):
            self.draw_button(gc, rect, caption, key == 'update', index == hovered,
                             self.pressed and index == hovered and index == self.down_index)

    def draw_row(self, gc, text, left, top, row, limit):
        text = self.fit_text(gc, text, limit)
        gc.DrawText(text, left, top + (row - gc.GetTextExtent(text or 'A')[1]) / 2)

    def draw_notes(self, gc, left, top, limit):
        theme = self.theme
        gc.SetFont(get_font(9), wx.Colour(theme['text']))
        notes_limit = limit - SCROLL_WIDTH * 3
        shown = self.lines[self.top_line:self.top_line + NOTES_LINES]
        for index, line in enumerate(shown):
            self.draw_row(gc, line, left, top + LINE_ROW * index, LINE_ROW, notes_limit)
        scroll = self.get_scroll_limit()
        if scroll:
            track = LINE_ROW * len(shown)
            thumb = max(12, round(track * NOTES_LINES / len(self.lines)))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.SetBrush(wx.Brush(wx.Colour(theme['rim'])))
            gc.DrawRoundedRectangle(left + limit - SCROLL_WIDTH,
                                    top + round((track - thumb) * self.top_line / scroll),
                                    SCROLL_WIDTH, thumb, 1)

    def draw_progress(self, gc, left, top, width):
        theme = self.theme
        y = top + (BUTTON_HEIGHT - PROGRESS_HEIGHT) // 2
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.SetBrush(wx.Brush(wx.Colour(theme['track'])))
        gc.DrawRoundedRectangle(left, y, width, PROGRESS_HEIGHT, 1)
        done = round(width * min(1.0, max(0.0, self.progress)))
        if done:
            gc.SetBrush(wx.Brush(wx.Colour(theme['accent'])))
            gc.DrawRoundedRectangle(left, y, done, PROGRESS_HEIGHT, 1)

    def draw_button(self, gc, rect, caption, primary, hovered, pressed):
        theme = self.theme
        if primary:
            fill, colour = theme['accent'], theme['on_accent']
            if pressed:
                fill = shade(fill, 0.90)
            elif hovered:
                fill = mix(fill, theme['on_accent'], 0.12)
        else:
            fill, colour = theme['control'], theme['text']
            if pressed:
                fill = shade(fill, 0.90)
            elif hovered:
                fill = mix(fill, theme['text'], 0.14)
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.SetBrush(wx.Brush(wx.Colour(fill)))
        gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, BUTTON_RADIUS)
        gc.SetFont(get_font(9), wx.Colour(colour))
        text_width, text_height = gc.GetTextExtent(caption)[:2]
        gc.DrawText(caption, rect.x + (rect.width - text_width) / 2,
                    rect.y + (rect.height - text_height) / 2)
