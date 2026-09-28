# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

창의 캡션을 떼어내고 그 자리를 앱이 직접 그린다. 왼쪽 끝에 햄버거,
그 옆에 아이콘과 제목, 오른쪽 끝에 최소화·최대화·닫기를 둔다.

끌기는 우리가 계산하지 않고 WM_NCLBUTTONDOWN 을 캡션으로 보내 Windows 에
맡긴다. 그래야 화면 가장자리로 던지는 스냅까지 그대로 따라온다.
'''


import ctypes
import wx

from icons import draw_glyph
from utilities import APP_NAME
from utilities import CAPTION_WIDTH
from utilities import TITLEBAR_HEIGHT
from utilities import Canvas
from utilities import get_asset_path
from utilities import get_font
from utilities import get_frame_margins
from utilities import shade


WM_NCLBUTTONDOWN = 0x00A1
HTCAPTION = 2

ICON_SIZE = 16
GLYPH_SIZE = 15
MENU_GLYPH_SIZE = 14

# 누름 자리는 칸을 꽉 채우지 않고 한 뼘 안으로 들여 모서리를 굴린다. 위쪽 띠는
# DWM 이 칠하는 자리라 우리가 닿을 수 없어, 꽉 채우면 위가 잘린 채로 보인다.
BUTTON_BOX = (34, 25)
BUTTON_RADIUS = 4


class TitleBar(Canvas):

    HEIGHT = TITLEBAR_HEIGHT

    def __init__(self, parent, theme, on_menu, on_maximize):
        super().__init__(parent, theme)
        self.on_menu = on_menu
        self.on_maximize = on_maximize
        self.icon = self.load_icon()
        self.cap_height = None
        self.visible = True
        self.menu_open = False
        self.maximized = False
        self.hovered = None
        self.pressed = None
        self.SetMinSize(wx.Size(-1, self.HEIGHT))
        self.Bind(wx.EVT_LEFT_DOWN, self.on_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_up)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def load_icon(self):
        path = get_asset_path('icon', 'icon.png')
        image = wx.Image(path) if wx.Image.CanRead(path) else None
        if image is None or not image.IsOk():
            return None
        return image.Scale(ICON_SIZE, ICON_SIZE, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()

    def get_cap_height(self):
        '''캔버스 위에 남아 있는 DWM 띠의 높이. 그 띠까지가 눈에 보이는 헤더라,
        요소는 캔버스가 아니라 띠를 포함한 전체의 한가운데에 놓아야 위아래
        여백이 같아진다. 한 번 재고 기억해 둔다.'''
        if self.cap_height is None:
            frame = self.GetTopLevelParent()
            top = frame.GetScreenRect().y + get_frame_margins(frame)[1]
            self.cap_height = max(0, frame.ClientToScreen(wx.Point(0, 0)).y - top)
        return self.cap_height

    def get_middle(self):
        return (self.HEIGHT - self.get_cap_height()) / 2

    def get_box(self, rect):
        middle = self.get_middle()
        return wx.Rect(rect.x + (rect.width - BUTTON_BOX[0]) // 2,
                       round(middle - BUTTON_BOX[1] / 2), *BUTTON_BOX)

    def get_zones(self):
        '''왼쪽 끝의 메뉴와 오른쪽 끝의 캡션 버튼. 나머지는 끌기 영역이다.'''
        width, height = self.GetClientSize()
        zones = [('menu', wx.Rect(0, 0, CAPTION_WIDTH, height))]
        for index, name in enumerate(('close', 'maximize', 'minimize')):
            left = width - CAPTION_WIDTH * (index + 1)
            zones.append((name, wx.Rect(left, 0, CAPTION_WIDTH, height)))
        return zones

    def hit_test(self, position):
        if not self.visible:
            return None
        for name, rect in self.get_zones():
            if rect.Contains(position):
                return name
        return None

    def set_visible(self, visible):
        if visible == self.visible:
            return False
        self.visible = visible
        # 숨어 있는 동안의 움직임은 흘려보냈다. 나타나는 순간 지금 커서 자리로
        # 다시 잡아야, 창에 들어와 버튼 위에 바로 멈춘 손이 아무 반응도 못 받는 일이 없다.
        self.hovered = self.hit_test(
            self.ScreenToClient(wx.GetMousePosition())) if visible else None
        self.Refresh()
        return True

    def set_menu_open(self, opened):
        if opened != self.menu_open:
            self.menu_open = opened
            self.Refresh()

    def set_maximized(self, maximized):
        if maximized != self.maximized:
            self.maximized = maximized
            self.Refresh()

    def start_drag(self):
        '''Windows 에 캡션을 눌렀다고 알린다. 이 호출 안에서 끌기가 끝난다.'''
        try:
            ctypes.windll.user32.ReleaseCapture()
            ctypes.windll.user32.SendMessageW(
                self.GetTopLevelParent().GetHandle(), WM_NCLBUTTONDOWN, HTCAPTION, 0)
        except Exception:
            pass

    def on_down(self, event):
        name = self.hit_test(event.GetPosition())
        if name is None:
            self.start_drag()
            return
        self.pressed = name
        self.Refresh()

    def on_up(self, event):
        name = self.hit_test(event.GetPosition())
        pressed, self.pressed = self.pressed, None
        self.Refresh()
        if name is None or name != pressed:
            return
        if name == 'menu':
            self.on_menu()
        elif name == 'minimize':
            self.GetTopLevelParent().Iconize(True)
        elif name == 'maximize':
            self.on_maximize()
        elif name == 'close':
            self.GetTopLevelParent().Close()

    def on_dclick(self, event):
        if self.hit_test(event.GetPosition()) is None:
            self.on_maximize()

    def on_motion(self, event):
        name = self.hit_test(event.GetPosition())
        if name != self.hovered:
            self.hovered = name
            self.Refresh()

    def on_leave(self, event):
        if self.hovered is not None or self.pressed is not None:
            self.hovered = None
            self.pressed = None
            self.Refresh()

    def get_fill(self, name):
        theme = self.theme
        if name == 'close':
            if self.pressed == name:
                return shade(theme['close'], 0.82)
            return theme['close'] if self.hovered == name else None
        if self.pressed == name:
            return shade(theme['face'], 0.88)
        if self.hovered == name:
            return theme['control']
        if name == 'menu' and self.menu_open:
            return theme['control']
        return None

    def draw(self, gc, width, height):
        if not self.visible:
            return

        theme = self.theme
        middle = self.get_middle()

        for name, rect in self.get_zones():
            fill = self.get_fill(name)
            if fill:
                box = self.get_box(rect)
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.SetBrush(wx.Brush(wx.Colour(fill)))
                gc.DrawRoundedRectangle(box.x, box.y, box.width, box.height,
                                        BUTTON_RADIUS)

            colour = theme['text']
            if name == 'close' and self.hovered == name:
                colour = '#ffffff'
            elif name != 'menu' and self.hovered != name and self.pressed != name:
                colour = theme['dim']

            glyph = name
            if name == 'menu':
                glyph = 'menu'
            elif name == 'maximize' and self.maximized:
                glyph = 'restore'
            size = MENU_GLYPH_SIZE if name == 'menu' else GLYPH_SIZE
            draw_glyph(gc, glyph, rect.x + rect.width / 2, middle, size, colour)

        self.draw_title(gc, width, middle)

    def draw_title(self, gc, width, middle):
        left = CAPTION_WIDTH + 2
        if self.icon:
            gc.DrawBitmap(self.icon, left, middle - ICON_SIZE / 2, ICON_SIZE, ICON_SIZE)
            left += ICON_SIZE + 10

        gc.SetFont(get_font(9), wx.Colour(self.theme['text']))
        text_height = gc.GetTextExtent(APP_NAME)[1]
        gc.Clip(left, 0, max(0, width - CAPTION_WIDTH * 3 - left - 8), self.HEIGHT)
        gc.DrawText(APP_NAME, left, middle - text_height / 2)
        gc.ResetClip()
