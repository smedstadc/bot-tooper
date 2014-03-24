#!/usr/bin/env python3
__author__ = 'Corey'

from socket import *
#from collections import deque
import time
import jita


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
servername = 'tnosperg'
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
time.sleep(3)
if DEBUG:
    print('waiting for PING before sending JOIN...')

# TODO: Alter message processing to use a queue.
# TODO: Refactor elements of the loop into functions so it will be easier to read & edit.
while True:
    # Read next 8kb from socket
    data_received = irc.recv(8192).decode('utf-8')

    # Process one chat line at a time.
    for message_line in data_received.split('\n'):
        if len(message_line.strip()) > 0:
            print(message_line)

        # Respond to pings from the server
        if message_line.find('PING') != -1:
            if DEBUG:
                print('PING received, sending pong...')
            msg = 'PONG ' + message_line.split(':')[1] + '\r\n'
            if DEBUG:
                print(msg)
            irc.send(msg.encode('utf-8'))

        # Join channels after registered with server.
        if message_line.find('NOTICE Auth :Welcome') != -1:
            if DEBUG:
                print('Greeting received. Joining channels.')
            join(bot_channel)

        # TODO add 30day argument to .jita
        # TRIGGER ".jita"
        jita_trigger = '.jita'
        if message_line.find(jita_trigger) != -1:
            if DEBUG:
                print('.jita command received, processing trigger...')
            jita_args = message_line[message_line.find(jita_trigger) + len(jita_trigger) + 1:].strip('\r\n').split('; ')
            if DEBUG:
                print(jita_args)
            messages = jita.get_price_messages(jita_args)

            for message in messages:
                chanmsg(bot_channel, message)
                time.sleep(.5)