# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import os
import subprocess
import time
import wx

from securebox import SecureBox
from settingsbox import SettingsBox
from sidemenu import SideMenu
from titlebar import TitleBar
from updatebox import UpdateBox
from updater import Updater
from updater import restart_source
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
DEFAULT_SIZE = (460, 670)
# settings page 624 + header 32 + frame 14
MIN_SIZE = (380, 670)

FRAME_STYLE = wx.DEFAULT_FRAME_STYLE & ~wx.CAPTION

MIN_VISIBLE_WIDTH = 120
MIN_VISIBLE_HEIGHT = 32

MENU_ITEMS = (('Folders', 'lock'), None, ('Settings', 'settings'))


class MainFrame(wx.Frame):

    stored_rect = None
    restore_bounds = None
    ready = False
    saver = None
    grown = 0
    closing = False

    def __init__(self):
        settings = load_settings()
        if not settings.get('remember', True):
            settings.pop('folders', None)
        super().__init__(None, title=APP_NAME, size=wx.Size(*DEFAULT_SIZE),
                         style=FRAME_STYLE)
        apply_no_caption(self)
        self.SetMinSize(wx.Size(*MIN_SIZE))

        self.theme_name = settings.get('theme', 'dark')
        theme = THEMES[self.theme_name]

        self.set_icon()

        self.book = wx.Simplebook(self)
        self.securebox = SecureBox(self.book, theme, settings, self.store_settings)
        self.settingsbox = SettingsBox(self.book, theme, settings, self.on_settings,
                                       self.on_check_updates)
        for page in (self.securebox, self.settingsbox):
            self.book.AddPage(page, '')

        self.titlebar = TitleBar(self, theme, self.on_menu, self.toggle_maximize)
        # before the menu, which opens over it
        self.updatebox = UpdateBox(self, theme, self.on_update_action, self.fit_notice)
        self.updater = Updater(settings, self.on_update_checked)
        self.release = None
        self.sidemenu = SideMenu(self, theme, MENU_ITEMS, self.on_select)
        apply_clip_siblings(self.book)
        apply_clip_siblings(self.updatebox)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titlebar, 0, wx.EXPAND)
        sizer.Add(self.updatebox, 0, wx.EXPAND)
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
        self.ready = True

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
        self.updatebox.set_theme(theme)
        self.securebox.apply_theme(theme)
        self.settingsbox.apply_theme(theme)
        apply_titlebar_theme(self, theme)
        self.Refresh()

    def on_menu(self):
        self.sidemenu.toggle()

    def on_select(self, index):
        self.book.SetSelection(index)
        self.fit_notice()
        self.store_settings()

    def toggle_maximize(self):
        # Windows maximizes a captionless frame over the taskbar
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
        self.titlebar.set_menu_open(self.sidemenu.is_open())
        if self.closing and not self.securebox.busy:
            self.finish_update()
        self.updater.tick(self.settingsbox.check_updates.GetValue())

    def fit_notice(self):
        # the settings page has no room to give, so the notice adds to the height
        extra = 0
        if self.updatebox.IsShown() and self.book.GetCurrentPage() is self.settingsbox:
            extra = self.updatebox.GetMinSize()[1]
        self.SetMinSize(wx.Size(MIN_SIZE[0], MIN_SIZE[1] + extra))
        if self.restore_bounds is None and not self.IsIconized():
            rect = self.GetRect()
            base = rect.height - self.grown
            height = max(base, MIN_SIZE[1] + extra)
            self.grown = height - base
            if height != rect.height:
                work = wx.Display(max(0, wx.Display.GetFromWindow(self))).GetClientArea()
                top = max(work.y, min(rect.y, work.y + work.height - height))
                self.SetRect(wx.Rect(rect.x, top, rect.width, height))
        self.Layout()

    def on_check_updates(self):
        self.settingsbox.check_now.set_tone('dim')
        self.settingsbox.check_now.set_label('Latest release', 'Checking…')
        self.updater.check(forced=True)

    def set_release_note(self, description, tone='dim'):
        self.settingsbox.check_now.set_label('Latest release', description)
        self.settingsbox.check_now.set_tone(tone)

    def on_update_checked(self, release, result, forced):
        # a queued call can arrive after close
        if not self:
            return
        if result == 'error':
            self.set_release_note('Could not reach GitHub', 'warn')
            return
        self.store_settings()
        checked = time.strftime('%H:%M', time.localtime(self.updater.checked_at))
        if result == 'found':
            self.set_release_note(f'{release["version"]} is available')
            self.show_update(release)
        elif result == 'skipped':
            self.set_release_note(f'{self.updater.skipped} skipped, checked at {checked}')
        else:
            self.set_release_note(f'Up to date, checked at {checked}')

    def show_update(self, release):
        # a notice already updating stays as it is
        if self.updatebox.IsShown() and self.updatebox.state == 'busy':
            return
        self.release = release
        self.updatebox.show_release(release)
        if not self.updatebox.IsShown():
            self.updatebox.Show()
            self.fit_notice()

    def hide_update(self):
        self.updatebox.Hide()
        self.fit_notice()

    def on_update_action(self, key):
        release = self.release
        if key == 'skip':
            self.updater.skipped = release['version']
            self.store_settings()
            self.set_release_note(f'{release["version"]} skipped')
            self.hide_update()
        elif key == 'later':
            self.hide_update()
        elif key == 'cancel':
            self.updater.cancel()
        elif release['kind'] == 'page':
            # explorer hands the link to the shell, so the browser does not inherit elevation
            subprocess.Popen(['explorer', release['page']])
            self.hide_update()
        elif self.securebox.busy:
            # the app closes to update, which would leave a folder half hidden
            self.updatebox.set_failed('Wait until the folders are done')
        else:
            if release['kind'] == 'installer':
                self.updatebox.set_busy('Downloading 0%', 0.0)
            else:
                self.updatebox.set_busy('Updating…')
            self.updater.update(release, self.on_update_progress, self.on_update_done)

    def on_update_progress(self, ratio):
        if not self or self.updatebox.state != 'busy' or self.updatebox.progress is None:
            return
        message = f'Downloading {int(ratio * 100)}%'
        if message != self.updatebox.message:
            self.updatebox.set_busy(message, ratio)

    def on_update_done(self, error):
        if not self:
            return
        if error is not None:
            self.updatebox.set_failed(error)
            return
        self.closing = True
        if self.securebox.busy:
            self.updatebox.set_busy('Closing once the folders are done')
            return
        self.finish_update()

    def finish_update(self):
        self.closing = False
        if self.release['kind'] == 'git':
            try:
                restart_source()
            except OSError:
                self.updatebox.set_failed('Updated, start the app again to use it')
                return
        # the installer replaces the app's files once it is gone
        self.Close()

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
            'rect': self.stored_rect,
            'remember': self.settingsbox.remember.GetValue(),
            'update_check': self.settingsbox.check_updates.GetValue(),
            'update_checked_at': self.updater.checked_at,
            'update_skipped': self.updater.skipped,
        }
        if settings['remember']:
            settings.update(self.securebox.store())
        save_settings(settings)

    def on_close(self, event):
        # closing midway leaves a folder half hidden
        if self.securebox.busy and event.CanVeto():
            self.securebox.hold_close()
            event.Veto()
            return
        self.timer.Stop()
        self.updater.cancel()
        if self.saver is not None and self.saver.IsRunning():
            self.saver.Stop()
        # release the mouse capture before the frame goes
        self.sidemenu.close()
        # close() starts the slide timer, which crashes (0xc0000374) after destroy
        self.sidemenu.timer.Stop()
        if self.restore_bounds is not None:
            self.stored_rect = list(self.restore_bounds)
        elif self.IsIconized() is False and self.IsMaximized() is False:
            # the height the notice added goes with it
            x, y, width, height = self.GetRect()
            self.stored_rect = [x, y, width, height - self.grown]
        self.flush_settings()
        event.Skip()


def launch_mainapp():
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    apply_titlebar_theme(frame, THEMES[frame.theme_name])
    app.MainLoop()
