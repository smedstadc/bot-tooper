from datetime import datetime


def init_plugin(command_dict):
    command_dict['.time'] = utc_time


def utc_time():
    return [datetime.utcnow().strftime("%A, %d. %B %Y %I:%M%p")]
