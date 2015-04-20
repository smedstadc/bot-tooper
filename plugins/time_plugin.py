"""A plugin to report the current UTC time to users who ask."""

from datetime import datetime

def init_plugin(command_map):
    command_map.map_command(".time", utc_time)
    command_map.map_command(".upladtime", uplad_time)


def utc_time():
    return [datetime.utcnow().strftime("%A, %d. %B %Y %H:%M UTC")]


def uplad_time():
    return [datetime.utcnow().isoformat()]