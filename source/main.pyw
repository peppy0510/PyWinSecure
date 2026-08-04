# encoding: utf-8


__appname__ = 'PyWinSecure'
__version__ = '0.1.3'
__author__ = 'Taehong Kim'
__email__ = 'peppy0510@hotmail.com'
__license__ = ''
__doc__ = '''
'''


import glob
import os
import subprocess
import wx

from icon import FrameIcon
from menubar import MenuBar
from preference import Preference
from statusbar import StatusBar
from wininstance import kill_existing_instances
from winscreens import get_screens


# 기억된 위치가 이만큼도 화면에 안 걸치면 사라진 모니터로 본다.
MIN_VISIBLE_WIDTH = 120
MIN_VISIBLE_HEIGHT = 32


class ListBoxListDnD(wx.FileDropTarget):

    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent

    def OnDropFiles(self, x, y, inpaths):
        self.parent.init_debug()
        self.parent.set_status(' IMPORT ...')
        for i in range(len(inpaths) - 1, -1, -1):
            path = inpaths[i]
            if not os.path.isdir(path):
                inpaths.pop(i)
                continue
            self.parent.debug_line('{}'.format(path))
        self.parent.FuncPanel.set_rootdirs(inpaths)
        self.parent.set_status(' IMPORT FINISHED')
        return 0


class FuncPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.rootdirs = []

        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        self.ShowButton = wx.Button(self, id=wx.ID_ANY, label='Show')
        self.ShowButton.SetFont(font)
        self.ShowButton.SetRect((4, 5, 120, 35))
        self.ShowButton.Bind(wx.EVT_BUTTON, self.OnShowButton)

        self.HideButton = wx.Button(self, id=wx.ID_ANY, label='Hide')
        self.HideButton.SetFont(font)
        self.HideButton.SetRect((127, 5, 120, 35))
        self.HideButton.Bind(wx.EVT_BUTTON, self.OnHideButton)

    def subprocess(self, command):
        subprocess.call(command, shell=True)

    def OnShowButton(self, event):
        self.parent.init_debug()
        pathparams = self.get_pathparams()

        if not pathparams:
            self.parent.set_status('NO DIRECTORIES HAS BEEN SET')
            return
        self.parent.set_status('SHOW ...')

        for v in pathparams:
            command = 'attrib -s -h "{}"'.format(v)
            self.parent.debug_line('{}'.format(v))
            self.subprocess(command)
        self.parent.set_status('SHOW FINISHED')

    def OnHideButton(self, event):
        self.parent.init_debug()
        pathparams = self.get_pathparams()

        if not pathparams:
            self.parent.set_status('NO DIRECTORIES HAS BEEN SET')
            return
        self.parent.set_status('HIDE ...')

        for v in pathparams:
            command = 'attrib +s +h "{}"'.format(v)
            self.parent.debug_line('{}'.format(v))
            self.subprocess(command)
        self.parent.set_status('HIDE FINISHED')

    def set_rootdirs(self, rootdirs):
        self.rootdirs = rootdirs

    def get_pathparams(self):
        if not self.rootdirs:
            return []
        params = []
        for rootdir in self.rootdirs:
            params += [os.path.join(rootdir, '*.*')]
            for v in self.search_subpath(rootdir):
                if os.path.isdir(v):
                    params += [v, os.path.join(v, '*.*')]
        return params

    def search_subpath(self, path, pattern='*'):
        retlist = glob.glob(os.path.join(path, pattern))
        for f in os.listdir(path):
            nextlist = os.path.join(path, f)
            if os.path.isdir(nextlist):
                retlist += self.search_subpath(nextlist, pattern)
        return retlist


class DebugPanel(wx.TextCtrl):

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent=parent, style=wx.NO_BORDER | wx.TE_DONTWRAP |
                             wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NOHIDESEL | wx.CLIP_CHILDREN)
        self.SetDoubleBuffered(True)
        self.SetBackgroundColour((180, 220, 220))
        self.parent = parent
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        self.SetMargins(left=5)


class MainFrame(wx.Frame, Preference, FrameIcon, MenuBar, StatusBar):

    __appname__ = __appname__
    __version__ = __version__
    __author__ = __author__
    __email__ = __email__

    def __init__(self, parent=None):
        self.defaultStyle = wx.CLIP_CHILDREN | wx.FRAME_SHAPED | wx.MINIMIZE_BOX |\
            wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CLOSE_BOX | wx.CAPTION |\
            wx.RESIZE_BORDER | wx.TAB_TRAVERSAL | wx.BORDER_DEFAULT

        wx.Frame.__init__(self, parent, id=wx.ID_ANY)
        Preference.__init__(self)
        FrameIcon.__init__(self)
        MenuBar.__init__(self)
        StatusBar.__init__(self)

        self.SetTitle(self.__appname__)
        self.SetMinSize((268, 300))
        self.SetMaxSize((-1, -1))
        self.SetSize((350, 300))
        # self.SetWindowStyle(self.defaultStyle | wx.STAY_ON_TOP)
        self.SetWindowStyle(self.defaultStyle)
        self.set_centre_position()
        self.FuncPanel = FuncPanel(self)
        self.DebugPanel = DebugPanel(self)
        self.FileDrop = ListBoxListDnD(self)
        self.DebugPanel.SetDropTarget(self.FileDrop)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnResize)

        self.restore_geometry(self.get_preference('size'),
                              self.get_preference('position'))

        alwaysontop = self.get_preference('alwaysontop')
        alwaysontop = True if alwaysontop is None else alwaysontop
        self.SetAlwaysOnTopValue(alwaysontop)
        self.Update()
        self.Show()

    def set_centre_position(self):
        w, h = self.GetSize()
        width, height = wx.GetDisplaySize()
        self.SetPosition((int((width - w) * 0.5), int((height - h) * 0.5)))

    def is_rect_visible(self, x, y, width, height):
        # 모니터를 떼거나 배치를 바꾸면 기억된 좌표가 어느 화면에도 안 걸칠 수 있다.
        for screen in get_screens():
            shared_width = min(x + width, screen.finish.x) - max(x, screen.offset.x)
            shared_height = min(y + height, screen.finish.y) - max(y, screen.offset.y)
            if shared_width >= MIN_VISIBLE_WIDTH and shared_height >= MIN_VISIBLE_HEIGHT:
                return True
        return False

    def restore_geometry(self, size, position):
        if not size or not position or len(size) != 2 or len(position) != 2:
            return

        self.SetSize(size)
        if self.is_rect_visible(position[0], position[1], size[0], size[1]):
            self.SetPosition(position)
            return
        self.set_centre_position()

    def init_debug(self):
        self.DebugPanel.SetValue('')
        self.DebugPanel.Update()

    def debug_line(self, text):
        self.DebugPanel.AppendText('{}\n'.format(text))

    def set_status(self, text):
        self.StatusBar.SetStatusText(' {}'.format(text))

    def OnSashSize(self, event):
        self.Splitter.SetSashPosition(40)
        self.Splitter.SetMinimumPaneSize(40)

    def OnResize(self, event):
        split = 46
        width, height = self.GetClientSize()
        self.FuncPanel.SetSize(width, split)
        self.DebugPanel.SetPosition((0, split))
        self.DebugPanel.SetSize(width, height - split)

    def OnClose(self, event=None):
        # 최소화·최대화 상태의 좌표를 저장하면 다음 실행이 화면 밖에서 뜬다.
        if self.IsIconized() is False and self.IsMaximized() is False:
            # SetSize 로 되돌리는 값이라 클라이언트 크기가 아니라 창 전체 크기를 저장한다.
            self.set_preference('size', list(self.GetSize()))
            self.set_preference('position', list(self.GetScreenPosition()))
        self.set_preference('alwaysontop', self.AlwaysOnTopMenuItem.IsChecked())
        wx.CallAfter(self.Destroy)


class StartUpApp(wx.App):

    def __init__(self, parent=None, *argv, **kwargs):
        wx.App.__init__(self, parent, *argv, **kwargs)

    def FilterEvent(self, event):
        return -1

    def OnPreInit(self):
        self.MainFrame = MainFrame()

    def OnClose(self, event=None):
        pass

    def __del__(self):
        pass


def main():
    app = StartUpApp()
    app.MainLoop()


if __name__ == '__main__':
    # from io import TextIOWrapper
    # sys.stdout = TextIOWrapper(
    #     sys.stdout.buffer, encoding='utf-8', errors='replace')
    kill_existing_instances()
    main()
