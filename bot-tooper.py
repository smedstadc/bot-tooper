#!/usr/bin/env python3
""" bot-tooper.py
    an IRC Bot geared towards eve-corporations by Bud Tooper

    Bot supports multiple channels and responds to the .commands listed below. Certain commands are unavailable to
    members outside channels without permissions. The bot will automatically respond to the appropriate pm or channel.

    COMMAND  - DESCRIPTION
    .jita      - price check for one or more eve-items,
                 multiple names may be separated by '; ',
                 checks for exact matches first then does
                 a startswith style search that will bail
                 out if it matches too many names.
    .amarr     - as .jita, but for amarr
    .dodixie   - as .jita, but for dodixie
    .rens      - as .jita, but for rens
    .hek       - as .jita, but for hek
    .time      - UTC time in human-friendly format
    .upladtime - UTC time in robot-friendly ISO-8601 format
    .ops       - lists upcoming ops and countdown timers (requires permissions)
    .addop     - add an event to the list by datetime
    .addtimer  - add an event to the list by timedelta
    .rmop      - removes a timer from the list, multiple numbers separated by '; '
    http(s)    - fetches page titles for links beginning with http

    Most of these will generate a usage hint or error message in response to bad commands/arguments.
"""

# TODO DOCSTRING ALL THE THINGS

from ircmanager import IrcManager
import settings
import re
from datetime import datetime, timedelta
import url
import pricecheck
import countdown

# parse_message patterns
# PING :gobbeldygook
_ping_message_pattern = re.compile(r'^PING :(.+)$')
# :server 001 recipient :Welcome to the servername recipient!username@hostname
_rpl_welcome_pattern = re.compile(r'^(.+) 001 (.+) :(.+)$')
# :nick!user@host PRIVMSG recipient :content
_message_pattern = re.compile(r'^:(.+)!.+@.+ PRIVMSG (.+) :(.+)$')
# :nick!user@host JOIN :#channel
_join_pattern = re.compile(r'^:(.+)!.+@.+ JOIN :(.+)$')
# :nick!user@host PART #channel :"Leaving"
_part_pattern = re.compile(r'^:(.+)!.+@.+ PART (.+) :".+"$')
# :server 353 recipient = #channel :name1 name2
_names_pattern = re.compile(r'^:.+ 353 .+ [=*@] (.+) :(.+)$')
# :irc.nosperg.com 332 test_tooper #test3 :butts butts butts butts
_topic_pattern = re.compile(r'^:.+ 332 .+ #.+ :.+$')

# .command patterns
_help_pattern = re.compile(r'^[.]help$')
_time_pattern = re.compile(r'^[.]time$')
_upladtime_pattern = re.compile(r'^[.]upladtime$')
_url_pattern = re.compile(r'(https?://\S+)')
_price_check_pattern = re.compile(r'^[.](jita|amarr|dodixie|rens|hek) (.+)$')
_ops_pattern = re.compile(r'^[.]ops$')
# .addop <year-month-day@hour:minute> <name>
_addop_pattern = re.compile(r'^[.]addop (\d{4}-\d{2}-\d{2}@\d{2}:\d{2}) (.+)$')
# .addtimer <days>d<hours>h<minutes>m <name>
_addtimer_pattern = re.compile(r'^[.]addtimer ([0-3])[dD]([01]?[0-9]|2[0-3])[hH]([0-9]|[0-5][0-9])[mM] (.+)$')
# .rmop <number>
_rmop_pattern = re.compile(r'^[.]rmop (.+)$')


# TODO alter to return a named tuple, rather than a dict
def parse_message(line_received):
    """Returns a dict of values extracted from a line sent by the sever.
    Values not found in the line default to None."""

    # return ping dict
    m = re.match(_ping_message_pattern, line_received)
    if m is not None:
        group = m.groups()
        return {'type': 'ping', 'content': group[0]}

    # return message dict
    m = re.match(_message_pattern, line_received)
    if m is not None:
        group = m.groups()
        return {'type': 'message', 'nick': group[0], 'recipient': group[1], 'content': group[2]}

    # return names dict
    m = re.match(_names_pattern, line_received)
    if m is not None:
        group = m.groups()
        return {'type': 'names', 'channel': group[0], 'names': group[1]}

    # return welcome dict
    m = re.match(_rpl_welcome_pattern, line_received)
    if m is not None:
        group = m.groups()
        return {'type': 'welcome', 'server': group[0], 'recipient': group[1], 'content': group[2]}

    # return join dict
    m = re.match(_join_pattern, line_received)
    if m is not None:
        group = m.groups()
        return {'type': 'join', 'nick': group[0], 'channel': group[1]}

    # return part dict
    m = re.match(_part_pattern, line_received)
    if m is not None:
        group = m.groups()
        return {'type': 'part', 'nick': group[0], 'channel': group[1]}

    # return topic dict
    m = re.match(_topic_pattern, line_received)
    if m is not None:
        return {'type': 'topic'}
    # return empty dict if no pattern is matched
    return {}


def opsec_enabled(reply_to, connection_name):
    """Returns True if reply_to is a channel or user with permissions.
       A user with permissions is present in at least one channel with permissions.
    """
    if reply_to.startswith('#'):
        if reply_to in opsec_channels:
            return True
    else:
        for channel in opsec_channels:
            if reply_to in ircm.names[connection_name+channel]:
                return True
    return False


def time_trigger(reply_to, message):
    if re.match(_time_pattern, message['content']) is not None:
        ircm.privmsg(reply_to, 'UTC {}'.format(datetime.utcnow().strftime("%A %B %d, %Y - %H:%M%p")), connection_name)


def uplad_time_trigger(reply_to, message):
    if re.match(_upladtime_pattern, message['content']) is not None:
        ircm.privmsg(reply_to, 'UTC {}'.format(datetime.utcnow().isoformat()), connection_name)


def url_trigger(reply_to, message):
    url_args = re.findall(_url_pattern, message['content'])
    if len(url_args) > 0:
        for url_message in url.get_url_titles(url_args):
            ircm.privmsg(reply_to, url_message, connection_name)


def help_trigger(reply_to, message, full_help=False):
    if re.match(_help_pattern, message['content']) is not None:
        ircm.privmsg(reply_to, '.jita, .amarr, .dodixie, .rens, .hek, .time, .upladtime', connection_name)
        if full_help:
            ircm.privmsg(reply_to, '.ops', connection_name)
            ircm.privmsg(reply_to, '.addop <year/month/day@hour:minute> <event name>', connection_name)
            ircm.privmsg(reply_to, '.addtimer <#d#h#m> <timer name>', connection_name)
            ircm.privmsg(reply_to, '.rmop <op number>', connection_name)


def ops_trigger(reply_to, message):
    if re.search(_ops_pattern, message['content']) is not None:
        for event_message in countdown.get_countdown_messages():
            ircm.privmsg(reply_to, event_message, connection_name)


def addop_trigger(reply_to, message):
    usage_hint = 'Usage: .addop <year>-<month>-<day>@<hour>:<minute> <name>'
    if re.match(r'^[.]addop(.+)?$', message['content']) is not None:
        m = re.match(_addop_pattern, message['content'])
        if m is not None:
            group = m.groups()
            try:
                countdown.add_event(datetime.strptime(group[0], '%Y-%m-%d@%H:%M'), group[1])
                ircm.privmsg(reply_to, 'Event added.', connection_name)
            # IndexError might not be possible in this implementation. Betterto be safe than sorry until I make sure.
            except IndexError:
                ircm.privmsg(reply_to, usage_hint, connection_name)
            except ValueError:
                ircm.privmsg(reply_to, usage_hint, connection_name)
        else:
            ircm.privmsg(reply_to, usage_hint, connection_name)


def addtimer_trigger(reply_to, message):
    usage_hint = 'Usage: .addtimer <days>d<hours>h<minutes>m <name>'
    if re.match(r'^[.]addtimer(.+)?$', message['content']) is not None:
        m = re.match(_addtimer_pattern, message['content'])
        if m is not None:
            group = m.groups()
            delta_days = int(group[0])
            delta_hours = int(group[1])
            delta_minutes = int(group[2])
            name = group[3]
            dt = datetime.utcnow()+timedelta(days=delta_days, hours=delta_hours, minutes=delta_minutes)
            try:
                countdown.add_event(dt, name)
                ircm.privmsg(reply_to, 'Event added.', connection_name)
            except ValueError:
                ircm.privmsg(reply_to, usage_hint, connection_name)
        else:
            ircm.privmsg(reply_to, usage_hint, connection_name)


def rmop_trigger(reply_to, message):
    usage_hint = 'Usage: .rmop <op>[; <op>; <op>...]+'
    if re.match(r'^[.]rmop(.+)?', message['content']) is not None:
        m = re.match(_rmop_pattern, message['content'])
        if m is not None:
            group = m.groups()
            try:
                args = sorted(set([int(x) for x in group[0].split('; ')]), reverse=True)
                if max(args) > len(countdown.events) or min(args) < 1:
                    ircm.privmsg(reply_to, 'One or more op numbers out of bounds.', connection_name)
                else:
                    for arg in args:
                        ircm.privmsg(reply_to, countdown.remove_event(arg), connection_name)
            except ValueError:
                ircm.privmsg(reply_to, usage_hint, connection_name)
        else:
            ircm.privmsg(reply_to, usage_hint, connection_name)


def price_check_trigger(reply_to, message):
    m = re.match(_price_check_pattern, message['content'])
    if m is not None:
        group = m.groups()
        if reply_to.startswith('#'):
            for price_message in pricecheck.get_price_messages(group[1].split('; '), group[0]):
                ircm.privmsg(reply_to, price_message, connection_name)
        else:
            for price_message in pricecheck.get_price_messages(group[1].split('; '), group[0], 50):
                ircm.privmsg(reply_to, price_message, connection_name)


def handle_triggers(reply_to, message):
    time_trigger(reply_to, message)
    uplad_time_trigger(reply_to, message)
    url_trigger(reply_to, message)
    price_check_trigger(reply_to, message)
    if opsec_enabled(reply_to, connection_name):
        help_trigger(reply_to, message, full_help=True)
        ops_trigger(reply_to, message)
        addop_trigger(reply_to, message)
        addtimer_trigger(reply_to, message)
        rmop_trigger(reply_to, message)
    else:
        help_trigger(reply_to, message)

ircm = IrcManager()

# pull settings from external module
host = settings.HOST
port = settings.PORT
channels = settings.CHANNELS
opsec_channels = settings.OPSEC
nick_name = settings.NICKNAME
user_name = settings.USERNAME
host_name = settings.HOSTNAME
server_name = settings.SERVERNAME
real_name = settings.REALNAME

# connect to server
ircm.connect(host, port, 'nosperg')
for connection_name in ircm.connections.keys():
    ircm.nick(nick_name, connection_name)
    ircm.user(user_name, host_name, server_name, real_name, connection_name)

# TODO fix line skipping
# main bot loop
while True:
    for connection_name in ircm.connections.keys():
        for line_received in ircm.connections[connection_name].recv(8192).decode('utf-8', 'ignore').split('\r\n'):
            # don't print empty strings
            if len(line_received) > 0:
                print(line_received)

            # get message dict
            message = parse_message(line_received)

            # respond to PING with PONG
            if message.get('type', None) == 'ping':
                ircm.pong(message['content'], connection_name)

            # join channels after RPL_WELCOME
            if message.get('type', None) == 'welcome':
                for channel in channels:
                    ircm.join(channel, connection_name)
                # if operator user/pass is set try to /OPER
                if settings.OPERUSER is not None and settings.OPERPASS is not None:
                    ircm.oper(settings.OPERUSER, settings.OPERPASS, connection_name)

            # set names upon joining channel
            if message.get('type', None) == 'names':
                ircm.set_names(connection_name, message['channel'], message['names'])

            # add/remove names upon observing join/part
            if message.get('type', None) == 'join':
                ircm.join_name(connection_name, message['channel'], message['nick'])
            if message.get('type', None) == 'part':
                ircm.part_name(connection_name, message['channel'], message['nick'])

            # skip topic lines
            if message.get('type', None) == 'topic':
                print('Ignoring topic message.')

            # respond commands in chat or pm
            if message.get('type', None) == 'message':
                if message['recipient'] == nick_name:
                    handle_triggers(message['nick'], message)
                else:
                    handle_triggers(message['recipient'], message)