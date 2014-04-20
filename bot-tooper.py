#!/usr/bin/env python3
""" bot-tooper.py
    an IRC Bot geared towards eve-corporations by Bud Tooper

    Bot responds to these commands sent to the channel it sits in:
    .jita      - price check for one or more eve-items, accepts partial names, multiple names separated by '; '
    .amarr     - as .jita, but for amarr
    .dodixie   - as .jita, but for dodixie
    .rens      - as .jita, but for rens
    .hek       - as .jita, but for hek
    .time      - sends UTC time to chat in human-friendly format
    .upladtime - sends ISO-8601 format UTC time to chat
    .ops       - lists upcoming ops and countdown timers
    .addop     - adds an event to the countdown list by datetime
    .addtimer  - adds an event to the countdown list by timedelta
    .rmop      - removes a timer from the countdown list
    http       - fetches the page title for any links pasted into chat and displays them in order

"""
#standard module imports
import re
from socket import *
from datetime import datetime, timedelta
from collections import deque

#custom module imports
import pricecheck
import url
import countdown

#import settings variables
import settings
## BEGIN example settings.py
# DEBUG = True
# HOST = 'irc.domain.com'
# PORT = 6667
# NICKNAME = 'bot_nickname'
# USERNAME = 'bot_username'
# HOSTNAME = 'bot_hostname'
# SERVERNAME = 'bot_server_name'
# REALNAME = 'real_name'
# CHANNEL = '#channel'
## END example settings.py


# TODO: Factor IRC stuff out of bot module.
def command(a_cmd):
    """Encodes a message to be sent to the IRC server."""
    irc.send(a_cmd.encode('utf-8'))


def join(a_channel):
    """Sends a JOIN command."""
    cmd = 'JOIN {}\n'.format(a_channel)
    print('Attempting to join {} '.format(a_channel))
    command(cmd)


def nick(a_nickname):
    """Sends a NICK command to the connected server."""
    cmd = 'NICK {}\n'.format(a_nickname)
    command(cmd)


def user(a_username, a_hostname, a_servername, a_realname):
    """Sends a USER command. (Important for registering with the server upon connecting.)"""
    cmd = 'USER {} {} {} :{}\n'.format(a_username, a_hostname, a_servername, a_realname)
    command(cmd)


def privmsg(a_message):
    """Sends a PRIVMSG command."""
    cmd = 'PRIVMSG {}\n'.format(a_message)
    command(cmd)


def chanmsg(a_channel, a_message):
    """Like privmsg(), but takes a channel as an argument."""
    cmd = 'PRIVMSG {} :{}\n'.format(a_channel, a_message)
    command(cmd)


def passw(a_password):
    """Sends a PASS command."""
    cmd = 'PASS {}\n'.format(a_password)
    command(cmd)


def price_check_helper(line, trigger, hub):
    """Helper function that executes a price check for the different system triggers.

       line: string, the chat line which triggered the price check

       trigger: string, the trigger string for the price check

       hub: string, used as a key to retrieve the solar system id needed to build the api request
    """
    if settings.DEBUG:
        print('{} price check command received, processing trigger...'.format(hub))
    args = line[line.find(trigger) + len(trigger):].strip('\r\n').split('; ')
    if settings.DEBUG:
        print(args)
    price_messages = pricecheck.get_price_messages(args, '{}'.format(hub))
    for price_message in price_messages:
        chanmsg(settings.CHANNEL, price_message)

# TODO implement support for multiple channels
# TODO implement proper logging instead of if settings.DEBUG = TRUE: print() calls.
# connect / do the dance
try:
    irc = socket(AF_INET, SOCK_STREAM)
except socket.error:
    print('failed to open socket...')
    sys.exit(1)
if settings.DEBUG:
    print('connecting socket...')
irc.connect((settings.HOST, settings.PORT))
if settings.DEBUG:
    print('sending NICK...')
nick(settings.NICKNAME)
if settings.DEBUG:
    print('sending USER...')
user(settings.USERNAME, settings.HOSTNAME, settings.SERVERNAME, settings.REALNAME)
if settings.DEBUG:
    print('waiting for PING before sending JOIN...')

# TODO: Alter message processing to use a queue and support channels, pms (25% done)
# TODO: Factor trigger elements of the loop out into functions for readability
received_queue = deque()
skiplines = None  # Replaying up to 15 lines of pre-join history spanning up to 86400 seconds
while True:
    # Read up to 8kb from socket into the queue
    print('Update received queue...')
    for message in irc.recv(8192).decode('utf-8', 'ignore').split('\n'):
        if len(message) > 0:
            received_queue.append(message)
    # get the next chat line
    while len(received_queue) > 0:
        chat_line = received_queue.popleft()
        if settings.DEBUG:
            print(chat_line)
        # Respond to pings from the server
        if chat_line.find('PING') != -1:
            msg = 'PONG ' + chat_line.split(':')[1] + '\n'
            if settings.DEBUG:
                print(msg)
            irc.send(msg.encode('utf-8'))

        # Join channels after registered with server.
        if re.search(r'NOTICE Auth :Welcome', chat_line) is not None:
            if settings.DEBUG:
                print('Registered... Joining channels...')
            join(settings.CHANNEL)

        replay_match = re.search(r'NOTICE {} :Replaying up to ([0-9]|1[0-9]) lines'.format(settings.CHANNEL), chat_line)
        if replay_match is not None:
            skiplines = int(replay_match.groups()[0])

        if skiplines is not None:
            if skiplines > 0:
                skiplines -= 1
                print('Ignoring replay line #{}.'.format(skiplines+1))
            else:
                skiplines = None
        elif re.search(r'332 {} {}'.format(settings.NICKNAME, settings.CHANNEL), chat_line) is not None:
            pass  # don't trigger off channel topics
        else:
            # TRIGGER ".jita"
            jita_trigger = '.jita '
            if chat_line.find(jita_trigger) != -1:
                price_check_helper(chat_line, jita_trigger, 'Jita')

            # TRIGGER ".amarr"
            amarr_trigger = '.amarr '
            if chat_line.find(amarr_trigger) != -1:
                price_check_helper(chat_line, amarr_trigger, 'Amarr')

            # TRIGGER ".dodixie"
            dodixie_trigger = '.dodixie '
            if chat_line.find(dodixie_trigger) != -1:
                price_check_helper(chat_line, dodixie_trigger, 'Dodixie')

            # TRIGGER ".rens"
            rens_trigger = '.rens '
            if chat_line.find(rens_trigger) != -1:
                price_check_helper(chat_line, rens_trigger, 'Rens')

            # TRIGGER ".hek"
            hek_trigger = '.hek '
            if chat_line.find(hek_trigger) != -1:
                price_check_helper(chat_line, hek_trigger, 'Hek')

            # TRIGGER "http:"
            url_pattern = re.compile(r'(https?://\S+)')
            url_args = re.findall(r'(https?://\S+)', chat_line)
            if len(url_args) > 0:
                if settings.DEBUG:
                    print('link detected, processing trigger...')
                    print(url_args)
                link_messages = url.get_url_titles(url_args)
                for message in link_messages:
                    chanmsg(settings.CHANNEL, message)

            # TRIGGER ".time"
            time_pattern = re.compile(r'{} :[.]time\s\Z'.format(settings.CHANNEL))
            if re.search(time_pattern, chat_line) is not None:
                time_message = 'UTC: {}'.format(datetime.utcnow().strftime("%A, %d. %B %Y %H:%M%p"))
                chanmsg(settings.CHANNEL, time_message)

            # TRIGGER ".upladtime"
            upladtime_pattern = re.compile(r'{} :[.]upladtime\s\Z'.format(settings.CHANNEL))
            if re.search(upladtime_pattern, chat_line) is not None:
                upladtime_message = 'UTC: {}'.format(datetime.utcnow().isoformat())
                chanmsg(settings.CHANNEL, upladtime_message)

            # TODO convert .addop to regex
            # Trigger ".addop"
            addop_trigger = '.addop '
            if chat_line.find(addop_trigger) != -1:
                if settings.DEBUG:
                    print('event detected, processing trigger...')
                event_trigger_args = chat_line[chat_line.find(addop_trigger) + len(addop_trigger):]
                # Praise the PEP8
                event_trigger_args = event_trigger_args.strip('\r\n').split(' ', 1)
                if settings.DEBUG:
                    print(event_trigger_args)
                try:
                    event_datetime = datetime.strptime(event_trigger_args[0], "%Y/%m/%d@%H:%M")
                    event_name = event_trigger_args[1]
                    countdown.add_event(event_datetime, event_name)
                    chanmsg(settings.CHANNEL, 'Event added.')
                except IndexError:
                    chanmsg(settings.CHANNEL, 'Usage: .addop <year/month/day@hour:minute> <event name>')
                except ValueError:
                    chanmsg(settings.CHANNEL, 'Usage: .addop <year/month/day@hour:minute> <event name>')

            # Trigger ".addtimer"
            addtimer_trigger_pattern = re.compile(r'.addtimer')
            if re.search(addtimer_trigger_pattern, chat_line) is not None:
                if settings.DEBUG:
                    print('timer detected, processing trigger...')
                addtimer_pattern = re.compile(
                    r'{} :[.]addtimer ([0-3])[dD]([01]?[0-9]|2[0-3])[hH]([0-9]|[0-5][0-9])[mM]'.format(
                        settings.CHANNEL))

                addref_match = re.search(addtimer_pattern, chat_line)
                if settings.DEBUG:
                    print(addref_match)
                if addref_match is not None:
                    # found a match, add event via timedelta
                    delta_days = int(addref_match.groups()[0])
                    delta_hours = int(addref_match.groups()[1])
                    delta_minutes = int(addref_match.groups()[2])
                    timer_name = chat_line[addref_match.end():].strip()
                    timer_datetime = datetime.utcnow()+timedelta(days=delta_days,
                                                                 hours=delta_hours,
                                                                 minutes=delta_minutes)

                    try:
                        countdown.add_event(timer_datetime, timer_name)
                        chanmsg(settings.CHANNEL, 'Event added.')
                    except ValueError:
                        chanmsg(settings.CHANNEL, 'Usage: .addtimer <days>d<hours>h<minutes>m <timer name>')
                else:
                    # no match, provide a usage hint
                    chanmsg(settings.CHANNEL, 'Usage: .addtimer <days>d<hours>h<minutes>m <timer name>')

            # Trigger ".ops"
            ops_pattern = re.compile(r'{} :[.]ops\s\Z'.format(settings.CHANNEL))
            if re.search(ops_pattern, chat_line) is not None:
                event_messages = countdown.get_countdown_messages()
                for message in event_messages:
                    chanmsg(settings.CHANNEL, message)
                    # sleep(.5)

            # Trigger ".rmop"
            rmop_trigger_pattern = re.compile(r'.rmop')
            if re.search(rmop_trigger_pattern, chat_line) is not None:
                if settings.DEBUG:
                    print('remove op command detected, procesing trigger...')
                rmop_pattern = re.compile(r'{} :[.]rmop (\d+)'.format(settings.CHANNEL))
                rmop_match = re.search(rmop_pattern, chat_line)
                if rmop_match is not None:
                    rmop_arg = rmop_match.groups()[0]
                    if settings.DEBUG:
                        print(rmop_arg)
                    chanmsg(settings.CHANNEL, countdown.remove_event(rmop_arg))
                else:
                    chanmsg(settings.CHANNEL, 'Usage: .rmop <op number>')

            # Trigger ".help"
            help_pattern = re.compile(r'{} :[.]help\s\Z'.format(settings.CHANNEL))
            if re.search(help_pattern, chat_line) is not None:
                chanmsg(settings.CHANNEL, '.jita, .amarr, .dodixie, .rens, .hek')
                chanmsg(settings.CHANNEL, '.ops, .time, .upladtime')
                chanmsg(settings.CHANNEL, '.addop <year/month/day@hour:minute> <event name>')
                chanmsg(settings.CHANNEL, '.addtimer <#d#h#m> <timer name>')
                chanmsg(settings.CHANNEL, '.rmop <op number> (listed in .ops output)')
irc.close()