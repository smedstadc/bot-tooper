import requests
from expiringdict import ExpiringDict
from lxml import etree
from collections import namedtuple

response_cache = ExpiringDict(max_len=100, max_age_seconds=180)
EveStatus = namedtuple('EveStatus', ['online', 'player_count'])


def init_plugin(command_dict):
    command_dict[".eve"] = get_status_message
    command_dict[".evestatus"] = get_status_message


def get_status_message():
    eve_status = get_eve_status()
    if eve_status:
        if eve_status.online:
            return ["Tranquility is up with {:,} players online.".format(eve_status.player_count)]
        else:
            return ["Tranquility is down."]
    else:
        return ["No response from Eve API."]


def get_eve_status():
    response = get_api_response()
    if response:
        tree = etree.XML(response.content)
        return EveStatus(bool(tree.find('result/serverOpen').text), int(tree.find('result/onlinePlayers').text))
    else:
        return None


def get_api_response():
    url = 'https://api.eveonline.com/server/ServerStatus.xml.aspx'
    response = response_cache.get(url)
    if response:
        return response
    else:
        response = requests.get(url)
        if response.status_code == 200:
            response_cache[url] = response
            return response
        else:
            return None