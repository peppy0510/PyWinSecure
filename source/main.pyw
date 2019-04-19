# encoding: utf-8


__appname__ = 'PyWinSecure'
__version__ = '0.1.1'
__author__ = 'Taehong Kim'
__email__ = 'peppy0510@hotmail.com'
__license__ = ''
__doc__ = '''
'''


import glob
import os
import subprocess
import sys
import threading
import wx

from icon import FrameIcon
from menubar import MenuBar
from preference import Preference
from statusbar import StatusBar
from wininstance import kill_existing_instances
from winscreens import get_screens
# from wininstance import get_current_real_cwq
# threadListLock = threading.Lock()


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
            self.parent.debug_line('IMPORT: {}'.format(path))
        self.parent.FuncPanel.set_rootdirs(inpaths)
        self.parent.set_status(' IMPORT FINISHED')
        return 0


class SubprocessThread(threading.Thread):

    def __init__(self, command):
        self.command = command
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

    def run(self):
        p = subprocess.Popen(self.command,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        self.stdout, self.stderr = p.communicate()


class FuncPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.rootdirs = []
        # self.Tool = FuncPanelTool(self)
        # self.Bind(wx.EVT_SIZE, self.OnSize)

        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        self.ShowButton = wx.Button(self, id=wx.ID_ANY, label="Show", pos=wx.DefaultPosition,
                                    size=wx.DefaultSize, style=0, validator=wx.DefaultValidator,
                                    name=wx.ButtonNameStr)

        self.ShowButton.Bind(wx.EVT_BUTTON, self.OnShowButton)
        self.ShowButton.SetFont(font)
        self.ShowButton.SetRect((4, 5, 120, 35))

        self.HideButton = wx.Button(self, id=wx.ID_ANY, label="Hide", pos=wx.DefaultPosition,
                                    size=wx.DefaultSize, style=0, validator=wx.DefaultValidator,
                                    name=wx.ButtonNameStr)
        self.HideButton.Bind(wx.EVT_BUTTON, self.OnHideButton)
        self.HideButton.SetFont(font)

        self.HideButton.SetRect((127, 5, 120, 35))

    def OnShowButton(self, event):
        self.parent.init_debug()
        pathparams = self.get_pathparams()

        if not pathparams:
            self.parent.set_status('NO DIRECTORIES HAS BEEN SET')
            return
        self.parent.set_status('SHOW ...')
        for v in pathparams:
            command = 'attrib -s -h "%s"' % (v)
            self.parent.debug_line('{}'.format(v))
            proc = SubprocessThread(command)
            # myclass = MyClass()
            proc.start()
            proc.join()
            # proc = subprocess.Popen(command, stdout=subprocess.PIPE)
            # proc.communicate()
        self.parent.set_status('SHOW FINISHED')

    def OnHideButton(self, event):
        self.parent.init_debug()
        pathparams = self.get_pathparams()

        if not pathparams:
            self.parent.set_status('NO DIRECTORIES HAS BEEN SET')
            return
        self.parent.set_status('HIDE ...')

        for v in pathparams:
            command = 'attrib +s +h "%s"' % (v)
            self.parent.debug_line('{}'.format(v))
            proc = SubprocessThread(command)
            proc.start()
            proc.join()
            # proc = subprocess.Popen(command, stdout=subprocess.PIPE)
            # proc.communicate()
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
        # self.SetMargins(left=5, top=50)
        # wx.CURSOR_ARROWWAIT | wx.CURSOR_WAIT


class MainFrame(wx.Frame, Preference, FrameIcon, MenuBar, StatusBar):

    __appname__ = __appname__
    __version__ = __version__
    __author__ = __author__
    __email__ = __email__

    def __init__(self, parent=None):
        self.defaultStyle = wx.CLIP_CHILDREN | wx.FRAME_SHAPED | wx.MINIMIZE_BOX |\
            wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CLOSE_BOX | wx.CAPTION |\
            wx.RESIZE_BORDER | wx.TAB_TRAVERSAL | wx.BORDER_DEFAULT
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                          size=wx.Size(300, 300), style=self.defaultStyle)
        # 268
        Preference.__init__(self)
        FrameIcon.__init__(self)
        MenuBar.__init__(self)
        StatusBar.__init__(self)

        self.SetTitle(self.__appname__)
        self.SetMinSize((300, 300))
        self.SetMaxSize((-1, -1))
        # self.SetWindowStyle(self.defaultStyle | wx.STAY_ON_TOP)
        self.SetWindowStyle(self.defaultStyle)
        w, h = self.GetSize()
        width, height = wx.GetDisplaySize()
        self.SetPosition(((width - w) / 2, (height - h) / 2))
        self.FuncPanel = FuncPanel(self)
        self.DebugPanel = DebugPanel(self)
        self.FileDrop = ListBoxListDnD(self)
        self.DebugPanel.SetDropTarget(self.FileDrop)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnResize)

        size = self.get_preference('size')
        position = self.get_preference('position')
        if size and position:
            x, y = position
            width, height = size
            margin = 50
            screens = get_screens()
            finish_x = min([v.finish.x for v in screens])
            finish_y = min([v.finish.y for v in screens])
            if x + margin < finish_x and y + margin < finish_y:
                self.SetSize(size)
                self.SetPosition(position)        # print('Enabled', style)

        alwaysontop = self.get_preference('alwaysontop')
        alwaysontop = True if alwaysontop is None else alwaysontop
        self.SetAlwaysOnTopValue(alwaysontop)
        self.Show()

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
        # self.StatusBar.SetSize(width, 30)
        # self.StatusBar.SetStatusWidths([width])

    def OnClose(self, event=None):
        # print(self.GetScreenPosition())
        self.set_preference('size', list(self.GetClientSize()))
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
