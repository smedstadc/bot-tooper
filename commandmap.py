from inspect import getargspec
from collections import namedtuple
import os
from glob import glob
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('commandmap')

Command = namedtuple('Command', ['func', 'arity'])


class CommandMap(object):
    def __init__(self):
        self.commands = {}
        self.excluded_plugins = []

    @staticmethod
    def arity(func):
        """Returns the number of arguments a given function expects."""
        def _len(thing):
            if thing is None:
                return 0
            else:
                return len(thing)
        return sum(map(_len, getargspec(func)))

    def map_command(self, trigger_string, function):
        """Map a trigger string to a plugin function."""
        tf = Command(function, self.arity(function))
        if not self.commands.get(trigger_string):
            self.commands[trigger_string] = tf
        else:
            logger.debug("Failure: {} is already defined.")

    def get_command(self, trigger_string):
        """Fetch a Command tuple for a given trigger."""
        return self.commands.get(trigger_string)

    def load_plugins(self, exclude=('')):
        """Imports each file matching ./plugins/*_plugin.py and calls it's init_plugin() function, passing self."""
        plugin_path = os.path.join(os.getcwd(), 'plugins')
        sys.path.append(plugin_path)
        plugin_files = glob(os.path.join(plugin_path, '*_plugin.py'))
        logger.debug("Loading plugins from {}".format(plugin_path))
        for plugin_file in plugin_files:
            path, name = os.path.split(plugin_file)
            name = name.split('.', 1)[0]
            if name not in exclude:
                plugin = __import__(name)
                # TODO: confirm plugin has required attributes
                try:
                    plugin.init_plugin(self)
                    logger.debug("Initialized {}".format(name))
                except AttributeError as e:
                    logger.debug("Failed to initialize {} because it does not define init_plugin()".format(name))
            else:
                logger.debug("Skipped {} because it is in the exclude list.".format(name))

    def triggers(self):
        return self.commands.keys()

if __name__ == "__main__":
    c = CommandMap()
    c.load_plugins()