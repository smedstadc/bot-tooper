""" ircmanager.py
    a simple manager for multiple irc connections

    an IrcManager instance holds multiple named sockets
    in a {name: socket} dict and
"""

# TODO implement IrcSocket class that manages it's own names and channels.
# Keying off (connection_name#channel) is a messy and is prone to unexpected index/key errors.

from socket import *


class IrcManager():
    def __init__(self):
        self.connections = {}
        self.names = {}

    def connect(self, host, port, connection_name):
        temp = socket(AF_INET, SOCK_STREAM)
        temp.connect((host, port))
        self.connections[connection_name] = temp

    def _command(self, command_string, connection_name):
        """Encodes a message to be sent to the IRC server."""
        print(command_string)
        command_string += '\r\n'
        self.connections[connection_name].send(command_string.encode('utf-8'))

    def join(self, channel, connection_name):
        """Sends a JOIN command."""
        command_string = 'JOIN {}'.format(channel)
        self._command(command_string, connection_name)

    def nick(self, nickname, connection_name):
        """Sends a NICK command to the connected server."""
        command_string = 'NICK {}'.format(nickname)
        self._command(command_string, connection_name)

    def user(self, user_name, host_name, server_name, real_name, connection_name):
        """Sends a USER command. (Important for registering with the server upon connecting.)"""
        command_string = 'USER {} {} {} :{}'.format(user_name, host_name, server_name, real_name)
        self._command(command_string, connection_name)

    def privmsg(self, recipient, message, connection_name):
        """Sends a PRIVMSG to a nick or channel."""
        command_string = 'PRIVMSG {} :{}'.format(recipient, message)
        self._command(command_string, connection_name)

    def passw(self, password, connection_name):
        """Sends a PASS command."""
        command_string = 'PASS {}'.format(password)
        self._command(command_string, connection_name)

    def pong(self, ping_content, connection_name):
        """Sends a PONG response."""
        command_string = 'PONG {}'.format(ping_content)
        self._command(command_string, connection_name)

    def join_name(self, connection_name, channel, nick):
        """Adds a name to the names set for a given connection and channel."""
        try:
            self.names[connection_name + channel].add(nick)
        except KeyError:
            self.names[connection_name + channel] = set()
            self.names[connection_name + channel].add(nick)

    def part_name(self, connection_name, channel, nick):
        """Removes a name from the names set for a given connection and channel."""
        try:
            self.names[connection_name + channel].remove(nick)
        except KeyError:
            print('Attempted to remove {}{}: {}, but it didn\'t exist.'.format(connection_name, channel, nick))

    def set_names(self, connection_name, channel, names):
        """Update the set of names for a channel upon receiving a /NAMES list from the server."""
        temp_names = []
        for name in names.strip().split():
            temp_names.append(name.strip('@').strip('~'))
        self.names[connection_name + channel] = set(temp_names)

    #def get_sockets(self):
        #return [self.connections[connection_name] for connection_name in self.connections]