# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import wx


class MenuBar():

    def __init__(self):

        def make_menuitem(label, menu, bind=None, kind=wx.ITEM_NORMAL):
            item = wx.MenuItem(menu, wx.ID_ANY, label, wx.EmptyString, kind=kind)
            menu.Append(item)
            if bind is not None:
                self.Bind(wx.EVT_MENU, bind, item)
            return item

        MenuBar = wx.MenuBar()

        FileMenu = wx.Menu()
        make_menuitem('Exit', FileMenu, self.OnClose)

        MenuBar.Append(FileMenu, '&File')
        SettingsMenu = wx.Menu()
        self.AlwaysOnTopMenuItem = make_menuitem(
            'Always on top', SettingsMenu, self.OnAlwaysOnTopToggle, kind=wx.ITEM_CHECK)
        MenuBar.Append(SettingsMenu, '&Settings')

        HelpMenu = wx.Menu()
        self.HelpMenuAbout = make_menuitem('About', HelpMenu, self.OnHelpMenuAbout)
        MenuBar.Append(HelpMenu, '&Help')
        self.SetMenuBar(MenuBar)

        # self.SetAlwaysOnTopValue()

    def OnAlwaysOnTopToggle(self, event=None):
        self.SetAlwaysOnTopValue(event.IsChecked())

    def SetAlwaysOnTopValue(self, value):
        if value:
            self.SetAlwaysOnTopEnabled()
        else:
            self.SetAlwaysOnTopDisabled()

    def SetAlwaysOnTopEnabled(self):
        self.AlwaysOnTopMenuItem.Check(True)
        # self.AlwaysOnTopToggle.SetValue(True)
        # style = self.GetWindowStyle()
        self.SetWindowStyleFlag(self.defaultStyle | wx.STAY_ON_TOP)
        # self.SetWindowStyle(style | wx.STAY_ON_TOP)
        self.Update()

    def SetAlwaysOnTopDisabled(self):
        self.AlwaysOnTopMenuItem.Check(False)
        # self.AlwaysOnTopToggle.SetValue(False)
        # style = self.GetWindowStyle()
        self.SetWindowStyleFlag(self.defaultStyle)
        # self.SetWindowStyle(style ^ wx.STAY_ON_TOP)
        self.Update()

    def OnHelpMenuAbout(self, event):

        width, height = (250, 135)
        x, y, w, h = self.GetScreenRect()
        x, y = (x + (w - width) / 2, y + (h - height) / 2)
        self.Dialog = wx.Dialog(self)
        self.Dialog.SetRect((x, y, width, height))
        self.Dialog.SetTitle('About')

        margin = 12
        width, height = self.Dialog.GetClientSize()
        message = '{} {}'.format(self.__appname__, self.__version__)
        wx.StaticText(self.Dialog, label=message, pos=(margin, margin))
        message = 'Author: {}'.format(self.__author__)
        wx.StaticText(self.Dialog, label=message, pos=(margin, margin + 18))
        message = 'Email: {}'.format(self.__email__)
        wx.StaticText(self.Dialog, label=message, pos=(margin, margin + 18 * 2))

        # wx.BORDER_NONE
        self.Dialog.CloseButton = wx.Button(self.Dialog, label=u'Close')
        self.Dialog.CloseButton.SetRect((width - (78 + margin) * 1, margin + 60, 78, 24))
        self.Dialog.CloseButton.Bind(wx.EVT_BUTTON, lambda event: self.Dialog.Destroy())

        x, y = self.Dialog.CloseButton.GetPosition()
        self.Dialog.SetClientSize((self.Dialog.GetClientSize().x, y + 35))
        self.Dialog.ShowModal()
