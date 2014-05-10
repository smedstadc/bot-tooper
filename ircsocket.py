""" ircsocket.py

    A simple container for a socket and a few helpful functions for talking to an IRC server
"""

from socket import *


class IrcSocket():
    def __init__(self):
        self.names = {}
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connect(self, address):
        self.sock.connect(address)

    def disconnect(self):
        self.sock.close()

    def _command(self, command_string):
        """Encodes a message to be sent to the IRC server."""
        print('SENT: ' + repr(command_string))
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

    def notice(self, channel, message):
        """Sends a NOTICE to a channel."""
        command_string = 'NOTICE {} :{}'.format(channel, message)
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
            print('WARN: ' + 'Attempted to remove {}: {}, but it didn\'t exist.'.format(channel, nick))

    def set_names(self, channel, names):
        """Update the set of names for a channel upon receiving a /NAMES list from the server."""
        temp_names = []
        for name in names.strip().split():
            temp_names.append(name.strip('@').strip('~'))
        self.names[channel] = set(temp_names)

    def nick_changed(self, old, new):
        """Update names if a user is observed changing their nick in one of the bot's channels."""
        # In IRC names have channels, rather than the opposite. This works for now, but should be updated at some point.
        for key in self.names.keys():
            if old in self.names[key]:
                self.names[key].remove(old)
                self.names[key].add(new)