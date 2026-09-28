# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

Puts a Start menu link that runs source/main.pyw through pythonw.exe.
'''


import os
import sys

from shortcut import ShortCut
from utilities import APP_NAME


def get_pythonw():
    path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    return path if os.path.exists(path) else sys.executable


def create(path):
    source = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(source)
    icon = os.path.join(root, 'assets', 'icon', 'icon.ico')

    ShortCut.create(
        path,
        target_path=get_pythonw(),
        arguments='"%s"' % os.path.join(source, 'main.pyw'),
        working_directory=source,
        icon=icon if os.path.exists(icon) else '')
    return path


def main():
    print('[ SHORTCUT CREATED ] [ {} ]'.format(
        create(ShortCut.get_user_programs_path(APP_NAME))))


if __name__ == '__main__':
    main()
