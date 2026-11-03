# encoding: utf-8


__appname__ = 'PyWinSecure'
__version__ = '0.3.0'
__author__ = 'Taehong Kim'
__email__ = 'peppy0510@hotmail.com'
__license__ = ''
__doc__ = '''
'''


import vcruntime  # noqa # first: stops before wx when the C++ runtime is missing

import psutil
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


def wait_for_previous():
    # an update restarts the app; the new copy waits for the old one to save and go
    if '--after' not in sys.argv:
        return
    try:
        pid = int(sys.argv[sys.argv.index('--after') + 1])
        psutil.Process(pid).wait(10)
    except (ValueError, IndexError, psutil.Error):
        pass


def main():
    from mainapp import launch_mainapp
    launch_mainapp()


if __name__ == '__main__':
    wait_for_previous()
    kill_existing_instances()
    main()
