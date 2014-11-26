#!/usr/bin/env python3
"""
countdown.py
Stores events and returns the time remaining until those events when asked.
"""

import os
from datetime import datetime, timedelta
import re
import sys
import pony.orm

##### HOUSKEEPING #####
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

##### SET DB #####
db = pony.orm.Database("sqlite", "countdown.sqlite", create_db=True)


#### MODELS #####
class Event(db.Entity):
    """
    Pony ORM modelfor Event table.
    """
    event_id = pony.orm.PrimaryKey(int, auto=True)
    name = pony.orm.Required(unicode)
    date_time = pony.orm.Required(datetime)


##### MAP MODELS TO DB AND CREATE TABLES UNLESS THEY EXIST #####
db.generate_mapping(create_tables=True)


##### COUNTDOWN METHODS #####
def add_timer(match):
    date_time = (datetime.utcnow() + timedelta(days=int(match.group('days')),
                                               hours=int(match.group('hours')),
                                               minutes=int(match.group('minutes'))))

    name = match.group('name')
    add_event(date_time, name)
    return True


def add_datetime(match):
    date_time = datetime(int(match.group('year')),
                         int(match.group('month')),
                         int(match.group('day')),
                         int(match.group('hour')),
                         int(match.group('minute')))

    name = match.group('name')
    add_event(date_time, name)
    return True


def add_event(date_time, event_name):
    event_name = upper_preserving_urls(event_name)
    with pony.orm.db_session:
        Event(date_time=date_time, name=event_name)


def remove_event(event_id_to_remove):
    with pony.orm.db_session:
        event = Event.get(event_id=event_id_to_remove)
        if event is not None:
            removed_name = event.name
            removed_id = event.event_id
            event.delete()
            return ["Removed: {} (ID:{}).".format(removed_name, removed_id)]
        else:
            return ["Event ID:{} doesn't exist and cannot be removed.".format(event_id_to_remove)]


def days_hours_minutes(time_delta):
    """Returns the value of a time delta as days, hours and minutes."""
    return time_delta.days, time_delta.seconds // 3600, (time_delta.seconds // 60) % 60


def get_countdown_messages():
    """
    Returns a list of messages reporting the time remaining or elapsed relative to each event in the event list.
    Events which have been expired for longer than 45 minutes will be removed from the list on the next .ops call.
    Calls write_timers() if the event list changes.
    """
    with pony.orm.db_session:
        events = Event.order_by(Event.date_time)
        messages = []
        if len(events) > 0:
            for event in events:
                event_id = event.event_id
                name = event.name
                date_time = event.date_time
                time_delta = event.date_time - datetime.utcnow()
                if time_delta.total_seconds() > 0:
                    delta = days_hours_minutes(time_delta)
                    messages.append(
                        '{0:4}d {1:2}h {2:2}m until {3} at {4} UTC (ID:{5})'.format(delta[0],
                                                                                     delta[1],
                                                                                     delta[2],
                                                                                     name,
                                                                                     date_time.strftime
                                                                                     ("%Y-%m-%dT%H:%M"),
                                                                                     event_id))

                else:
                    minutes_elapsed = abs(time_delta.total_seconds()) // 60
                    if minutes_elapsed > 30:
                        Event[event_id].delete()
                    else:
                        messages.append('   IT\'S HAPPENING: \"{}\" (ID:{})'.format(name, event_id))

        else:
            messages.append("No upcoming events.")
        return messages


def upper_preserving_urls(string):
    """Returns an uppercase version of the given string, but preserves urls which may be case sensitive."""
    urls = re.findall(r'(https?://\S+)', string)
    string = re.sub(r'(https?://\S+)', '{}', string)
    return string.upper().format(*urls)


##### TEST #####
if __name__ == "__main__":
    # .addtimer <days>d<hours>h<minutes>m <name>
    addtimer_pattern = re.compile(
        r'^[.]addop (?P<days>\d{1,3})[dD](?P<hours>\d{1,2})[hH](?P<minutes>\d{1,2})[mM] (?P<name>.+)$')
    t1 = '.addop 1d2h3m first op'
    t2 = '.addop 2d4h6m second op'
    t3 = '.addop 3d6h9m third op'