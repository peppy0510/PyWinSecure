# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import os
import sys

from shortcut import ShortCut
from utilities import APP_NAME


def get_pythonw():
    path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    return path if os.path.exists(path) else sys.executable


START_MENU = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Microsoft', 'Windows',
                          'Start Menu')


def get_start_menu_paths():
    # Create puts it in Programs; PyWinClock used to put it in the Start menu root
    return (os.path.join(START_MENU, 'Programs', f'{APP_NAME}.lnk'),
            os.path.join(START_MENU, f'{APP_NAME}.lnk'))


def has_start_menu():
    return any(os.path.exists(path) for path in get_start_menu_paths())


def remove_start_menu():
    for path in get_start_menu_paths():
        if os.path.exists(path):
            os.remove(path)


def create(path):
    source = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(source)
    icon = os.path.join(root, 'assets', 'icon', 'icon.ico')
    script = os.path.join(source, 'main.pyw')

    ShortCut.create(
        path,
        target_path=get_pythonw(),
        arguments=f'"{script}"',
        working_directory=source,
        icon=icon if os.path.exists(icon) else '')
    return path


def main():
    print(f'[ SHORTCUT CREATED ] [ {create(ShortCut.get_user_programs_path(APP_NAME))} ]')


if __name__ == '__main__':
    main()
