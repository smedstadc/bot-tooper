# Setup:
# 1. Create a copy of this file with the name 'settings.py' in the same directory as bot.py
# 2. Edit each value to match your desired settings.
# 3. Run the bot (ex: python3 bot.py)

# Change this if you re-name the static data export
DB_FILENAME = 'sqlite-latest.sqlite'

# IRC SETTINGS
IRC_HOST = 'irc.nosperg.com'
IRC_PORT = 6667  # default IRC port is 6667, but your specific server may be different
IRC_NICKNAME = 'test_tooper' #  Can't be taken by someone else on the server.
IRC_USERNAME = 'test'
IRC_HOSTNAME = 'test'
IRC_SERVERNAME = 'test'
IRC_REALNAME = 'test_fucking_tooper'
IRC_PASSWORD = ''  # IRC AUTH SUPPORT NOT YET IMPLEMENTED THIS DOES NOTHING
IRC_OPERUSER = None  # Required if the bot has oper privs for spam/kick/ban/mode on any channels
IRC_OPERPASS = None  # ^
IRC_CHANNELS = ['#test1']  # list of channels for the bot to join
IRC_PROTECTEDCHANNELS = ['']

# XMPP/JABBER SETTINGS
XMPP_JID = ''
XMPP_PASSWORD = ''
XMPP_ROOM = ''
XMPP_NICK = ''
XMPP_LOG_LEVEL = ''