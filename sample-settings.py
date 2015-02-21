# Setup:
# 1. Create a copy of this file with the name 'settings.py' in the same directory as bot.py
# 2. Edit each value to match your desired settings.
# 3. Run the bot (ex: python3 bot.py)

# Change this if you re-name the static data export
DBFILENAME = 'sqlite-latest.sqlite'

# IRC SETTINGS
IRC_HOST = 'irc.server.com'
IRC_PORT = 6667  # default IRC port is 6667, but your specific server may be different
IRC_NICKNAME = 'nickname' #  Can't be taken by someone else on the server.
IRC_USERNAME = 'username'
IRC_HOSTNAME = 'hostname'
IRC_SERVERNAME = 'servername'
IRC_REALNAME = 'realname'
IRC_PASSWORD = ''  # IRC AUTH SUPPORT NOT YET IMPLEMENTED THIS DOES NOTHING
IRC_OPERUSER = None  # Required if the bot has oper privs for spam/kick/ban/mode on any channels
IRC_OPERPASS = None  # ^
IRC_CHANNELS = ['#test1', '#test2', '#test3']  # list of channels for the bot to join
IRC_OPSEC = ['']  # list of channels allowed to use the timerboard feature

# XMPP/JABBER SETTINGS
XMPP_JID = ''
XMPP_PASSWORD = ''
XMPP_ROOM = ''
XMPP_NICK = ''
XMPP_LOG_LEVEL = ''