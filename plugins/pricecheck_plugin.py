""" pricecheck.py
    Checks the eve-central api marketdata for a given item name and returns price message strings.

"""
import requests
import sqlite3
import json
from expiringdict import ExpiringDict
import os


database_path = os.path.join(os.getcwd(), 'db', 'sqlite-latest.sqlite')
marketstat_cache = ExpiringDict(max_len=100, max_age_seconds=1800)


def init_plugin(trigger_map):
    trigger_map.map_command(".jita", check_jita)
    trigger_map.map_command(".amarr", check_amarr)
    trigger_map.map_command(".dodixie", check_dodixie)
    trigger_map.map_command(".hex", check_hek)
    trigger_map.map_command(".rens", check_rens)


def check_jita(item=None):
    return get_price_messages(item, 'jita')


def check_amarr(item=None):
    return get_price_messages(item, 'amarr')


def check_dodixie(item=None):
    return get_price_messages(item, 'dodixie')


def check_hek(item=None):
    return get_price_messages(item, 'hek')


def check_rens(item=None):
    return get_price_messages(item, 'rens')


def get_price_messages(item_name, system_name):
    if item_name:
        messages = ["Sorry, I can't find {} on the market.".format(item_name)]
        type_ids = get_type_ids(item_name)
        type_names = get_type_names(*type_ids)
        marketstat_json = get_marketstat_json(get_solar_system_id(system_name), type_ids)
        if marketstat_json is not None:
            messages = []
            for item_json in marketstat_json:
                messages.append(get_message_string(item_json, type_names))
        messages = trim_responses(messages)
        return messages
    else:
        return ["Usage: .jita|amarr|dodixie|hek|rens <item_name>"]


def get_marketstat_json(system_id, type_ids):
    if len(type_ids) > 0:
        request_url = get_marketstat_request_url(system_id, type_ids)
        response = marketstat_cache.get(request_url)
        if response is not None:
            return json.loads(response)
        else:
            try:
                response = requests.get(request_url, headers={'User-agent': 'Mozilla/5.0'},
                                        allow_redirects=True, verify=False)
                if response.status_code == 200:
                    marketstat_cache[request_url] = response.content
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


def get_marketstat_request_url(system_id, type_ids):
    url = ['http://api.eve-central.com/api/marketstat/json?typeid={}'.format(str(type_ids[0]))]
    if len(type_ids) > 1:
        for typeid in type_ids[1:]:
            url.append('&typeid={}'.format(typeid))
    url.append('&usesystem={}'.format(system_id))
    request_url = ''.join(url)
    return request_url


def get_message_string(item_json, type_names):
    return '{}, sell: {:,.2f}, buy: {:,.2f}, volume: {:,}'.format(
        type_names[item_json["all"]["forQuery"]["types"][0]],
        item_json["sell"]["min"],
        item_json["buy"]["max"],
        item_json["all"]["volume"])


def trim_responses(responses):
    if len(responses) >= 10:
        num_extra = len(responses[9:])
        first_nine = responses[:9]
        first_nine.append("...and {} more lines. Try a narrower search term?".format(num_extra))
        return first_nine
    else:
        return responses


def get_type_ids(item_name):
    if len(item_name) > 3:
        query_string = "SELECT typeID " \
                       "FROM invTypes WHERE " \
                       "typeName LIKE ? " \
                       "AND typeName NOT LIKE '% blueprint'" \
                       "AND marketGroupID NOT NULL " \
                       "AND published = 1"
        # try to find an exact match first
        result = get_cursor().execute(query_string, (item_name,)).fetchall()
        if result:
            return [row[0] for row in result]
        # otherwise return partial matches
        result = get_cursor().execute(query_string, ("%" + item_name + "%",)).fetchall()
        return [row[0] for row in result]
    else:
        return []


def get_type_names(*type_ids):
    query_string = "SELECT typeId, typeName " \
                   "FROM invTypes " \
                   "WHERE typeId IN {}".format(_wildcards(type_ids))

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
    return '({})'.format(','.join(['?']*len(args)))
