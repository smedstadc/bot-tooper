#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys
import logging
import sleekxmpp
import argh
from commandmap import CommandMap

# ensure python2 is using unicode
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot-tooper-jabber')


class BotTooper(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.room = room
        self.nick = nick
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("groupchat_message", self.groupchat_message)
        self.add_event_handler("message", self.direct_message)
        self.commands = CommandMap()
        self.commands.load_plugins()

    def session_start(self, event):
        """Process the session_start event."""
        logger.debug("RECV session_start")
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)

    def direct_message(self, msg):
        """Process incoming message stanzas from any user."""
        logger.debug("RECV {}".format(repr(msg)))
        if msg['type'] in ('chat', 'normal'):
            responses = self.get_responses(msg)
            if responses:
                for line in responses:
                    logger.debug("SEND reply_to={} message={}".format(msg['from'], line))
                    self.send_message(mto=msg['from'], mfrom=msg['to'], mbody=line)

    def groupchat_message(self, msg):
        """Process incoming message stanzas from any chat room."""
        logger.debug("RECV {}".format(repr(msg)))
        # Infinite loops are bad. Don't reply to self.
        if msg['mucnick'] != self.nick and msg['type'] == 'groupchat':
            responses = self.get_responses(msg)
            if responses:
                for line in responses:
                    logger.debug("SEND reply_to={} type='groupchat' message={}".format(msg['from'].bare, line))
                    self.send_message(mto=msg['from'].bare, mfrom=msg['to'], mbody=line, mtype='groupchat')

    def get_responses(self, msg):
        """Return a list of responses to initialized triggers if any. Return an empty list if not."""
        message = msg["body"].split(None, 1)
        command = self.commands.get_command(message[0])
        if command:
            if len(message) > 1 and command.arity > 1:
                return command.func(message[1])
            else:
                return command.func()
        else:
            return None


def main(jid, password, room, nick, verbose=False):
    if verbose:
        logger.setLevel(logging.DEBUG)

    xmpp = BotTooper(jid, password, room, nick)
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multi-User Chat
    xmpp.register_plugin('xep_0199')  # XMPP Ping
    logger.debug("Attempting to connect.")
    if xmpp.connect():
        xmpp.process(block=False)
        logger.info("Connected.")
    else:
        logger.info("Unable to connect.")


if __name__ == '__main__':
    argh.dispatch_command(main)