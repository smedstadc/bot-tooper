#!/usr/bin/env python3
""" countdown.py
    Stores events and returns the time remaining until those events when asked.

"""

from datetime import datetime

events = []


def write_timers():
    """Writes currently tracked timers to text file. Called by add_event after each timer is added."""
    try:
        global events
        with open('timers.txt', 'w') as file:
            for event in events:
                dt = event[0]
                name = event[1]
                file.write('{};{};{};{};{};{}\n'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, name))
    except IOError:
        print('Problem writing timers.txt')


def add_event(adatetime, aname):
    """Appends a (datetime, name) tuple to a list of events then sorts it by datetime order"""
    global events
    if aname == '':
        aname = 'Nameless Mystery Timer'
    event = (adatetime, aname)
    events.append(event)
    events = sorted(events, key=lambda list_item: list_item[0])
    write_timers()


def remove_event(event_number):
    """Deletes an event at event_index and returns a message to the bot."""
    global events
    try:
        event_number = int(event_number[0])
        removed_event_name = events[event_number - 1][1]
        del events[event_number - 1]
        write_timers()
        return 'Removed event #{}: "{}".'.format(event_number, removed_event_name)
    except IndexError:
        return 'No event #{} to remove.'.format(event_number)
    except ValueError:
        return 'Invalid event number.'


def days_hours_minutes(adelta):
    """Returns the value of a time delta as days, hours and minutes."""
    return adelta.days, adelta.seconds // 3600, (adelta.seconds // 60) % 60


# TODO Factor out expiration logic to re-use in remove function
def get_countdown_messages():
    """ Returns a list of messages reporting the time remaining or elapsed relative to each event in the event list.
        Events which have been expired for longer than 45 minutes will be removed from the list on the next .ops call.
        Calls write_timers() if the event list changes.

    """
    global events
    messages = []
    if len(events) == 0:
        messages.append("Zero upcoming events.")
    else:
        count = 0
        for event in events:
            name = event[1]
            time_delta = event[0] - datetime.utcnow()
            if time_delta.total_seconds() > 0:
                delta = days_hours_minutes(time_delta)
                count += 1
                messages.append(
                    '{0}: {1:2}d {2:2}h {3:2}m until \"{4}\" @ {5} UTC'.format(count, delta[0], delta[1], delta[2],
                                                                               name.upper(),
                                                                               event[0].strftime("%Y-%m-%dT%H:%M")))
            else:
                minutes_elapsed = abs(time_delta.total_seconds()) // 60
                if minutes_elapsed > 30:
                    events = events[1:]
                else:
                    count += 1
                    messages.append('{}: IT\'S HAPPENING: \"{}\"'.format(count, name))
    write_timers()
    return messages


def read_timers():
    """Reads saved timers into timers list from text file."""
    try:
        global events
        with open('timers.txt', 'r') as file:
            for line in file:
                line = line.split(';')
                # Is there simple a way to unpack a list of strings as ints?
                event = (
                    datetime(int(line[0]), int(line[1]), int(line[2]), int(line[3]), int(line[4])), line[5].strip())
                events.append(event)
        events = sorted(events, key=lambda list_item: list_item[0])
    except IOError:
        print("Problem reading timers.txt")


read_timers()