# bot-tooper
## A chat bot geared towards Eve-Online corps.

### Features:
- Supports XMPP and IRC
- Respond to commands in channel or private message
- Connect and listen in multiple channels
- Limit certain commands to a list of privileged channels or members in those channels. (Very rough implementation ATM)
- Text-mode timerboard for events
- Price check with the 5 major trade hubs
- UTC (eve) time in user-friendly or ISO format
- Will attempt to fetch and report page titles for http(s): links in chat

### Requires:
- Python 2.7.x or 3.4.x
- beautifulsoup4 (pip install bs4)
- requests (pip install requests)
- sleekxmpp (pip install sleekxmpp)

### Setup:
1. Open sample-settings.py in your favorite text editor.
2. Follow the directions in the comments
3a. Run 'python irc-bot.py' for IRC
3b. Run 'python jabber-bot.py for XMPP

### Misc:
If the bot misbehaves or crashes please make a github account (it's painless) and report any issues you have [here](https://github.com/smedstadc/bot-tooper/). If you don't know what happened try piping the output to a text file and reading the last few lines.