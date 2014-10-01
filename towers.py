"""
Enables commands to retrieve the last datetime that towers were checked for a siphon.
"""

import pony.orm
import datetime

##### SET DB #####
db = pony.orm.Database("sqlite", "towers.sqlite", create_db=True)


##### MODELS #####
class Tower(db.Entity):
    """
    Pony ORM model for Tower table.
    """
    name = pony.orm.Required(unicode)
    last_siphon_check = pony.orm.Optional(datetime.datetime)


##### MAP MODELS TO DB AND CREATE TABLES UNLESS THEY EXIST #####
db.generate_mapping(create_tables=True)


##### ENABLE/DISABLE DEBUG #####
pony.orm.sql_debug(False)


##### TOWER METHODS #####
def add_tower(tower_name):
    """
    Adds a tower if it doesn't already exist.
    Returns a string reply value.
    """
    tower_name = tower_name.upper().strip()
    with pony.orm.db_session:
        if Tower.get(name=tower_name) is None:
            Tower(name=tower_name)
            return ["Added: '{}'".format(tower_name)]
        else:
            return ["'{}' already exists.".format(tower_name)]


def remove_tower(tower_name):
    """
    Removes a tower if it exists.
    Returns a string reply value.
    """
    tower_name = tower_name.upper().strip()
    with pony.orm.db_session:
        tower = Tower.get(name=tower_name)
        if tower is not None:
            tower.delete()
            return ["Removed: '{}'".format(tower_name)]
        else:
            return ["'{}' doesn't exist to delete.".format(tower_name)]


def mark_checked(tower_name):
    """
    Sets a tower's last_siphon_checked value to utcnow() if it exists.
    Returns a string reply value.
    """
    tower_name = tower_name.upper().strip()
    with pony.orm.db_session:
        tower = Tower.get(name=tower_name)
        if tower is not None:
            tower.last_siphon_check = datetime.datetime.utcnow()
            return ["{} marked as checked on {}.".format(tower_name,
                                                        tower.last_siphon_check.strftime("%b %d at %H:%M UTC"))]
        else:
            return ["'{}' doesn't exist to mark.".format(tower_name)]


def get_tower_messages():
    """
    Returns a list of tower messages.
    Returns a list of strings.
    """
    reply_messages = []
    with pony.orm.db_session:
        towers = pony.orm.select(tower for tower in Tower)
        if len(towers) > 0:
            for tower in towers:
                if tower.last_siphon_check is None:
                    reply_messages.append("{} never checked.".format(tower.name))
                else:
                    reply_messages.append("{} checked on {}".format(tower.name,
                                                                    tower.last_siphon_check.strftime("%b %d at %H:%M UTC")))
            reply_messages.append("It is now {}".format(datetime.datetime.utcnow().strftime("%b %d at %H:%M UTC")))
            return reply_messages
        else:
            reply_messages.append("Not tracking any towers yet.")
            return reply_messages


##### TEST #####
if __name__ == "__main__":
    pass