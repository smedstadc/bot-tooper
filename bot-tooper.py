__author__ = 'Corey'

from socket import *
#from collections import deque
import time
import jita


def command(cmd):
    irc.send(cmd.encode('utf-8'))


def join(a_channel):
    cmd = 'JOIN {}\r\n'.format(a_channel)
    print('Attempting to join {} '.format(a_channel))
    command(cmd)


def nick(a_nickname):
    cmd = 'NICK {}\r\n'.format(a_nickname)
    command(cmd)


def user(a_username, a_hostname, a_servername, a_realname):
    cmd = 'USER {} {} {} :{}\r\n'.format(a_username, a_hostname, a_servername, a_realname)
    command(cmd)


def privmsg(a_message):
    cmd = 'PRIVMSG {}\r\n'.format(a_message)
    command(cmd)


def chanmsg(channel, message):
    cmd = 'PRIVMSG {} :{}\r\n'.format(channel, message)
    command(cmd)


def passw(a_password):
    cmd = 'PASS {}\r\n'.format(a_password)
    command(cmd)

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
time.sleep(3)
if DEBUG:
    print('waiting for PING before sending JOIN...')

data_received = ""

# TODO: Alter message processing to use a queue.

while True:
    # Read next 8kb from socket
    data_received = irc.recv(8192).decode('utf-8') # if 8kb isn't enough definitely leftpop a queue

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

        # TRIGGER ".jita"
        jita_trigger = '.jita'
        if message_line.find(jita_trigger) != -1:
            if DEBUG:
                print('.jita command received, processing trigger...')
            jita_args = message_line[message_line.find(jita_trigger) + len(jita_trigger)+1:].split('; ')
            if DEBUG:
                print(jita_args)
            for arg in jita_args:
                chanmsg(bot_channel, jita.get_price_message(str(arg).lower().strip('\r\n')))
                time.sleep(1)