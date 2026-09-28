# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import makeshortcut
import wx

from controls import ButtonCard
from controls import NoticeCard
from controls import SettingCard
from shortcut import ShortCut
from utilities import APP_AUTHOR
from utilities import APP_NAME
from utilities import APP_VERSION
from utilities import get_font


MARGIN = 16
TITLE_INSET = 3
TITLE_GAP = 8
CARD_GAP = 4
GROUP_GAP = 14


class SettingsBox(wx.Panel):

    def __init__(self, parent, theme, settings, on_change):
        super().__init__(parent)
        self.ontop = SettingCard(self, theme, 'Always on top',
                                 'Keep the window above others', on_change)
        self.dark = SettingCard(self, theme, 'Dark theme',
                                'Use the dark colour scheme', on_change)
        self.shortcut = ButtonCard(self, theme, 'Start menu',
                                   'Put a shortcut in the Start menu',
                                   'Create', self.on_shortcut)
        self.about = NoticeCard(self, theme, '%s %s' % (APP_NAME, APP_VERSION),
                                APP_AUTHOR)
        self.cards = (self.ontop, self.dark, self.shortcut, self.about)

        # 0.1.x 부터 기본이 항상 위였다.
        self.ontop.SetValue(settings.get('on_top', True))
        self.dark.SetValue(settings.get('theme', 'dark') == 'dark')

        self.groups = []
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(MARGIN)
        for title, cards in (('Window', (self.ontop, self.dark)),
                             ('Shortcut', (self.shortcut,)),
                             ('About', (self.about,))):
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

    def on_shortcut(self):
        try:
            makeshortcut.create(ShortCut.get_user_programs_path(APP_NAME))
        except Exception:
            self.shortcut.set_label('Start menu', 'Could not create the shortcut')
            self.shortcut.set_tone('warn')
            return
        self.shortcut.set_label('Start menu', 'Shortcut created')
        self.shortcut.set_tone('done')

    def apply_theme(self, theme):
        self.SetBackgroundColour(wx.Colour(theme['bg']))
        for label in self.groups:
            label.SetForegroundColour(wx.Colour(theme['text']))
        for card in self.cards:
            card.set_theme(theme)
        self.Refresh()
