#!/usr/bin/env python3
""" bot-tooper.py
    an IRC Bot geared towards eve-corporations by Bud Tooper

    Bot supports multiple channels and responds to the .commands listed below. Certain commands are unavailable to
    members outside channels without permissions. The bot will automatically respond to the appropriate pm or channel.

    COMMAND  - DESCRIPTION
    .jita      - price check for one or more eve-items,
                 multiple names may be separated by '; ',
                 checks for exact matches first then does
                 a regex search that will bail out if it
                 matches too many names. Searches sent to
                 the bot via PM have a higher limit.
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
from ircsocket import IrcSocket
import settings
import re
from datetime import datetime, timedelta
import url
import pricecheck
import countdown
import time

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
#:budtooper!budtooper@nosperg-keedpp.ma.comcast.net NICK bud
_nick_pattern = re.compile(r'^:(.+)!.+@.+ NICK (.+)$')
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


# TODO return named tuples instead of dicts
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

    # return nick dict
    m = re.match(_nick_pattern, line_received)
    if m is not None:
        group = m.groups()
        return {'type': 'nick', 'old': group[0], 'new': group[1]}

    # return topic dict
    m = re.match(_topic_pattern, line_received)
    if m is not None:
        return {'type': 'topic'}
    # return empty dict if no pattern is matched
    return {}


def opsec_enabled(reply_to):
    """Returns True if reply_to is a channel or user with permissions.
       A user with permissions is present in at least one channel with permissions.
    """
    if reply_to.startswith('#'):
        if reply_to in opsec_channels:
            return True
    else:
        for channel in opsec_channels:
            if reply_to in irc.names[channel]:
                return True
    return False


def time_trigger(reply_to, message):
    if re.match(_time_pattern, message['content']) is not None:
        irc.privmsg(reply_to, 'UTC {}'.format(datetime.utcnow().strftime("%A %B %d, %Y - %H:%M%p")))


def uplad_time_trigger(reply_to, message):
    if re.match(_upladtime_pattern, message['content']) is not None:
        irc.privmsg(reply_to, 'UTC {}'.format(datetime.utcnow().isoformat()))


def url_trigger(reply_to, message):
    url_args = re.findall(_url_pattern, message['content'])
    if len(url_args) > 0:
        for url_message in url.get_url_titles(url_args):
            irc.privmsg(reply_to, url_message)


def help_trigger(reply_to, message, full_help=False):
    if re.match(_help_pattern, message['content']) is not None:
        irc.privmsg(reply_to, '.jita, .amarr, .dodixie, .rens, .hek, .time, .upladtime')
        if full_help:
            irc.privmsg(reply_to, '.ops')
            irc.privmsg(reply_to, '.addop <year/month/day@hour:minute> <event name>')
            irc.privmsg(reply_to, '.addtimer <#d#h#m> <timer name>')
            irc.privmsg(reply_to, '.rmop <op number>')


def ops_trigger(reply_to, message):
    if re.search(_ops_pattern, message['content']) is not None:
        for event_message in countdown.get_countdown_messages():
            irc.privmsg(reply_to, event_message)


def addop_trigger(reply_to, message):
    usage_hint = 'Usage: .addop <year>-<month>-<day>@<hour>:<minute> <name>'
    if re.match(r'^[.]addop(.+)?$', message['content']) is not None:
        m = re.match(_addop_pattern, message['content'])
        if m is not None:
            group = m.groups()
            try:
                countdown.add_event(datetime.strptime(group[0], '%Y-%m-%d@%H:%M'), group[1])
                irc.privmsg(reply_to, 'Event added.')
            # IndexError might not be possible in this implementation. Betterto be safe than sorry until I make sure.
            except IndexError:
                irc.privmsg(reply_to, usage_hint)
            except ValueError:
                irc.privmsg(reply_to, usage_hint)
        else:
            irc.privmsg(reply_to, usage_hint)


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
                irc.privmsg(reply_to, 'Event added.')
            except ValueError:
                irc.privmsg(reply_to, usage_hint)
        else:
            irc.privmsg(reply_to, usage_hint)


def rmop_trigger(reply_to, message):
    usage_hint = 'Usage: .rmop <op>[; <op>; <op>...]+'
    if re.match(r'^[.]rmop(.+)?', message['content']) is not None:
        m = re.match(_rmop_pattern, message['content'])
        if m is not None:
            group = m.groups()
            try:
                args = sorted(set([int(x) for x in group[0].split('; ')]), reverse=True)
                if max(args) > len(countdown.events) or min(args) < 1:
                    irc.privmsg(reply_to, 'One or more op numbers out of bounds.')
                else:
                    for arg in args:
                        irc.privmsg(reply_to, countdown.remove_event(arg))
            except ValueError:
                irc.privmsg(reply_to, usage_hint)
        else:
            irc.privmsg(reply_to, usage_hint)


def price_check_trigger(reply_to, message):
    m = re.match(_price_check_pattern, message['content'])
    if m is not None:
        group = m.groups()
        if reply_to.startswith('#'):
            for price_message in pricecheck.get_price_messages(group[1].split('; '), group[0]):
                irc.privmsg(reply_to, price_message)
        else:
            for price_message in pricecheck.get_price_messages(group[1].split('; '), group[0], 50):
                irc.privmsg(reply_to, price_message)


def handle_triggers(reply_to, message):
    time_trigger(reply_to, message)
    uplad_time_trigger(reply_to, message)
    url_trigger(reply_to, message)
    price_check_trigger(reply_to, message)
    if opsec_enabled(reply_to):
        help_trigger(reply_to, message, full_help=True)
        ops_trigger(reply_to, message)
        addop_trigger(reply_to, message)
        addtimer_trigger(reply_to, message)
        rmop_trigger(reply_to, message)
    else:
        help_trigger(reply_to, message)


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
op_user = settings.OPERUSER
op_pass = settings.OPERPASS

# connect to server
irc = IrcSocket()
irc.connect((host, port))
time.sleep(3)
irc.user(user_name, host_name, server_name, real_name)
irc.nick(nick_name)

# main bot loop
while True:
    for line_received in irc.sock.recv(8192).decode('utf-8', 'ignore').split('\r\n'):
        # don't print empty strings
        if len(line_received) > 0:
            print(line_received)

        # get message dict
        message = parse_message(line_received)

        # respond to PING with PONG
        if message.get('type', None) == 'ping':
            irc.pong(message['content'])

        # join channels after RPL_WELCOME
        if message.get('type', None) == 'welcome':
            for channel in channels:
                irc.join(channel)

            # if operator user/pass is set try to /OPER
            if settings.OPERUSER is not None and settings.OPERPASS is not None:
                irc.oper(op_user, op_pass)

        # set names upon joining channel
        if message.get('type', None) == 'names':
            irc.set_names(message['channel'], message['names'])

        # add/remove names upon observing join/part/nick
        if message.get('type', None) == 'join':
            irc.name_joined(message['channel'], message['nick'])

        if message.get('type', None) == 'part':
            irc.name_parted(message['channel'], message['nick'])

        if message.get('type', None) == 'nick':
            print('Observed user:{} change nick to:{}'.format(message['old'], message['new']))
            irc.nick_changed(message['old'], message['new'])

        # skip topic lines
        if message.get('type', None) == 'topic':
            print('Ignoring topic message.')

        # respond commands in chat or pm
        if message.get('type', None) == 'message':
            if message['recipient'] == nick_name:
                handle_triggers(message['nick'], message)
            else:
                handle_triggers(message['recipient'], message)