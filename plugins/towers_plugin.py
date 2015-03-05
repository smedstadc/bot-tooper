"""
Commands to retrieve the last datetime that towers were checked for a siphon.
"""

import pony.orm
import datetime
import os

database_path = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), 'db', 'towers_plugin.sqlite'))
db = pony.orm.Database("sqlite", database_path, create_db=True)


def init_plugin(trigger_map, database=db):
    # Maps model classes to tables and creates tables if they don't exist
    database.generate_mapping(create_tables=True)
    pony.orm.sql_debug(False)
    trigger_map.map_command(".addtower", add_tower)
    trigger_map.map_command(".rmtower", remove_tower)
    trigger_map.map_command(".towers", get_tower_messages)
    trigger_map.map_command(".marktower", mark_checked)


class Tower(db.Entity):
    """
    Pony ORM model for Tower table.
    """
    name = pony.orm.Required(unicode)
    last_siphon_check = pony.orm.Optional(datetime.datetime)


def add_tower(tower_name=None):
    """
    Adds a tower if it doesn't already exist.
    Returns a string reply value.
    """
    if tower_name:
        tower_name = tower_name.upper().strip()
        with pony.orm.db_session:
            if not Tower.get(name=tower_name):
                Tower(name=tower_name)
                return ['Tower added.']
            else:
                return ["A tower named '{}' already exists.".format(tower_name)]
    else:
        return ["Usage: .addtower <tower_name>"]


def remove_tower(tower_id_to_remove=None):
    """
    Removes a tower if it exists.
    Returns a string reply value.
    """
    usage_hint = ["Usage: .rmtower <tower_id>"]
    if tower_id_to_remove:
        with pony.orm.db_session:
            try:
                tower = Tower.get(id=tower_id_to_remove)
            except ValueError:
                return usage_hint

            if tower is not None:
                removed_id = tower.id
                removed_name = tower.name
                tower.delete()
                return ["Removed: '{}' (ID: {}).".format(removed_name, removed_id)]
            else:
                return ["Tower ID: {} doesn't exist and cannot be removed.".format(tower_id_to_remove)]
    else:
        return usage_hint


def mark_checked(tower_id_to_check=None):
    """
    Sets a tower's last_siphon_checked value to utcnow() if it exists.
    Returns a string reply value.
    """
    usage_hint = ["Usage: .marktower <tower_id>"]
    if tower_id_to_check:
        with pony.orm.db_session:
            try:
                tower = Tower.get(id=tower_id_to_check)
            except ValueError:
                return usage_hint

            if tower is not None:
                tower.last_siphon_check = datetime.datetime.utcnow()
                return ["{} marked as checked on {}.".format(tower.name,
                                                             tower.last_siphon_check.strftime("%b %d at %H:%M UTC"))]
            else:
                return ["Tower ID: {} doesn't exist and cannot be marked as checked.".format(tower_id_to_check)]
    else:
        return usage_hint


def get_tower_messages():
    """
    Returns a list of tower messages.
    Returns a list of strings.
    """
    reply_messages = []
    with pony.orm.db_session:
        towers = Tower.select().order_by(Tower.last_siphon_check)
        if len(towers) > 0:
            for tower in towers:
                if tower.last_siphon_check is None:
                    reply_messages.append("{} never checked (ID: {})".format(tower.name, tower.id))
                else:
                    reply_messages.append("{} checked on {} (ID: {})".format(tower.name,
                                                                    tower.last_siphon_check.strftime("%b %d at %H:%M UTC"),
                                                                    tower.id))
            reply_messages.append("It is now {}".format(datetime.datetime.utcnow().strftime("%b %d at %H:%M UTC")))
            return reply_messages
        else:
            reply_messages.append("Not tracking any towers yet.")
            return reply_messages
