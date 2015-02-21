#!/usr/bin/env python2
""" pricecheck.py
    Checks the eve-central api marketdata for a given item name and returns price message strings.

"""
import requests
import os
import sys
import sqlite3
import json
import settings

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

database_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), settings.DB_FILENAME)


def get_price_messages(item_name, system_name, max_results=10):
    messages = []
    type_ids = get_type_ids(item_name)
    if len(type_ids) > max_results:
        messages.append('Too many results for \'{}\'. This limit is ignored in PMs.'.format(item_name))
    else:
        type_names = get_type_names(*type_ids)
        marketstat_json = get_marketstat_json(get_solar_system_id(system_name), type_ids)
        if marketstat_json is not None:
            for item_json in marketstat_json:
                messages.append('{}, sell: {:,.2f}, buy: {:,.2f}, volume: {:,}'.format(
                    type_names[item_json["all"]["forQuery"]["types"][0]],
                    item_json["sell"]["min"],
                    item_json["buy"]["max"],
                    item_json["all"]["volume"]))
    return messages


def get_marketstat_json(system_id, type_ids):
    if len(type_ids) > 0:
        url = ['http://api.eve-central.com/api/marketstat/json?typeid={}'.format(str(type_ids[0]))]
        if len(type_ids) > 1:
            for typeid in type_ids[1:]:
                url.append('&typeid={}'.format(typeid))
        url.append('&usesystem={}'.format(system_id))
        try:
            request_url = ''.join(url)
            response = requests.get(request_url, headers={'User-agent': 'Mozilla/5.0'}, allow_redirects=True, verify=False)
            if response.status_code == 200:
                return json.loads(response.content)
            elif response.status_code == 400:
                return None
        except IOError:
            print "Problem encountered with HTTP request."
            return None
        except ValueError:
            print "Problem encountered decoding JSON response."
            return None
    else:
        return None


def get_type_ids(item_name):
    if len(item_name) > 3:
        query_string = "SELECT typeID " \
                       "FROM invTypes WHERE " \
                       "typeName LIKE ? " \
                       "AND marketGroupID " \
                       "NOT NULL AND published = 1"
        result = get_cursor().execute(query_string, ("%" + item_name + "%",)).fetchall()
        return [row[0] for row in result]
    else:
        return []


def get_type_names(*type_ids):
    query_string = "SELECT typeId, typeName " \
                   "FROM invTypes " \
                   "WHERE typeId IN ({})".format(_wildcards(type_ids))

    return {row[0]: row[1] for row in get_cursor().execute(query_string, type_ids)}


def get_solar_system_id(solar_system_name):
    if len(solar_system_name) > 2:
        query_string = "SELECT solarSystemID " \
                       "FROM mapSolarSystems " \
                       "WHERE solarSystemName LIKE ? "
        try:
            return get_cursor().execute(query_string, (solar_system_name,)).fetchone()[0]
        except TypeError:
            return None
    else:
        return None


def get_cursor():
    return sqlite3.connect(database_path).cursor()


def _wildcards(args):
    return ','.join(['?']*len(args))


