#!/usr/bin/env python3
""" bot.py
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

from ircsocket import IrcSocket
import settings
import re
from datetime import datetime, timedelta
import url
import pricecheck
import countdown
import sys
from socket import timeout
# parse_message patterns
# PING :gobbeldygook
ping_message_pattern = re.compile(r'^PING :(?P<content>.+)$')
# :server 001 recipient :Welcome to the servername recipient!username@hostname
rpl_welcome_pattern = re.compile(r'^.+ 001 .+ :.+$')
# :nick!user@host PRIVMSG recipient :content
message_pattern = re.compile(r'^:(?P<nick>.+)!.+@.+ PRIVMSG (?P<recipient>\S+) :(?P<content>.+)$')
# :nick!user@host JOIN :#channel
join_pattern = re.compile(r'^:(?P<nick>.+)!.+@.+ JOIN :(?P<channel>.+)$')
# :nick!user@host PART #channel :"Leaving"
part_pattern = re.compile(r'^:(?P<nick>.+)!.+@.+ PART (?P<channel>.+) :".+"$')
# :oldnick!user@host NICK newnick
nick_pattern = re.compile(r'^:(?P<oldnick>.+)!.+@.+ NICK (?P<newnick>.+)$')
# :server 353 recipient = #channel :name1 name2
rpl_names_pattern = re.compile(r'^:.+ 353 .+ [=*@] (?P<channel>.+) :(?P<names>.+)$')
# :server 332 recipient #channel :butts butts butts butts
rpl_topic_pattern = re.compile(r'^:.+ 332 .+ #.+ :.+$')
# :server 433 * nick :Nickname is already in use.
rpl_nick_conflict_pattern = re.compile(r'^:.+ 433 .+ .+ :Nickname is already in use.$')
# ERROR :Closing link: (test_tooper@c-76-24-157-37.hsd1.ma.comcast.net) [Registration timeout]
error_pattern = re.compile(r'^ERROR :(?P<content>.+)$')
# :irc.nosperg.com NOTICE #test3 :Replaying up to 15 lines of pre-join history spanning up to 86400 seconds
skiplines_notice_pattern = re.compile(r'^:irc.nosperg.com NOTICE (?P<channel>#\S+) :Replaying up to (?P<num_skips>\d{1,2}) lines of pre-join history spanning up to \d+ seconds$')

# .command patterns
help_pattern = re.compile(r'^[.]help$')
time_pattern = re.compile(r'^[.]time$')
upladtime_pattern = re.compile(r'^[.]upladtime$')
url_pattern = re.compile(r'(https?://\S+)')
price_check_pattern = re.compile(r'^[.](jita|amarr|dodixie|rens|hek) (.+)$')
ops_pattern = re.compile(r'^[.]ops$')
# .addop <year-month-day@hour:minute> <name>
addop_pattern = re.compile(
    r'^[.]addop (?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})[@Tt](?P<hour>\d{1,2}):(?P<minute>\d{1,2}) (?P<name>.+)$')
# .addtimer <days>d<hours>h<minutes>m <name>
addtimer_pattern = re.compile(
    r'^[.]addop (?P<days>\d{1,3})[dD](?P<hours>\d{1,2})[hH](?P<minutes>\d{1,2})[mM] (?P<name>.+)$')
# .rmop <number>
rmop_pattern = re.compile(r'^[.]rmop (?P<rmop_args>.+)$')
pidgin_notice_pattern = re.compile(r'^ ?[(]notice[)] (?P<content>.+)$')


def lines_from_socket(socket):
    """Generator that yields complete messages one at a time until the socket buffer is empty."""
    # buffer mechanism prevents bot processing incomplete lines
    done = False
    try:
        buffer = socket.recv(4096).decode('utf-8', 'ignore')
        while not done:
            if '\r\n' in buffer:
                line, buffer = buffer.split('\r\n', 1)
                yield line
            else:
                more = socket.recv(4096).decode('utf-8', 'ignore')
                if not more:
                    done = True
                else:
                    buffer = buffer + more
        if buffer:
            yield buffer
    except timeout:
        print("INFO: It's quiet. Too quiet. Server, are you there?")
        try:
            irc.command('PING ' + settings.IRC_HOST)
            # calling socket.recv() here to check for a PONG could screw with the buffer
            # and if the socket is closed on the server side attempting to send a PING would
            # raise a timeout or ConnectionReset exception anyway.
        except timeout as e:
            print("INFO: Ping timeout. {}".format(e))
            print("INFO: Quitting.")
            sys.exit(1)
        except OSError as e:
            print("INFO: OSError. {}".format(e))
            print("INFO: Quitting.")
            sys.exit(1)


def parse_message(line_received):
    """Returns a dict of values extracted from a line sent by the sever.
    Values not found in the line default to None."""

    # return ping dict
    m = ping_message_pattern.match(line_received)
    if m is not None:
        return {'type': 'ping', 'content': m.group('content')}

    # return message dict
    m = message_pattern.match(line_received)
    if m is not None:
        return {'type': 'message', 'nick': m.group('nick'), 'recipient': m.group('recipient'),
                'content': m.group('content')}

    # return names dict
    m = rpl_names_pattern.match(line_received)
    if m is not None:
        return {'type': 'names', 'channel': m.group('channel'), 'names': m.group('names')}

    # return welcome dict
    m = rpl_welcome_pattern.match(line_received)
    if m is not None:
        return {'type': 'welcome'}

    # return join dict
    m = join_pattern.match(line_received)
    if m is not None:
        return {'type': 'join', 'nick': m.group('nick'), 'channel': m.group('channel')}

    # return part dict
    m = part_pattern.match(line_received)
    if m is not None:
        return {'type': 'part', 'nick': m.group('nick'), 'channel': m.group('channel')}

    # return nick dict
    m = nick_pattern.match(line_received)
    if m is not None:
        return {'type': 'nick', 'old': m.group('oldnick'), 'new': m.group('newnick')}

    # return topic dict
    m = rpl_topic_pattern.match(line_received)
    if m is not None:
        return {'type': 'topic'}

    # return nick conflict dict
    if rpl_nick_conflict_pattern.match(line_received) is not None:
        return {'type': 'conflict'}

    m = skiplines_notice_pattern.match(line_received)
    if m is not None:
        return {'type': 'skiplines', 'channel': m.group('channel'), 'num_skips': int(m.group('num_skips'))}

    # return ERROR dict
    m = error_pattern.match(line_received)
    if m is not None:
        return {'type': 'error', 'content': m.group('content')}

    # return empty dict if no pattern is matched
    return {'type': None}


def opsec_enabled(reply_to):
    """Returns True if reply_to is a channel or user with permissions.
       A user with permissions is present in at least one channel with permissions.
    """
    if reply_to.startswith('#'):
        if reply_to in settings.IRC_PROTECTEDCHANNELS:
            return True
    else:
        for channel in settings.IRC_PROTECTEDCHANNELS:
            if reply_to in irc.names[channel]:
                return True
    return False


def time_trigger(reply_to, message):
    """Responds to .time with human friendly UTC date/time."""
    if re.match(time_pattern, message['content']) is not None:
        irc.privmsg(reply_to, 'UTC {}'.format(datetime.utcnow().strftime("%A %B %d, %Y - %H:%M%p")))


def uplad_time_trigger(reply_to, message):
    """Responds to .upladtime with ISO-8601 format UTC time."""
    if re.match(upladtime_pattern, message['content']) is not None:
        irc.privmsg(reply_to, 'UTC {}'.format(datetime.utcnow().isoformat()))


def url_trigger(reply_to, message):
    """Responds to urls pasted into chat by announcing the title of the page they link to."""
    url_args = re.findall(url_pattern, message['content'])
    if len(url_args) > 0:
        for url_message in url.get_url_titles(url_args):
            irc.privmsg(reply_to, url_message)


def help_trigger(reply_to, message, full_help=False):
    """Handles the .help command.
    """
    if re.match(help_pattern, message['content']) is not None:
        irc.privmsg(reply_to, '.jita, .amarr, .dodixie, .rens, .hek, .time, .upladtime')
        if full_help:
            irc.privmsg(reply_to, '.ops, .addop, .rmop')


def ops_trigger(reply_to, message):
    """Handles the .ops command. Responds with a list of times remaining until events."""
    if re.match(ops_pattern, message['content']) is not None:
        for event_message in countdown.get_countdown_messages():
            irc.privmsg(reply_to, event_message)


def addop_trigger(reply_to, message):
    """Adds an event to the event list given a datetime, name or timer, name pair."""
    usage_hint = 'Usage: .addop <year>-<month>-<day>@<hour>:<minute> <name> | <days>d<hours>h<minutes>m <name>'
    if re.match(r'^[.]addop(.+)?$', message['content']) is not None:
        # datetime format arg
        m = re.match(addop_pattern, message['content'])
        if m is not None:
            if countdown.add_datetime(m):
                irc.privmsg(reply_to, 'Event added.')
            else:
                irc.privmsg(reply_to, usage_hint)

        else:
            # ref timer format arg
            m = re.match(addtimer_pattern, message['content'])
            if m is not None:
                if countdown.add_timer(m):
                    irc.privmsg(reply_to, 'Event added.')
                else:
                    irc.privmsg(reply_to, usage_hint)
            else:
                irc.privmsg(reply_to, usage_hint)


def rmop_trigger(reply_to, message):
    """Handles the .rmop command. Executes in reversed sorted order to protect users from themselves."""
    usage_hint = 'Usage: .rmop <op number>'
    if re.match(r'^[.]rmop(.+)?', message['content']) is not None:
        m = re.match(rmop_pattern, message['content'])
        if m is not None:
            reply_messages = countdown.remove_event(m.group('rmop_args'))
            for reply_message in reply_messages:
                irc.privmsg(reply_to, reply_message)
        else:
            irc.privmsg(reply_to, usage_hint)


def price_check_trigger(reply_to, message):
    """Responds to .jita, .amarr, etc with a price check against the eve_c api."""
    m = price_check_pattern.match(message['content'])
    if m is not None:
        group = m.groups()
        if reply_to.startswith('#'):
            for price_message in pricecheck.get_price_messages(group[1].split('; '), group[0]):
                irc.privmsg(reply_to, price_message)
        else:
            for price_message in pricecheck.get_price_messages(group[1].split('; '), group[0], 50):
                irc.privmsg(reply_to, price_message)


def pidgin_notice_trigger(reply_to, message):
    """Responds to channel notices sent by pidgin's IRC plugin with a proper channel notice."""
    m = pidgin_notice_pattern.match(message['content'])
    if m is not None:
        if message['recipient'].startswith('#'):
            irc.notice(reply_to, m.group('content'))


def handle_triggers(reply_to, message):
    """Checks a message against all possible triggers, respects channel permissions with opsec_enabled."""
    # detect/set skiplines here
    time_trigger(reply_to, message)
    uplad_time_trigger(reply_to, message)
    url_trigger(reply_to, message)
    price_check_trigger(reply_to, message)
    pidgin_notice_trigger(reply_to, message)
    if opsec_enabled(reply_to):
        help_trigger(reply_to, message, full_help=True)
        ops_trigger(reply_to, message)
        addop_trigger(reply_to, message)
        rmop_trigger(reply_to, message)
    else:
        help_trigger(reply_to, message)


# pull settings from external module
# connect to server
irc = IrcSocket()
irc.connect((settings.IRC_HOST, settings.IRC_PORT))
irc.user(settings.IRC_USERNAME, settings.IRC_HOSTNAME, settings.IRC_SERVERNAME, settings.IRC_REALNAME)
irc.nick(settings.IRC_NICKNAME)

# skiplines tracker
skiplines = {channel: 0 for channel in settings.IRC_CHANNELS}


# main bot loop
while True:
    for line_received in lines_from_socket(irc.sock):
        # get message dict
        print('RECV: ' + repr(line_received))
        message = parse_message(line_received)
        print('INFO: message = ' + repr(message))

        # respond to PING with PONG
        if message['type'] == 'ping':
            irc.pong(message['content'])

        # join channels after RPL_WELCOME
        if message['type'] == 'welcome':
            for channel in settings.IRC_CHANNELS:
                irc.join(channel)

            # if operator user/pass is set try to /OPER
            if settings.IRC_OPERUSER is not None and settings.IRC_OPERPASS is not None:
                irc.oper(settings.IRC_OPERUSER, settings.IRC_OPERPASS)

        # set skiplines if encounter replay notice
        if message['type'] == 'skiplines':
            skiplines[message['channel']] = message['num_skips']
            print('INFO: Updated skiplines.')
            print('INFO: skiplines = ' + repr(skiplines))

        # set names upon joining channel
        if message['type'] == 'names':
            irc.set_names(message['channel'], message['names'])

        # add/remove names upon observing join/part/nick
        if message['type'] == 'join':
            irc.name_joined(message['channel'], message['nick'])

        if message['type'] == 'part':
            irc.name_parted(message['channel'], message['nick'])

        if message['type'] == 'nick':
            irc.nick_changed(message['old'], message['new'])

        # disconnect and exit if nick is taken or server sends an ERROR message
        if message['type'] == 'conflict':
            irc.disconnect()
            sys.exit(0)

        if message['type'] == 'error':
            irc.disconnect()
            sys.exit(1)

        # skip topic lines
        if message['type'] == 'topic':
            # do nothing with topics for now
            pass

        # respond commands in chat or pm
        if message['type'] == 'message':
            if message['recipient'] == settings.IRC_NICKNAME:
                handle_triggers(message['nick'], message)
            else:
                if skiplines[message['recipient']] > 0:
                    print('INFO: Skipping line.')
                    skiplines[message['recipient']] -= 1
                    print('INFO: skiplines = ' + repr(skiplines))
                else:
                    handle_triggers(message['recipient'], message)