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
import getpass
from optparse import OptionParser
import re
import sleekxmpp
from datetime import datetime, timedelta
import url
import pricecheck
import countdown
import settings
import towers

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

# TODO Move argument pattern matching into respective modules.
# Bot should match triggers. Commands should be responsible for validating input.
help_pattern = re.compile(r'^[.]help$')
time_pattern = re.compile(r'^[.]time$')
upladtime_pattern = re.compile(r'^[.]upladtime$')
url_pattern = re.compile(r'(https?://\S+)')
price_check_pattern = re.compile(r'^[.](?P<system>jita|amarr|dodixie|rens|hek) (?P<item_args>.+)$')
ops_pattern = re.compile(r'^[.]ops$')
# .addop <year-month-day@hour:minute> <name>
addop_pattern = re.compile(
    r'^[.]addop (?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})[@Tt](?P<hour>\d{1,2}):(?P<minute>\d{1,2}) (?P<name>.+)$')
# .addtimer <days>d<hours>h<minutes>m <name>
addtimer_pattern = re.compile(
    r'^[.]addop (?P<days>\d{1,3})[dD](?P<hours>\d{1,2})[hH](?P<minutes>\d{1,2})[mM] (?P<name>.+)$')
# .rmop <number>
rmop_pattern = re.compile(r'^[.]rmop (?P<rmop_args>\d+)$')
# .addtower <name>
addtower_pattern = re.compile(r'^[.]addtower (?P<addtower_arg>.+)$')
# .rmtower <name>
rmtower_pattern = re.compile(r'^[.]rmtower (?P<rmtower_arg>.+)$')
# .marktower <name>
marktower_pattern = re.compile(r'^[.]marktower (?P<marktower_arg>.+)$')
towers_pattern = re.compile(r'^[.]towers$')

class JabberBot(sleekxmpp.ClientXMPP):

    """
    A simple SleekXMPP bot that will greets those
    who enter the room, and acknowledge any messages
    that mentions the bot's nickname.
    """

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The groupchat_message event is triggered whenever a message
        # stanza is received from any chat room. If you also also
        # register a handler for the 'message' event, MUC messages
        # will be processed by both handlers.
        self.add_event_handler("groupchat_message", self.muc_message)

        # The groupchat_presence event is triggered whenever a
        # presence stanza is received from any chat room, including
        # any presences you send yourself. To limit event handling
        # to a single room, use the events muc::room@server::presence,
        # muc::room@server::got_online, or muc::room@server::got_offline.
        self.add_event_handler("muc::%s::got_online" % self.room, self.muc_online)
        self.add_event_handler("message", self.message)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        # If a room password is needed, use:
                                        # password=the_room_password,
                                        wait=True)

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            for line in self.get_reply_lines(msg):
                self.send_message(mto=msg['from'], mfrom=msg['to'], mbody=line)

    def muc_message(self, msg):
        if msg['mucnick'] != self.nick and msg['type'] == 'groupchat':
            for line in self.get_reply_lines(msg):
                self.send_message(mto=msg['from'].bare, mfrom=msg['to'], mbody=line, mtype='groupchat')

    def get_reply_lines(self, msg):
        """
        :rtype list

        Process incoming message stanzas from any chat room. Be aware
        that if you also have any handlers for the 'message' event,
        message stanzas may be processed by both handlers, so check
        the 'type' attribute when using a 'message' event handler.

        IMPORTANT: Always check that a message is not from yourself,
                   otherwise you will create an infinite loop responding
                   to your own messages.

        This handler will reply to messages that contain a valid command.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """

        if time_pattern.match(msg['body']) is not None:
            return ['UTC {}'.format(datetime.utcnow().strftime("%A %B %d, %Y - %H:%M%p"))]

        if upladtime_pattern.match(msg['body']) is not None:
            return ['UTC {}'.format(datetime.utcnow().isoformat())]

        if url_pattern.search(msg['body']) is not None:
            url_args = re.findall(url_pattern, msg['body'])
            if len(url_args) > 0:
                return ['"'+n+'"' for n in url.get_url_titles(url_args)]

        m = price_check_pattern.match(msg['body'])
        if m is not None:
            return pricecheck.get_price_messages(m.group('item_args').split('; '), m.group('system'))

        if ops_pattern.match(msg['body']) is not None:
            return countdown.get_countdown_messages()

        addop_use_hint = 'Usage: .addop <year>-<month>-<day>@<hour>:<minute> <name> OR <days>d<hours>h<minutes>m <name>'
        if re.match(r'^[.]addop(.+)?$', msg['body']) is not None:
            # Check datetime addop format
            m = re.match(addop_pattern, msg['body'])
            if m is not None:
                if countdown.add_datetime(m):
                    return ['Event added.']
                else:
                    return [addop_use_hint]
            else:
                # Check countdown addop format
                m = re.match(addtimer_pattern, msg['body'])
                if m is not None:
                    if countdown.add_timer(m):
                        return ['Event added.']
                    else:
                        return [addop_use_hint]
                else:
                    return [addop_use_hint]

        rmop_usage_hint = 'Usage: .rmop <op id>'
        if re.match(r'^[.]rmop(.+)?$', msg['body']) is not None:
            m = re.match(rmop_pattern, msg['body'])
            if m is not None:
                return countdown.remove_event(m.group('rmop_args'))
            else:
                return [rmop_usage_hint]

        addtower_usage_hint = 'Usage: .addtower <tower name>'
        if re.match(r'[.]addtower(.+)?$', msg['body']) is not None:
            m = re.match(addtower_pattern, msg['body'])
            if m is not None:
                return towers.add_tower(m.group('addtower_arg'))
            else:
                return [addtower_usage_hint]

        rmtower_usage_hint = 'Usage: .rmtower <tower name>'
        if re.match(r'[.]rmtower(.+)?$', msg['body']) is not None:
            m = re.match(rmtower_pattern, msg['body'])
            if m is not None:
                return towers.remove_tower(m.group('rmtower_arg'))
            else:
                return [rmtower_usage_hint]

        marktower_usage_hint = 'Usage: .marktower <tower name>'
        if re.match(r'[.]marktower(.+)?$', msg['body']) is not None:
            m = re.match(marktower_pattern, msg['body'])
            if m is not None:
                return towers.mark_checked(m.group('marktower_arg'))
            else:
                return [marktower_usage_hint]

        if re.match(towers_pattern, msg['body']) is not None:
            return towers.get_tower_messages()

        if help_pattern.match(msg['body']) is not None:
            return ['Commands: .help, .time, .upladtime, .jita, .amarr, .dodixie, .rens, .hek, .ops, .addop, .rmop']

    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.

        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """
        pass  # disable this for now
        # if presence['muc']['nick'] != self.nick:
        #     self.send_message(mto=presence['from'].bare,
        #                       mbody="Hello, %s %s" % (presence['muc']['role'],
        #                                               presence['muc']['nick']),
        #                       mtype='groupchat')


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=settings.XMPP_LOG_LEVEL)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=settings.XMPP_LOG_LEVEL)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=settings.XMPP_LOG_LEVEL)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use",
                    default=settings.XMPP_JID)
    optp.add_option("-p", "--password", dest="password",
                    help="password to use",
                    default=settings.XMPP_PASSWORD)
    optp.add_option("-r", "--room", dest="room",
                    help="MUC room to join",
                    default=settings.XMPP_ROOM)
    optp.add_option("-n", "--nick", dest="nick",
                    help="MUC nickname",
                    default=settings.XMPP_NICK)

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.room is None:
        opts.room = raw_input("MUC room: ")
    if opts.nick is None:
        opts.nick = raw_input("MUC nickname: ")

    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = JabberBot(opts.jid, opts.password, opts.room, opts.nick)
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multi-User Chat
    xmpp.register_plugin('xep_0199')  # XMPP Ping
    #xmpp.register_plugin('xep_0078')  # Legacy Auth

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp.process(block=False)
        print("Done")
    else:
        print("Unable to connect.")