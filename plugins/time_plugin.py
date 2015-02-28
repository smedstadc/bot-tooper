from datetime import datetime


def init_plugin(command_map):
    command_map.map_command(".time", utc_time)
    command_map.map_command(".upladtime", uplad_time)


def utc_time():
    return [datetime.utcnow().strftime("%A, %d. %B %Y %I:%M%p UTC")]


def uplad_time():
    return [datetime.utcnow().isoformat()]