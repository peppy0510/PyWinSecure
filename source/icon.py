# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import os
import sys
import wx


from wininstance import get_current_real_cwq


class FrameIcon():

    icon_path = os.path.join('assets', 'icon', 'icon.ico')

    def __init__(self):

        icon = wx.Icon()

        if hasattr(sys, '_MEIPASS'):
            self.icon_path = os.path.join(sys._MEIPASS, self.icon_path)
        else:
            cwd = os.path.dirname(get_current_real_cwq())
            self.icon_path = os.path.join(cwd, self.icon_path)

        icon.CopyFromBitmap(wx.Bitmap(self.icon_path, wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)
