bot-tooper
==========

bot-tooper.py
an IRC Bot geared towards eve-corporations by Bud Tooper

Bot responds to:
.jita      - price check for one or more eve-items, accepts 
             partial names, multiple names separated by '; '
.time      - sends UTC time to chat in human-friendly format
.upladtime - sents ISO-8601 format UTC time to chat
.ops       - lists upcoming ops and countdown timers
.addop     - adds an event to the countdown list by datetime
.addtimer  - adds an event to the countdown list by timedelta
.rmop      - removes a timer from the countdown list
http://    - fetches the page title for any links pasted into 
             chat and displays them in order

I know there are plenty of irc and networking frameworks 
available to python, but I thought I could learn more by 
re-inventing the wheel. So far so good.

Basic functionality is working well, so the next job is to work
on generalizing the IRC handling bits so that in the future the
bot can do more than sit in one channel on one server at a time.
