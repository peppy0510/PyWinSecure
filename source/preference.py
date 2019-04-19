# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import json
import os
import sys


class Preference():

    def __init__(self):
        self.preference_dir = os.path.join(
            os.path.expanduser('~'), 'AppData', 'Local', self.__appname__)
        self.preference_path = os.path.join(self.preference_dir, 'settings.json')
        print(self.preference_dir)

    def get_preference_path(self):
        return os.path.join(os.path.expanduser('~'),
                            'AppData', 'Local', self.__appname__)

    def get_preference(self, key):
        self.get_preference_path()
        if os.path.exists(self.preference_path):
            with open(self.preference_path, 'r') as file:
                content = file.read()
                preference = json.loads(content)
                return preference.get(key)

    def set_preference(self, key, value):
        if not os.path.exists(self.preference_dir):
            try:
                os.mkdir(self.preference_dir)
            except Exception:
                return

        preference = None
        if os.path.exists(self.preference_path):
            with open(self.preference_path, 'r') as file:
                content = file.read()
                preference = json.loads(content)

        if not preference:
            preference = {}

        preference.update({key: value})
        preference.update({'version': self.__version__})
        content = json.dumps(preference)
        with open(self.preference_path, 'w') as file:
            file.write(content)
