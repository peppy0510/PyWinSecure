# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import os
import wx

from securebox import SecureBox
from settingsbox import SettingsBox
from sidemenu import SideMenu
from titlebar import TitleBar
from utilities import APP_NAME
from utilities import THEMES
from utilities import apply_clip_siblings
from utilities import apply_no_caption
from utilities import apply_titlebar_theme
from utilities import get_asset_path
from utilities import get_frame_margins
from utilities import load_settings
from utilities import save_settings


HOVER_INTERVAL = 120
SAVE_DELAY = 600
DEFAULT_SIZE = (460, 600)
# 설정 페이지가 잘리지 않는 높이다(실측: 내용 356 + 헤더 32 + 창틀 14).
MIN_SIZE = (380, 402)

# 캡션을 떼고 그 자리를 직접 그린다. 크기 조절과 스냅은 그대로 남는다.
FRAME_STYLE = wx.DEFAULT_FRAME_STYLE & ~wx.CAPTION

# 기억된 위치가 이만큼도 화면에 안 걸리면 사라진 모니터로 본다.
MIN_VISIBLE_WIDTH = 120
MIN_VISIBLE_HEIGHT = 32

PAGE_KEYS = ('folders', 'settings')

MENU_ITEMS = (('Folders', 'lock'), None, ('Settings', 'settings'))


class MainFrame(wx.Frame):

    stored_rect = None
    # 흉내 낸 최대화 이전의 자리. None 이면 최대화 상태가 아니다.
    restore_bounds = None
    ready = False
    saver = None

    def __init__(self):
        settings = load_settings()
        super().__init__(None, title=APP_NAME, size=wx.Size(*DEFAULT_SIZE),
                         style=FRAME_STYLE)
        apply_no_caption(self)
        self.SetMinSize(wx.Size(*MIN_SIZE))

        self.theme_name = settings.get('theme', 'dark')
        theme = THEMES[self.theme_name]

        self.set_icon()

        self.book = wx.Simplebook(self)
        self.securebox = SecureBox(self.book, theme, settings, self.store_settings)
        self.settingsbox = SettingsBox(self.book, theme, settings, self.on_settings)
        for page in (self.securebox, self.settingsbox):
            self.book.AddPage(page, '')

        self.titlebar = TitleBar(self, theme, self.on_menu, self.toggle_maximize)
        self.sidemenu = SideMenu(self, theme, MENU_ITEMS, self.on_select)
        # 서랍은 페이지 위에 떠 있다. 페이지 쪽이 형제를 클립해 주어야 살아남는다.
        apply_clip_siblings(self.book)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titlebar, 0, wx.EXPAND)
        sizer.Add(self.book, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.apply_theme()
        self.on_settings()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_tick)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MAXIMIZE, self.on_maximize)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.timer.Start(HOVER_INTERVAL)
        self.restore_rect(settings)
        self.restore_page(settings)
        self.ready = True

    def restore_page(self, settings):
        stored = settings.get('page')
        index = PAGE_KEYS.index(stored) if stored in PAGE_KEYS else 0
        self.book.SetSelection(index)
        # 구분선이 하나 끼어 있어 항목의 차례와 페이지의 차례가 그 뒤로 어긋난다.
        self.sidemenu.set_selection(index if not index else index + 1)

    def get_page_key(self):
        index = self.book.GetSelection()
        return PAGE_KEYS[index] if 0 <= index < len(PAGE_KEYS) else PAGE_KEYS[0]

    def is_rect_visible(self, rect):
        for index in range(wx.Display.GetCount()):
            shared = wx.Display(index).GetClientArea().Intersect(rect)
            if shared.width >= MIN_VISIBLE_WIDTH and shared.height >= MIN_VISIBLE_HEIGHT:
                return True
        return False

    def centre_on_primary(self):
        primary = wx.Display(wx.Display.GetFromPoint(wx.Point(0, 0))).GetClientArea()
        width, height = self.GetSize()
        self.SetPosition(wx.Point(primary.x + (primary.width - width) // 2,
                                  primary.y + (primary.height - height) // 2))

    def restore_rect(self, settings):
        stored = settings.get('rect')
        if stored and len(stored) == 4:
            rect = wx.Rect(*stored)
            if self.is_rect_visible(rect):
                self.SetRect(rect)
                self.stored_rect = list(stored)
                return
            self.SetSize(rect.GetSize())

        self.centre_on_primary()
        self.stored_rect = list(self.GetRect())

    def set_icon(self):
        path = get_asset_path('icon', 'icon.ico')
        if os.path.exists(path):
            self.SetIcon(wx.Icon(path, wx.BITMAP_TYPE_ICO))

    def apply_theme(self):
        theme = THEMES[self.theme_name]
        self.SetBackgroundColour(wx.Colour(theme['bg']))
        self.book.SetBackgroundColour(wx.Colour(theme['bg']))
        self.titlebar.set_theme(theme)
        self.sidemenu.set_theme(theme)
        self.securebox.apply_theme(theme)
        self.settingsbox.apply_theme(theme)
        apply_titlebar_theme(self, theme)
        self.Refresh()

    def on_menu(self):
        self.sidemenu.toggle()

    def on_select(self, index):
        self.book.SetSelection(index)
        self.store_settings()

    def toggle_maximize(self):
        '''캡션이 없는 창을 Windows 가 최대화하면 보이지 않는 여백만큼 화면
        밖으로 넘치고 작업 표시줄까지 덮는다. 작업 영역에 맞춰 직접 채운다.'''
        if self.restore_bounds is not None:
            bounds, self.restore_bounds = self.restore_bounds, None
            self.SetRect(wx.Rect(*bounds))
        else:
            self.restore_bounds = list(self.GetRect())
            index = max(0, wx.Display.GetFromWindow(self))
            work = wx.Display(index).GetClientArea()
            left, top, right, bottom = get_frame_margins(self)
            self.SetRect(wx.Rect(work.x - left, work.y - top,
                                 work.width + left + right,
                                 work.height + top + bottom))
        self.titlebar.set_maximized(self.restore_bounds is not None)

    def on_maximize(self, event):
        if not self.IsMaximized():
            return
        self.Maximize(False)
        if self.restore_bounds is None:
            self.toggle_maximize()

    def on_char(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE and self.sidemenu.is_open():
            self.sidemenu.close()
            return
        event.Skip()

    def on_settings(self):
        style = self.GetWindowStyle()
        if self.settingsbox.ontop.GetValue():
            self.SetWindowStyle(style | wx.STAY_ON_TOP)
        else:
            self.SetWindowStyle(style & ~wx.STAY_ON_TOP)

        theme_name = 'dark' if self.settingsbox.dark.GetValue() else 'light'
        if theme_name != self.theme_name:
            self.theme_name = theme_name
            self.apply_theme()
        self.store_settings()

    def on_size(self, event):
        self.sidemenu.place(TitleBar.HEIGHT)
        event.Skip()

    def on_tick(self, event):
        # 서랍은 바깥 누름·ESC·캡처 잃음으로도 닫힌다. 햄버거 표시는 여기서 따라간다.
        self.titlebar.set_menu_open(self.sidemenu.is_open())

    def store_settings(self):
        if not self.ready:
            return
        if self.saver is not None and self.saver.IsRunning():
            self.saver.Stop()
        self.saver = wx.CallLater(SAVE_DELAY, self.flush_settings)

    def flush_settings(self):
        settings = {
            'theme': self.theme_name,
            'on_top': self.settingsbox.ontop.GetValue(),
            'page': self.get_page_key(),
            'rect': self.stored_rect,
        }
        settings.update(self.securebox.store())
        save_settings(settings)

    def on_close(self, event):
        # 도중에 닫으면 폴더가 반만 숨겨진 채 남는다. 끝날 때까지 기다리게 한다.
        if self.securebox.busy and event.CanVeto():
            self.securebox.hold_close()
            event.Veto()
            return
        self.timer.Stop()
        if self.saver is not None and self.saver.IsRunning():
            self.saver.Stop()
        # 마우스를 잡은 채로 창이 사라지면 나중에 죽는다. 먼저 놓게 한다.
        self.sidemenu.close()
        # close 가 닫는 애니메이션 타이머를 켠다. 창이 사라진 뒤 그 타이머가 오면
        # 힙이 깨져 종료 코드 0xc0000374 로 죽는다.
        self.sidemenu.timer.Stop()
        if self.restore_bounds is not None:
            self.stored_rect = list(self.restore_bounds)
        elif self.IsIconized() is False and self.IsMaximized() is False:
            self.stored_rect = list(self.GetRect())
        self.flush_settings()
        event.Skip()


def launch_mainapp():
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    apply_titlebar_theme(frame, THEMES[frame.theme_name])
    app.MainLoop()
