# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import glob
import os
import stat
import subprocess


CREATE_NO_WINDOW = 0x08000000

# already hidden by Explorer, not a sign of a partly hidden folder
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
