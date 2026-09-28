# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import attributes
import os
import threading
import wx

from controls import ButtonCard
from controls import ButtonsCard
from folderlist import FolderList
from utilities import Canvas
from utilities import get_font


MARGIN = 16
TITLE_INSET = 3
TITLE_GAP = 8
CARD_GAP = 4

EMPTY_IDLE = 'Drop folders here'
ADD_HINT = 'Or drop folders onto the list above'
ADD_NO_FOLDER = 'Only folders can be added'
ALL_HINT = 'Click an eye to hide or show one folder'

# attrib 한 번이 수십 ms 라 몇 번에 한 번만 알려도 막대처럼 움직인다.
PROGRESS_STEP = 10


def format_count(count):
    return '{:,}'.format(count)


def get_key(path):
    return os.path.normcase(os.path.normpath(path))


class FolderDrop(wx.FileDropTarget):

    def __init__(self, box):
        super().__init__()
        self.box = box

    def OnEnter(self, x, y, result):
        if self.box.busy:
            return wx.DragNone
        self.box.files.set_hot(True)
        return wx.DragCopy

    def OnDragOver(self, x, y, result):
        return wx.DragNone if self.box.busy else wx.DragCopy

    def OnLeave(self):
        self.box.files.set_hot(False)

    def OnDropFiles(self, x, y, paths):
        self.box.files.set_hot(False)
        self.box.add_folders(paths)
        return True


class SecureBox(Canvas):

    def __init__(self, parent, theme, settings, on_change):
        super().__init__(parent, theme)
        self.on_change = on_change
        self.busy = False
        self.states = []
        # 빠진 USB·끊긴 공유 폴더도 목록에서 지우지 않는다. 돌릴 때만 거른다.
        self.folders = list(settings.get('folders', []))

        self.files = FolderList(self, theme, EMPTY_IDLE, self.on_toggle, self.on_remove)
        self.add = ButtonCard(self, theme, 'Add folder', ADD_HINT,
                              'Choose', self.on_choose)
        self.all = ButtonsCard(self, theme, 'All folders', ALL_HINT,
                               (('Show', self.on_show_all),
                                ('Hide', self.on_hide_all)))
        self.cards = (self.add, self.all)

        # 목록 칸만이 아니라 페이지 어디에 놓아도 받는다.
        for window in (self, self.files):
            window.SetDropTarget(FolderDrop(self))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(MARGIN)
        self.titles = []
        self.files_count = self.add_title(sizer, 'Folders', True)
        sizer.Add(self.files, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, MARGIN)
        sizer.AddSpacer(CARD_GAP)
        self.add_card(sizer, self.add)
        sizer.AddSpacer(CARD_GAP)
        self.add_card(sizer, self.all)
        sizer.AddSpacer(MARGIN)
        self.SetSizer(sizer)

        self.apply_theme(theme)
        self.load_folders()

    def add_title(self, sizer, text, counted=False):
        row = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, label=text)
        label.SetFont(get_font(10, bold=True))
        row.Add(label, 0, wx.LEFT, MARGIN + TITLE_INSET)
        self.titles.append(label)

        count = None
        if counted:
            count = wx.StaticText(self, label='')
            count.SetFont(get_font(9))
            row.AddStretchSpacer()
            # 굵기가 달라 위를 맞추면 어긋난다. 밑줄을 맞춘다.
            row.Add(count, 0, wx.RIGHT | wx.ALIGN_BOTTOM, MARGIN + TITLE_INSET)

        sizer.Add(row, 0, wx.EXPAND)
        sizer.AddSpacer(TITLE_GAP)
        return count

    def add_card(self, sizer, card):
        sizer.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, MARGIN)

    def get_item(self, path):
        name = os.path.basename(os.path.normpath(path))
        # 드라이브 루트는 이름이 비어 경로 자체를 이름으로 쓴다.
        if not name:
            return (path, '')
        return (name, os.path.dirname(os.path.normpath(path)))

    def load_folders(self):
        self.states = [attributes.get_state(path) for path in self.folders]
        self.files.set_items([self.get_item(path) for path in self.folders], self.states)

        count = len(self.folders)
        label = ''
        if count:
            label = '%s folder%s' % (format_count(count), '' if count == 1 else 's')
            hidden = self.states.count('hidden')
            if hidden:
                label += ' · %s hidden' % format_count(hidden)
        self.files_count.SetLabel(label)
        self.Layout()
        self.sync_actions()

    def sync_actions(self):
        self.all.set_enabled(not self.busy and bool(self.folders))
        self.add.set_enabled(not self.busy)

    def set_status(self, description, tone='dim'):
        self.all.set_label('All folders', description)
        self.all.set_tone(tone)

    def add_folders(self, paths):
        if self.busy:
            return
        known = [get_key(path) for path in self.folders]
        added = skipped = 0
        for path in paths:
            if not os.path.isdir(path):
                skipped += 1
                continue
            if get_key(path) in known:
                continue
            known.append(get_key(path))
            self.folders.append(path)
            added += 1

        if skipped and not added:
            self.add.set_label('Add folder', ADD_NO_FOLDER)
            self.add.set_tone('warn')
        else:
            self.add.set_label('Add folder', ADD_HINT)
            self.add.set_tone('dim')
        if not added:
            return
        self.set_status(ALL_HINT)
        self.load_folders()
        self.on_change()

    def on_choose(self):
        dialog = wx.DirDialog(self, 'Choose a folder', '',
                              wx.DD_DIR_MUST_EXIST | wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.add_folders([dialog.GetPath()])
        dialog.Destroy()

    def on_remove(self, index):
        if self.busy or not 0 <= index < len(self.folders):
            return
        self.folders.pop(index)
        self.set_status(ALL_HINT)
        self.load_folders()
        self.on_change()

    def on_toggle(self, index):
        # 반만 숨겨진 폴더는 숨기는 쪽으로 마저 끝낸다.
        hide = self.states[index] != 'hidden'
        self.start(hide, [index])

    def on_hide_all(self):
        self.start(True, range(len(self.folders)))

    def on_show_all(self):
        self.start(False, range(len(self.folders)))

    def start(self, hide, indexes):
        if self.busy:
            return
        indexes = [index for index in indexes if os.path.isdir(self.folders[index])]
        if not indexes:
            self.set_status('None of these folders can be reached', 'warn')
            return
        self.busy = True
        self.running = hide
        self.sync_actions()
        self.files.set_enabled(False, indexes)
        self.set_status('Reading the folders…')
        folders = [self.folders[index] for index in indexes]
        thread = threading.Thread(target=self.run, args=(hide, folders))
        thread.daemon = True
        thread.start()

    def run(self, hide, folders):
        def on_progress(done, total):
            if done % PROGRESS_STEP == 0 or done == total:
                wx.CallAfter(self.take_progress, hide, done, total)

        try:
            params = attributes.get_pathparams(folders)
            wx.CallAfter(self.take_progress, hide, 0, len(params))
            result = (len(folders), len(params), attributes.apply(hide, params, on_progress))
        except Exception:
            result = None
        wx.CallAfter(self.take_done, hide, result)

    def take_progress(self, hide, done, total):
        if not self or not self.busy:
            return
        self.set_status('%s · step %s of %s' % ('Hiding' if hide else 'Showing',
                                                format_count(done), format_count(total)))

    def take_done(self, hide, result):
        if not self:
            return
        self.busy = False
        self.files.set_enabled(True)
        self.load_folders()

        if result is None:
            self.set_status('Could not read the folders', 'warn')
            return

        # attrib 을 부른 횟수라 항목 수와 다르다. 실패한 몫만 숫자로 말한다.
        count, total, failed = result
        if failed:
            self.set_status('%s of %s steps failed' % (format_count(failed),
                                                       format_count(total)), 'warn')
            return
        self.set_status('%s %s folder%s' % ('Hid' if hide else 'Showed',
                                            format_count(count),
                                            '' if count == 1 else 's'), 'done')

    def hold_close(self):
        self.set_status('Wait until this finishes to close', 'warn')

    def store(self):
        return {'folders': list(self.folders)}

    def apply_theme(self, theme):
        self.set_theme(theme)
        self.SetBackgroundColour(wx.Colour(theme['bg']))
        for label in self.titles:
            label.SetForegroundColour(wx.Colour(theme['text']))
        self.files_count.SetForegroundColour(wx.Colour(theme['dim']))
        for card in self.cards:
            card.set_theme(theme)
        self.files.set_theme(theme)
        self.Refresh()
