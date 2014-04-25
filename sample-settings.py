# Setup:
# 1. Create a copy of this file with the name 'settings.py' in the same directory as bot-tooper.py
# 2. Edit each value to match your desired settings.
# 3. Run the bot (ex: python3 bot-tooper.py)

# server info
HOST = 'irc.server.com'
# default IRC port is 6667, but your specific server may be different
PORT = 6667

# NICKNAME is important to set to something which
# isn't already taken by another user connected to
# the server.
NICKNAME = 'nickname'
USERNAME = 'username'
HOSTNAME = 'hostname'
SERVERNAME = 'servername'
REALNAME = 'realname'
#PASSWORD SUPPORT NOT YET IMPLEMENTED
#PASSWORD = ''

# list of channels for the bot to join
# ex CHANNELS = ['#chan1', '#chan2', 'chan3']
CHANNELS = ['#test1', '#test2', '#test3']

# list of channels with permission to use trigger
# commands gated by OPSEC_ENABLED()
# timers with .ops .addop .addtimer and .rmop
# IF MULTIPLE CHANNELS SHOULD BE A LIST LIKE CHANNELS
# ex OPSEC = ['#test1', '#test2', '#test3']
# IF NO CHANNELS SHOULD HAVE PERMISSIONS USE
# OPSEC = ['']
OPSEC = ['']