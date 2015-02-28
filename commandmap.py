from inspect import getargspec
from collections import namedtuple
import os
from glob import glob
import sys

Command = namedtuple('Command', ['func', 'arity'])


class CommandMap(object):
    def __init__(self):
        self.commands = {}

    @staticmethod
    def arity(func):
        def _len(thing):
            if thing is None:
                return 0
            else:
                return len(thing)
        return sum(map(_len, getargspec(func)))

    def map_command(self, trigger_string, function):
        tf = Command(function, self.arity(function))
        self.commands[trigger_string] = tf

    def get_command(self, trigger_string):
        return self.commands.get(trigger_string)

    def load_plugins(self):
        plugin_path = os.path.join(os.getcwd(), 'plugins')
        sys.path.append(plugin_path)
        plugin_files = glob(os.path.join(plugin_path, '*_plugin.py'))
        print "Loading plugins from {}".format(plugin_path)
        for plugin_file in plugin_files:
            path, name = os.path.split(plugin_file)
            name = name.split('.', 1)[0]
            plugin = __import__(name)
            # TODO: confirm plugin has required attributes
            print "Initializing: {}".format(name)
            plugin.init_plugin(self)