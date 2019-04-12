# encoding: utf-8

import glob
import os
import psutil
import subprocess
import threading
import wx


__version__ = '0.0.1'
__author__ = 'Taehong Kim'
__email__ = 'peppy0510@hotmail.com'
__license__ = ''
__doc__ = '''
'''


def kill_existing_instances():
    pid = int(os.getpid())
    cwd = os.path.split(__file__)[0]
    # basename = os.path.basename(os.getcwd())
    for p in psutil.process_iter():
        try:
            p.cwd()
        except Exception:
            continue
        if p.pid != pid and p.cwd() == cwd and p.name().lower() in ('python.exe', 'pythonw.exe',):
            # print(basename)
            p.terminate()


# threadListLock = threading.Lock()


class ListBoxListDnD(wx.FileDropTarget):

    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
        self.dropTimer = 0
        self.onClient = False
        self.itemDrag = False
        self.importing = False
        self.insertItemIdx = None

    def OnDropFiles(self, x, y, inpaths):

        self.parent.init_debug()
        self.parent.debug_line('[ IMPORT ] [ STARTED ]')

        for i in range(len(inpaths) - 1, -1, -1):
            path = inpaths[i]
            if not os.path.isdir(path):
                inpaths.pop(i)
                continue
            self.parent.debug_line('[ IMPORT ] [ %s ]' % (path))

        self.parent.FuncPanel.set_rootdirs(inpaths)

        self.parent.debug_line('[ IMPORT ] [ FINISHED ]')
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

    def __init__(self, parent, splitter):
        wx.Panel.__init__(self, parent=splitter)
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
            self.parent.debug_line('[ NO DIRECTORIES HAS BEEN SET ]')
            return

        self.parent.debug_line('[ SHOW ] [ STARTED ]')

        for v in pathparams:
            command = 'attrib -s -h "%s"' % (v)
            self.parent.debug_line('[ SHOW ] [ %s ]' % (v))
            proc = SubprocessThread(command)
            # myclass = MyClass()
            proc.start()
            proc.join()
            # proc = subprocess.Popen(command, stdout=subprocess.PIPE)
            # proc.communicate()

        self.parent.debug_line('[ SHOW ] [ FINISHED ]')

    def OnHideButton(self, event):
        self.parent.init_debug()
        pathparams = self.get_pathparams()

        if not pathparams:
            self.parent.debug_line('[ NO DIRECTORIES HAS BEEN SET ]')
            return

        self.parent.debug_line('[ HIDE ] [ STARTED ]')

        for v in pathparams:
            command = 'attrib +s +h "%s"' % (v)
            self.parent.debug_line('[ HIDE ] [ %s ]' % (v))
            proc = SubprocessThread(command)
            proc.start()
            proc.join()
            # proc = subprocess.Popen(command, stdout=subprocess.PIPE)
            # proc.communicate()

        self.parent.debug_line('[ HIDE ] [ FINISHED ]')

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


class DebugPanel(wx.Panel):

    def __init__(self, parent, splitter):
        wx.Panel.__init__(self, parent=splitter,
                          style=wx.CLIP_CHILDREN | wx.TAB_TRAVERSAL | wx.NO_BORDER | wx.FRAME_SHAPED)
        self.SetBackgroundColour((180, 220, 220))
        self.parent = parent

        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.SUNKEN_BORDER)
        fgsizer = wx.FlexGridSizer(1, 0, 0, 0)
        fgsizer.AddGrowableCol(0)
        fgsizer.AddGrowableRow(0)
        fgsizer.SetFlexibleDirection(wx.BOTH)
        fgsizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        fgsizer.Add(self.text, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        self.SetSizer(fgsizer)

    def AppendText(self, text):
        self.text.AppendText(text + '\n')
        self.text.Refresh()


class MainFrame(wx.Frame):

    def __init__(self, parent=None):
        self.defaultStyle = wx.CLIP_CHILDREN | wx.FRAME_SHAPED | wx.MINIMIZE_BOX |\
            wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CLOSE_BOX | wx.CAPTION |\
            wx.RESIZE_BORDER | wx.TAB_TRAVERSAL | wx.BORDER_DEFAULT
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                          size=wx.Size(600, 250), style=self.defaultStyle)

        self.SetTitle('WinSecure')
        self.SetMinSize((600, 250))
        self.SetMaxSize((-1, -1))
        self.SetWindowStyle(self.defaultStyle | wx.STAY_ON_TOP)
        w, h = self.GetSize()
        width, height = wx.GetDisplaySize()
        self.SetPosition(((width - w) / 2, (height - h) / 2))
        self.Splitter = wx.SplitterWindow(self)
        self.FuncPanel = FuncPanel(self, self.Splitter)
        self.DebugPanel = DebugPanel(self, self.Splitter)
        self.Splitter.SplitHorizontally(
            self.FuncPanel, self.DebugPanel, sashPosition=40)
        self.Splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSashSize)
        self.Splitter.SetSashGravity(0.0)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.Splitter, 1, wx.EXPAND)

        self.FileDrop = ListBoxListDnD(self)
        self.DebugPanel.SetDropTarget(self.FileDrop)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.SetSizer(sizer)
        self.Show()

    def init_debug(self):
        self.DebugPanel.text.SetValue('')
        self.DebugPanel.text.Refresh()

    def debug_line(self, text):
        self.DebugPanel.AppendText(text)

    def OnSashSize(self, event):
        self.Splitter.SetSashPosition(40)
        self.Splitter.SetMinimumPaneSize(40)

    def OnClose(self, event=None):
        wx.CallAfter(self.Destroy)
        print('OnClose')


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
    # import sys  # noqa
    # from io import TextIOWrapper
    # sys.stdout = TextIOWrapper(sys.stdout.buffer,
    #                            encoding='utf-8', errors='replace')
    kill_existing_instances()
    main()
