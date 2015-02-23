#!/usr/bin/env python
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
import argh
import os
from glob import glob
import sys


class BotTooper(irc.IRCClient):

    def __init__(self, nickname):
        self.nickname = nickname
        self.commands = {}
        self.load_plugins()

    def signedOn(self):
        # called on connect
        self.join(self.factory.channel)

    def privmsg(self, user, channel, message):
        user = user.split('!', 1)[0]
        reply_to = self.get_reply_target(channel, user)
        responses = self.get_response(message)
        if responses:
            for line in responses:
                self.msg(reply_to, line)

    def get_reply_target(self, channel, user):
        if self.is_private_message(channel):
            return user
        elif self.is_channel_message(channel):
            return channel

    def get_response(self, message):
        message = message.split(None, 1)
        command = self.commands.get(message[0])
        if command:
            if len(message) > 1:
                return command(message[1])
            else:
                return command()
        else:
            return None

    def is_private_message(self, channel):
        return channel == self.nickname

    def is_channel_message(self, channel):
        return channel.startswith('#')

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
            plugin.init_plugin(self.commands)


class BotTooperFactory(protocol.ClientFactory):
    def __init__(self, channel, nickname):
        self.channel = channel
        self.nickname = nickname

    def buildProtocol(self, addr):
        proto = BotTooper(self.nickname)
        proto.factory = self
        return proto

    def clientConnectionLost(self, connector, reason):
        # try to reconnect if disconnected
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


def main(host, port, channel, nickname):
    reactor.connectTCP(host, int(port), BotTooperFactory(channel, nickname))
    reactor.run()

if __name__ == "__main__":
    argh.dispatch_command(main)