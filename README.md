bot-tooper
==========

Bud Tooper's IRC bot for [T-S-K]

A simple IRC bot implemented in Python 3.

There are plenty of these already that I could 
have re-used or extended, but I chose to implement 
my own to see what I could learn. So far so good.

As a bot for an Eve corp, it's functionality is
mostly eve related.

Currently the only feature is the bot will respond
to the command ".jita <argument(s)>" by sending
the channel the buy and sell prices for an item.

More features are planned after I polish the code
a bit. It's still a bit rough from gluing the initial
proof of concept bits together.

Current organization:
bot-tooper.py - is responsible for connecting to 
  irc and processing triggers.
jita.py - implements the jita price check methods
