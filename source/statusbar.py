# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import wx


class StatusPanel(wx.StatusBar):

    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)
        self.parent = parent
        self.SetFieldsCount(1)


class StatusBar():

    def __init__(self):
        self.StatusBar = StatusPanel(self)
        self.SetStatusBar(self.StatusBar)
