#!/usr/bin/env python
"""An extensible, Eve: Online chat bot for IRC built using twisted."""

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
    def __init__(self, nickname):
        self.nickname = nickname
        self.commands = CommandMap()
        self.commands.load_plugins(exclude=('towers_plugin', 'timers_plugin'))
        self.commands.map_command(".help", self.help)

    def signedOn(self):
        # called on connect
        logger.debug("Welcome received, joining channel.")
        self.join(self.factory.channel)
        if self.factory.operuser and self.factory.operpass:
            logger.debug("Operator credentials set, sending OPER.")
            self.sendLine("OPER {} {}".format(self.factory.operuser, self.factory.operpass))

    def privmsg(self, user, channel, message):
        logger.debug("RECV user={} channel={} message={}".format(repr(user), repr(channel), repr(message)))
        user = user.split('!', 1)[0]
        reply_to = self.get_reply_target(channel, user)
        responses = self.get_response(message)
        if responses:
            for line in responses:
                logger.debug("SEND reply_to={} line={}".format(reply_to, line))
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

    def is_channel_message(self, channel):
        return channel == self.factory.channel

    def help(self):
        return ["Available commands: {}".format(', '.join(sorted(self.commands.triggers())))]


class BotTooperFactory(protocol.ClientFactory):
    def __init__(self, channel, nickname, operuser=None, operpass=None):
        self.channel = channel
        self.nickname = nickname
        self.operuser = operuser
        self.operpass = operpass

    def buildProtocol(self, addr):
        protokol = BotTooper(self.nickname)
        protokol.factory = self
        return protokol

    def clientConnectionLost(self, connector, reason):
        logger.debug("Lost connection. Reconnecting.")
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        logger.debug("Connection failed. Stopping.")
        reactor.stop()


def main(host, port, channel, nickname, operuser=None, operpass=None, verbose=False):
    if verbose:
        logger.setLevel(logging.DEBUG)
    logger.debug("Attempting to connect.")
    reactor.connectTCP(host, int(port), BotTooperFactory(channel, nickname, operuser, operpass))
    reactor.run()

if __name__ == "__main__":
    argh.dispatch_command(main)