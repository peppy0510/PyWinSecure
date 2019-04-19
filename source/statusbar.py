# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import wx


# class StatusPanel(wx.StatusBar):

#     def __init__(self, parent):
#         wx.StatusBar.__init__(self, parent, -1)
#         self.parent = parent
#         self.LeftText = wx.StaticText(self, -1, '')
#         self.Bind(wx.EVT_SIZE, self.OnSize)

#     def OnSize(self, event):
#         margin = 4
#         w, h = self.GetClientSize()
#         self.LeftText.SetRect((margin, margin, w / 2 - margin * 2, h - margin * 2))


# class StatusBar():

#     def __init__(self):
#         self.StatusBar = StatusPanel(self)
#         self.SetStatusBar(self.StatusBar)


class StatusPanel(wx.StatusBar):

    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)
        self.parent = parent
        # self.Text = wx.StaticText(self, -1, '')
        # self.Bind(wx.EVT_SIZE, self.OnSize)

    # def OnSize(self, event):
    #     margin = 4
    #     w, h = self.GetClientSize()
    #     self.Text.SetRect((margin, margin, w - margin * 2, h - margin * 2))
    #     # self.Text.SetRect((margin, margin, w / 2 - margin * 2, h - margin * 2))


class StatusBar():

    def __init__(self):
        self.StatusBar = StatusPanel(self)
        # print(dir(self.StatusBar))
        self.StatusBar.SetFieldsCount(1)
        # self.StatusBar.GetStatusWidth(0)
        # self.StatusBar.SetMinHeight(40)
        # self.StatusBar.SetStatusWidths([200])
        self.SetStatusBar(self.StatusBar)
