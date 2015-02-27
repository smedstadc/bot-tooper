from datetime import datetime


def init_plugin(trigger_map):
    trigger_map.map_command(".time", utc_time)


def utc_time():
    return [datetime.utcnow().strftime("%A, %d. %B %Y %I:%M%p")]
