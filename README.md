# bot-tooper
## A chat bot for Eve-Online corps

### Features:
- Supports XMPP and IRC
- Respond to commands in channel or private message
- Connect and listen in multiple channels
- Text-mode timerboard for events
- Text-mode towerboard for organizing siphon checks
- Price check with the 5 major trade hubs
- UTC (eve) time in user-friendly or ISO format
- Attempts to fetch and report page titles for http(s): links in chat

### Requires:
- Python 2.7.x
- beautifulsoup4
- sleekxmpp
- pony
- requests
- expiringdict

### Setup:
1. Open sample-settings.py in your favorite text editor.
2. Follow the directions in the comments
3. Run 'python irc-bot.py' for IRC or 'python jabber-bot.py' for XMPP