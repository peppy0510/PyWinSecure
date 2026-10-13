# encoding: utf-8


__appname__ = 'PyWinSecure'
__version__ = '0.2.0'
__author__ = 'Taehong Kim'
__email__ = 'peppy0510@hotmail.com'
__license__ = ''
__doc__ = '''
'''


import sys

from wininstance import kill_existing_instances


class stderr:
    def write(self, *args, **kwargs):
        pass

    # without flush, pythonw exits with code 120
    def flush(self, *args, **kwargs):
        pass


# pythonw leaves the standard streams as None
if not sys.stderr:
    sys.stderr = stderr()
if not sys.stdout:
    sys.stdout = stderr()


def main():
    from mainapp import launch_mainapp
    launch_mainapp()


if __name__ == '__main__':
    kill_existing_instances()
    main()
