# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import os

from win32com.client import Dispatch


def create_shortcut(path, target_path='', arguments='', working_directory='', icon=''):
    ext = os.path.splitext(path)[-1][1:].lower()
    if ext == 'url':
        with open(path, 'w') as file:
            file.write('[InternetShortcut]\nURL=%s' % target_path)
    else:
        shell = Dispatch('WScript.Shell')

        shortcut = shell.CreateShortCut(
            path if path.endswith('.lnk') else '.'.join([path, 'lnk']))
        # shortcut.WindowStyle = 1
        shortcut.Arguments = arguments
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = working_directory
        if icon:
            shortcut.IconLocation = icon
        shortcut.save()
    print('[ SHORTCUT CREATED ] [ %s ]' % path)


def create_desktop_ini(directory, icon_resource, folder_type='Generic'):
    with open(os.path.join(directory, 'desktop.ini'), 'w') as file:
        file.write('\n'.join([
            '[.ShellClassInfo]', 'IconResource=%s,0' % icon_resource,
            '[ViewState]', 'Mode=', 'Vid=', 'FolderType=%s' % folder_type]))


def main():
    # C:\Users\username\AppData\Roaming\Microsoft\Windows\Start Menu
    # C:\Users\username\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
    shortcut_name = 'secure.pyw'
    target_name = 'secure.pyw'
    cwd = os.path.dirname(__file__)
    home = os.path.expanduser('~')
    icon = os.path.join(cwd, 'assets', 'icon.ico')
    startmenu = os.path.join(home, 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu')
    python = 'pythonw.exe'
    create_shortcut(
        os.path.join(startmenu, shortcut_name),
        python, os.path.join(cwd, target_name), cwd, icon)

    create_desktop_ini(cwd, icon)


if __name__ == '__main__':
    main()
