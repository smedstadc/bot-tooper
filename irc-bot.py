#!/usr/bin/env python
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
import argh
from commandmap import CommandMap
import logging
import sys

# ensure python2 is using unicode
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot-tooper-irc')


class BotTooper(irc.IRCClient):

    def __init__(self, nickname, channel, operuser=None, operpass=None):
        self.nickname = nickname
        self.channel = channel
        self.operuser = operuser
        self.operpass = operpass
        self.commands = CommandMap()
        self.commands.load_plugins()

    def signedOn(self):
        # called on connect
        self.join(self.channel)
        if self.operuser and self.operpass:
            self.sendLine("OPER {} {}".format(self.operuser, self.operpass))

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
        command = self.commands.get_command(message[0])
        if command:
            if len(message) > 1 and command.arity > 1:
                return command.func(message[1])
            else:
                return command.func()
        else:
            return None

    def is_private_message(self, channel):
        return channel == self.nickname

    @staticmethod
    def is_channel_message(channel):
        return channel.startswith('#')


class BotTooperFactory(protocol.ClientFactory):
    def __init__(self, channel, nickname, operuser=None, operpass=None):
        self.channel = channel
        self.nickname = nickname
        self.operuser = operuser
        self.operpass = operpass

    def buildProtocol(self, addr):
        proto = BotTooper(self.nickname, self.channel, self.operuser, self.operpass)
        proto.factory = self
        return proto

    def clientConnectionLost(self, connector, reason):
        # try to reconnect if disconnected
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


def main(host, port, channel, nickname, operuser=None, operpass=None, verbose=False):
    reactor.connectTCP(host, int(port), BotTooperFactory(channel, nickname, operuser, operpass))
    reactor.run()

if __name__ == "__main__":
    argh.dispatch_command(main)