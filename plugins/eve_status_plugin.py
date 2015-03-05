"""A plugin to reports the status of Eve: Online game servers."""

import requests
from expiringdict import ExpiringDict
from lxml import etree
from collections import namedtuple

response_cache = ExpiringDict(max_len=100, max_age_seconds=180)
EveStatus = namedtuple('EveStatus', ['online', 'player_count'])


def init_plugin(command_map):
    command_map.map_command(".eve", get_tranquility_status_message)
    command_map.map_command(".sisi", get_singularity_status_message)


def get_tranquility_status_message():
    status = get_status('tranquility')
    if status:
        if status.online:
            return ["Tranquility is up with {:,} players online.".format(status.player_count)]
        else:
            return ["Tranquility is down."]
    else:
        return ["No response from Eve API."]


def get_singularity_status_message():
    status = get_status('singularity')
    if status:
        if status.online:
            return ["Singularity is up with {:,} players online.".format(status.player_count)]
        else:
            return ["Singularity is down."]
    else:
        return ["No response from Eve API."]


def get_status(servername):
    if servername == 'tranquility':
        response = get_api_response('https://api.eveonline.com/server/ServerStatus.xml.aspx')
    elif servername == 'singularity':
        response = get_api_response('https://api.testeveonline.com/server/ServerStatus.xml.aspx')
    else:
        raise ValueError("Servername should be in ['tranquility', 'singularity'] but was: {}".format(servername))
    if response:
        tree = etree.XML(response.content)
        return EveStatus(bool(tree.find('result/serverOpen').text), int(tree.find('result/onlinePlayers').text))
    else:
        return None


def get_api_response(url):
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
