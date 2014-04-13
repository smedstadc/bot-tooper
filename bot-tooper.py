#!/usr/bin/env python3
""" bot-tooper.py
    IRC Bot geared towards eve-corporations.
    Written by Bud Tooper of The Suicide Kings

    Bot responds to:
    .jita   - price check for one or more eve-items, accepts partial names, multiple names separated by '; '
    .time   - sends UTC time to chat in human-friendly format
    .ops    - lists upcoming ops and countdown timers
    .addop  - adds an event to the list of upcoming events
    .rmop   - removes a countdowm timer by number shown by .ops
    http:// - fetches the page title for any links pasted into chat and displays them in order

"""
#standard module imports
from socket import *
from time import sleep
from re import findall, compile, search
from datetime import datetime, timedelta
#custom module imports
from jita import get_price_messages
from url import get_url_titles
from eventcountdown import get_countdown_messages, add_event, remove_event


# TODO: Factor IRC stuff out of bot module.
def command(a_cmd):
    """Encodes a string for transport over the socket and sends it as a command to the IRC server."""
    irc.send(a_cmd.encode('utf-8'))


def join(a_channel):
    """Sends a JOIN command."""
    cmd = 'JOIN {}\r\n'.format(a_channel)
    print('Attempting to join {} '.format(a_channel))
    command(cmd)


def nick(a_nickname):
    """Sends a NICK command."""
    cmd = 'NICK {}\r\n'.format(a_nickname)
    command(cmd)


def user(a_username, a_hostname, a_servername, a_realname):
    """Sends a USER command. (Important for registering with the server upon connecting.)"""
    cmd = 'USER {} {} {} :{}\r\n'.format(a_username, a_hostname, a_servername, a_realname)
    command(cmd)


def privmsg(a_message):
    """Sends a PRIVMSG command."""
    cmd = 'PRIVMSG {}\r\n'.format(a_message)
    command(cmd)


def chanmsg(a_channel, a_message):
    """Like privmsg(), but takes a channel as an argument."""
    cmd = 'PRIVMSG {} :{}\r\n'.format(a_channel, a_message)
    command(cmd)


def passw(a_password):
    """Sends a PASS command."""
    cmd = 'PASS {}\r\n'.format(a_password)
    command(cmd)

# TODO implement support for multiple channels
# TODO implement proper logging instead of if DEBUG = TRUE: print() calls.
# enable/disable debug print statements
DEBUG = True

# server info
HOST = 'irc.nosperg.com'
PORT = 6667
ADDR = (HOST, PORT)

# client info
nickname = 'bottooper'
username = 'bottooper'
hostname = 'nosperg'
servername = 'nosperg'
realname = 'tskbot'
bot_channel = '#tsk'

# Replaying up to 15 lines of pre-join history spanning up to 86400 seconds
#
REPLAY_LINES = 15
skiplines = None

# connect / do the dance
irc = socket(AF_INET, SOCK_STREAM)
if DEBUG:
    print('connecting socket...')
irc.connect(ADDR)
sleep(1)
if DEBUG:
    print('sending NICK...')
nick(nickname)
sleep(1)
if DEBUG:
    print('sending USER...')
user(username, hostname, servername, realname)
sleep(1)
if DEBUG:
    print('waiting for PING before sending JOIN...')

# TODO: Alter message processing to use a queue.
# TODO: Factor elements of the loop out into functions.
# TODO: Create .addevent trigger (validate dates with regex)
# TODO: Create .isotime for Uplad reference: https://en.wikipedia.org/wiki/ISO_8601
while True:
    # Read next 8kb from socket
    data_received = irc.recv(8192).decode('utf-8', 'replace')

    # Process one chat line at a time.
    for chat_line in data_received.split('\n'):
        if len(chat_line.strip()) > 0:
            print(chat_line)

        # Respond to pings from the server
        if chat_line.find('PING') != -1:
            if DEBUG:
                print('PING received, sending pong...')
            msg = 'PONG ' + chat_line.split(':')[1] + '\r\n'
            if DEBUG:
                print(msg)
            irc.send(msg.encode('utf-8'))

        # Join channels after registered with server.
        if chat_line.find('NOTICE Auth :Welcome') != -1:
            if DEBUG:
                print('Greeting received. Joining channels.')
            join(bot_channel)

        replay_match = search(r'NOTICE {} :Replaying up to ([0-9]|1[0-9]) lines'.format(bot_channel), chat_line)
        if replay_match is not None:
            skiplines = int(replay_match.groups()[0])

        if skiplines is not None:
            if skiplines > 0:
                skiplines -= 1
                print('Ignoring replay line #{}.'.format(skiplines+1))
            else:
                skiplines = None
        elif search(r'332 {} {}'.format(nickname, bot_channel), chat_line) is not None:
            pass  # don't trigger off channel topics
        else:
            # TRIGGER ".jita"
            jita_trigger = '.jita'
            if chat_line.find(jita_trigger) != -1:
                if DEBUG:
                    print('.jita command received, processing trigger...')
                jita_args = chat_line[chat_line.find(jita_trigger) + len(jita_trigger) + 1:].strip('\r\n').split('; ')
                if DEBUG:
                    print(jita_args)
                price_messages = get_price_messages(jita_args)

                for message in price_messages:
                    chanmsg(bot_channel, message)
                    # sleep(.5)

            # TRIGGER "http:"
            link_trigger = 'http'
            if chat_line.find(link_trigger) != -1:
                if DEBUG:
                    print('link detected, processing trigger...')
                url_args = findall(r'(https?://\S+)', chat_line)
                if DEBUG:
                    print(url_args)
                if len(url_args) > 0:
                    link_messages = get_url_titles(url_args)
                    for message in link_messages:
                        chanmsg(bot_channel, message)
                        # sleep(.5)

            # TRIGGER ".time"
            time_trigger = '.time'
            if chat_line.find(time_trigger) != -1:
                time_message = 'UTC: {}'.format(datetime.utcnow().strftime("%A, %d. %B %Y %H:%M%p"))
                chanmsg(bot_channel, time_message)

            # TRIGGER ".upladtime"
            upladtime_trigger = '.upladtime'
            if chat_line.find(upladtime_trigger) != -1:
                upladtime_message = 'UTC: {}'.format(datetime.utcnow().isoformat())
                chanmsg(bot_channel, upladtime_message)

            # Trigger ".addop"
            addop_trigger = '.addop'
            if chat_line.find(addop_trigger) != -1:
                if DEBUG:
                    print('event detected, processing trigger...')
                event_trigger_args = chat_line[chat_line.find(addop_trigger) + len(addop_trigger) + 1:]
                # Praise the PEP8
                event_trigger_args = event_trigger_args.strip('\r\n').split(' ', 1)
                if DEBUG:
                    print(event_trigger_args)
                try:
                    event_datetime = datetime.strptime(event_trigger_args[0], "%Y/%m/%d@%H:%M")
                    event_name = event_trigger_args[1]
                    add_event(event_datetime, event_name)
                    chanmsg(bot_channel, 'Event added.')
                except IndexError:
                    chanmsg(bot_channel, 'Usage: .addop <year/month/day@hour:minute> <event name>')
                except ValueError:
                    chanmsg(bot_channel, 'Usage: .addop <year/month/day@hour:minute> <event name>')

            # Trigger ".addtimer"
            timer_pattern = compile(r'.addtimer ([0-3])[dD]([01]?[0-9]|2[0-3])[hH]([0-9]|[0-5][0-9])[mM]')
            addref_trigger = '.addtimer'
            if chat_line.find(addref_trigger) != -1:
                if DEBUG:
                    print('timer detected, processing trigger...')
                addref_match = search(timer_pattern, chat_line)
                if DEBUG:
                    print(addref_match)
                if addref_match is not None:
                    # found a match, add event via timedelta
                    delta_days = int(addref_match.groups()[0])
                    delta_hours = int(addref_match.groups()[1])
                    delta_minutes = int(addref_match.groups()[2])
                    timer_name = chat_line[addref_match.end():].strip()
                    timer_datetime = datetime.utcnow()+timedelta(days=delta_days, hours=delta_hours, minutes=delta_minutes)
                    try:
                        add_event(timer_datetime, timer_name)
                        chanmsg(bot_channel, 'Event added.')
                    except ValueError:
                        chanmsg(bot_channel, 'Usage: .addtimer <days>d<hours>h<minutes>m <timer name>')
                else:
                    # no match, provide a usage hint
                    chanmsg(bot_channel, 'Usage: .addtimer <days>d<hours>h<minutes>m <timer name>')

            # Trigger ".ops"
            ops_trigger = '.ops'
            if chat_line.find(ops_trigger) != -1:
                event_messages = get_countdown_messages()
                for message in event_messages:
                    chanmsg(bot_channel, message)
                    # sleep(.5)

            # Trigger ".rmop"
            rmop_trigger = '.rmop'
            if chat_line.find(rmop_trigger) != -1:
                if DEBUG:
                    print('remove op command detected, procesing trigger...')
                rmop_trigger_args = chat_line[chat_line.find(rmop_trigger) + len(rmop_trigger) + 1:]
                rmop_trigger_args = rmop_trigger_args.strip('\r\n').split(' ', 1)
                if DEBUG:
                    print(rmop_trigger_args)
                chanmsg(bot_channel, remove_event(rmop_trigger_args))

            # Trigger ".help"
            help_trigger = '.help'
            if chat_line.find(help_trigger) != -1:
                chanmsg(bot_channel, '.jita, .ops, .time, .upladtime')
                chanmsg(bot_channel, '.addop <year/month/day@hour:minute> <event name>')
                chanmsg(bot_channel, '.addtimer <#d#h#m> <timer name>')
                chanmsg(bot_channel, '.rmop <op number> (listed in .ops output)')
irc.close()