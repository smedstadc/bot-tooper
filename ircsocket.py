""" ircmanager.py
    a simple manager for multiple irc connections

    an IrcManager instance holds multiple named sockets
    in a {name: socket} dict and
"""

# TODO implement IrcSocket class that manages it's own names and channels.
# Keying off (connection_name#channel) is a messy and is prone to unexpected index/key errors.

from socket import *


class IrcSocket():
    def __init__(self):
        self.names = {}
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connect(self, address):
        self.sock.connect(address)

    def _command(self, command_string):
        """Encodes a message to be sent to the IRC server."""
        print(command_string)
        command_string += '\r\n'
        self.sock.send(command_string.encode('utf-8'))

    def join(self, channel):
        """Sends a JOIN command."""
        command_string = 'JOIN {}'.format(channel)
        self._command(command_string)

    def nick(self, nickname):
        """Sends a NICK command to the connected server."""
        command_string = 'NICK {}'.format(nickname)
        self._command(command_string)

    def user(self, user_name, host_name, server_name, real_name):
        """Sends a USER command. (Important for registering with the server upon connecting.)"""
        command_string = 'USER {} {} {} :{}'.format(user_name, host_name, server_name, real_name)
        self._command(command_string)

    def privmsg(self, recipient, message):
        """Sends a PRIVMSG to a nick or channel."""
        command_string = 'PRIVMSG {} :{}'.format(recipient, message)
        self._command(command_string)

    def passw(self, password):
        """Sends a PASS command."""
        command_string = 'PASS {}'.format(password)
        self._command(command_string)

    def oper(self, user, password):
        command_string = 'OPER {} {}'.format(user, password)
        self._command(command_string)

    def pong(self, ping_content):
        """Sends a PONG response."""
        command_string = 'PONG {}'.format(ping_content)
        self._command(command_string)

    def name_joined(self, channel, nick):
        """Adds a name to the names set for a given connection and channel."""
        try:
            self.names[channel].add(nick)
        except KeyError:
            self.names[channel] = set()
            self.names[channel].add(nick)

    def name_parted(self, channel, nick):
        """Removes a name from the names set for a given connection and channel."""
        try:
            self.names[channel].remove(nick)
        except KeyError:
            print('Attempted to remove {}: {}, but it didn\'t exist.'.format(channel, nick))

    def set_names(self, channel, names):
        """Update the set of names for a channel upon receiving a /NAMES list from the server."""
        temp_names = []
        for name in names.strip().split():
            temp_names.append(name.strip('@').strip('~'))
        self.names[channel] = set(temp_names)