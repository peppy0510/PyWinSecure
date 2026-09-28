# encoding: utf-8


# makebuild.py 가 이 줄들을 읽는다. 버전은 utilities.APP_VERSION 과 함께 올린다.
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

    # 없으면 종료할 때 파이썬이 스트림을 못 비워 exit code 120 으로 끝난다.
    def flush(self, *args, **kwargs):
        pass


# pythonw 로 띄우면 표준 스트림이 셋 다 None 이라 print 한 줄에 죽는다.
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
