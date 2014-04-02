#!/usr/bin/env python3
""" bot-tooper.py
    IRC Bot geared towards eve-corporations.
    Written by Bud Tooper of The Suicide Kings

    Bot responds to:
    .jita   - price check for one or more eve-items, accepts partial names, multiple names separated by '; '
    .time   - sends UTC time to chat in human-friendly format
    .ops    - lists upcoming ops and countdown timers
    .addop  - adds an event to the list of upcoming events
    http:// - fetches the page title for any links pasted into chat and displays them in order

"""

from socket import *
#from collections import deque
import time
import jita
from url import get_url_titles
import re
from datetime import datetime
import eventcountdown


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

# connect / do the dance
irc = socket(AF_INET, SOCK_STREAM)
if DEBUG:
    print('connecting socket...')
irc.connect(ADDR)
time.sleep(1)
if DEBUG:
    print('sending NICK...')
nick(nickname)
time.sleep(1)
if DEBUG:
    print('sending USER...')
user(username, hostname, servername, realname)
time.sleep(1)
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

        # TRIGGER ".jita"
        jita_trigger = '.jita'
        if chat_line.find(jita_trigger) != -1:
            if DEBUG:
                print('.jita command received, processing trigger...')
            jita_args = chat_line[chat_line.find(jita_trigger) + len(jita_trigger) + 1:].strip('\r\n').split('; ')
            if DEBUG:
                print(jita_args)
            price_messages = jita.get_price_messages(jita_args)

            for message in price_messages:
                chanmsg(bot_channel, message)
                time.sleep(.5)

        # TRIGGER "http:"
        link_trigger = 'http'
        if chat_line.find(link_trigger) != -1:
            if DEBUG:
                print('link detected, processing trigger...')
            url_args = re.findall(r'(https?://\S+)', chat_line)
            if DEBUG:
                print(url_args)
            if len(url_args) > 0:
                link_messages = get_url_titles(url_args)
                for message in link_messages:
                    chanmsg(bot_channel, message)
                    time.sleep(.5)

        # TRIGGER ".time"
        time_trigger = '.time'
        if chat_line.find(time_trigger) != -1:
            time_message = 'UTC: {}'.format(datetime.utcnow().strftime("%A, %d. %B %Y %H:%M%p"))
            chanmsg(bot_channel, time_message)

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
                event_datetime = datetime.strptime(event_trigger_args[0], "%d/%m/%Y@%H:%M")
                event_name = event_trigger_args[1]
                eventcountdown.add_event(event_datetime, event_name)
                chanmsg(bot_channel, 'Event added.')
            except IndexError:
                chanmsg(bot_channel, 'Usage: .addop <day/month/year@hour:minute> <event name>')
                chanmsg(bot_channel, 'Example: .addop 29/5/2014@20:35 Clever Event Name')
            except ValueError:
                chanmsg(bot_channel, 'Usage: .addop <day/month/year@hour:minute> <event name>')
                chanmsg(bot_channel, 'Example: .addop 29/5/2014@20:35 Clever Event Name')

        # Trigger ".ops"
        ops_trigger = '.ops'
        if chat_line.find(ops_trigger) != -1:
            event_messages = eventcountdown.get_countdown_messages()
            for message in event_messages:
                chanmsg(bot_channel, message)
                time.sleep(.5)

        # Trigger "trooper"
        trooper_trigger = 'trooper'
        if chat_line.find(trooper_trigger) != -1:
            chanmsg(bot_channel, '^r')
irc.close()