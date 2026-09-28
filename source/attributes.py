# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

폴더 안쪽만 숨기고 드러낸다. 떨어뜨린 폴더 자신은 건드리지 않는다 — 그래야
숨긴 뒤에도 그 폴더를 다시 끌어다 놓아 되돌릴 수 있다.
'''


import glob
import os
import stat
import subprocess


# pythonw 에서 attrib 을 부를 때마다 콘솔 창이 번쩍인다.
CREATE_NO_WINDOW = 0x08000000

# 탐색기가 원래 숨겨 두는 파일이라 이것만으로 mixed 가 되면 안 된다.
SHELL_FILES = ('desktop.ini', 'thumbs.db')


def get_pathparams(rootdirs):
    params = []
    for rootdir in rootdirs:
        params += [os.path.join(rootdir, '*.*')]
        for v in search_subpath(rootdir):
            if os.path.isdir(v):
                params += [v, os.path.join(v, '*.*')]
    return params


def search_subpath(path, pattern='*'):
    retlist = glob.glob(os.path.join(path, pattern))
    for f in os.listdir(path):
        nextlist = os.path.join(path, f)
        if os.path.isdir(nextlist):
            retlist += search_subpath(nextlist, pattern)
    return retlist


def apply(hide, params, on_progress=None):
    '''실패한 attrib 호출 수를 돌려준다.'''
    sign = '+' if hide else '-'
    failed = 0
    for index, v in enumerate(params):
        command = 'attrib {0}s {0}h "{1}"'.format(sign, v)
        if subprocess.call(command, shell=True, creationflags=CREATE_NO_WINDOW) != 0:
            failed += 1
        if on_progress is not None:
            on_progress(index + 1, len(params))
    return failed


def get_state(rootdir):
    '''바로 아래 항목만 본다. 숨기기는 늘 통째로 하므로 첫 층이 전체를 대변한다.'''
    hidden = visible = 0
    try:
        for entry in os.scandir(rootdir):
            if entry.name.lower() in SHELL_FILES:
                continue
            attributes = entry.stat(follow_symlinks=False).st_file_attributes
            if attributes & stat.FILE_ATTRIBUTE_HIDDEN:
                hidden += 1
            else:
                visible += 1
    except Exception:
        return 'missing'
    if hidden and visible:
        return 'mixed'
    if hidden:
        return 'hidden'
    if visible:
        return 'visible'
    return ''
