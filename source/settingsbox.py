# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import makeshortcut
import subprocess
import sys
import wx

from controls import AboutCard
from controls import ButtonCard
from controls import SettingCard
from utilities import APP_AUTHOR
from utilities import APP_EMAIL
from utilities import APP_HOME
from utilities import APP_NAME
from utilities import APP_VERSION
from utilities import get_asset_path
from utilities import get_font


MARGIN = 16
TITLE_INSET = 3
TITLE_GAP = 8
CARD_GAP = 4
GROUP_GAP = 14

SHORTCUT_OFF = 'Put a shortcut in the Start menu'
SHORTCUT_ON = 'A shortcut is in the Start menu'
UPDATE_NOTE = 'Look for a new release on GitHub'


class SettingsBox(wx.Panel):

    def __init__(self, parent, theme, settings, on_change, on_check):
        super().__init__(parent)
        self.ontop = SettingCard(self, theme, 'Always on top',
                                 'Keep the window above others', on_change)
        self.dark = SettingCard(self, theme, 'Dark theme',
                                'Use the dark colour scheme', on_change)
        self.remember = SettingCard(self, theme, 'Remember folders',
                                    'Keep the folder list for next time', on_change)
        # a source run only: an installed exe has the installer's Start menu entry
        self.shortcut = None
        if not getattr(sys, 'frozen', False):
            self.shortcut = ButtonCard(self, theme, 'Start menu', SHORTCUT_OFF, 'Create',
                                       self.on_shortcut)
            self.update_shortcut()
        self.check_updates = SettingCard(self, theme, 'Check for updates',
                                         'Once a day, a notice when one is out', on_change)
        self.check_now = ButtonCard(self, theme, 'Latest release', UPDATE_NOTE,
                                    'Check now', on_check)
        self.about = AboutCard(self, theme, f'{APP_NAME} {APP_VERSION}',
                               (APP_AUTHOR, APP_EMAIL), 'GitHub', self.on_home,
                               wx.Image(get_asset_path('icon', 'muteklab.png')))
        self.cards = tuple(card for card in (
            self.ontop, self.dark, self.remember, self.shortcut, self.check_updates,
            self.check_now, self.about) if card)

        self.ontop.SetValue(settings.get('on_top', True))
        self.dark.SetValue(settings.get('theme', 'dark') == 'dark')
        self.remember.SetValue(settings.get('remember', True))
        self.check_updates.SetValue(settings.get('update_check', True))

        self.groups = []
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(MARGIN)
        for title, cards in (('Window', (self.ontop, self.dark)),
                             ('Startup', (self.remember,)),
                             ('Shortcut', (self.shortcut,)),
                             ('Updates', (self.check_updates, self.check_now)),
                             ('About', (self.about,))):
            cards = [card for card in cards if card]
            if not cards:
                continue
            label = wx.StaticText(self, label=title)
            label.SetFont(get_font(10, bold=True))
            self.groups.append(label)
            sizer.Add(label, 0, wx.LEFT, MARGIN + TITLE_INSET)
            sizer.AddSpacer(TITLE_GAP)
            for index, card in enumerate(cards):
                if index:
                    sizer.AddSpacer(CARD_GAP)
                sizer.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, MARGIN)
            sizer.AddSpacer(GROUP_GAP)
        sizer.AddStretchSpacer()
        self.SetSizer(sizer)
        self.apply_theme(theme)

    def update_shortcut(self, note=None):
        present = makeshortcut.has_start_menu()
        self.shortcut.set_caption('Remove' if present else 'Create')
        self.shortcut.set_label('Start menu', note or (SHORTCUT_ON if present else SHORTCUT_OFF))

    def on_shortcut(self):
        try:
            if makeshortcut.has_start_menu():
                makeshortcut.remove_start_menu()
                note = 'Shortcut removed'
            else:
                makeshortcut.create(makeshortcut.get_start_menu_paths()[0])
                note = 'Shortcut created'
        except Exception:
            self.shortcut.set_label('Start menu', 'Could not change the shortcut')
            self.shortcut.set_tone('warn')
            return
        self.update_shortcut(note)
        self.shortcut.set_tone('done')

    def on_home(self):
        # explorer hands the link to the shell, so the browser does not inherit elevation
        subprocess.Popen(['explorer', APP_HOME])

    def apply_theme(self, theme):
        self.SetBackgroundColour(wx.Colour(theme['bg']))
        for label in self.groups:
            label.SetForegroundColour(wx.Colour(theme['text']))
        for card in self.cards:
            card.set_theme(theme)
        self.Refresh()
