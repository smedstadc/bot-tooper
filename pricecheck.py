#!/usr/bin/env python3
""" pricecheck.py
    Checks the eve-central api marketdata for a given item name and returns price message strings.

"""

# TODO Alter get_marketstat_xml to use requests

from settings import TYPEIDSFILENAME
import xml.etree.ElementTree as ET
#import urllib.request
import requests
import re
import os
import sys


if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

def typeids_from_csv(filename):
    """Returns a dict of {type_name : type_id} from a csv file ordered as type_id, type_name."""
    pairs = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                pairs.append(line.strip('\r\n').split(',', 1))
        return {type_name: type_id for type_id, type_name in pairs}
    except IOError:
        return {}


def get_matching_keys(partial):
    """Returns a list of keys that a partial string matches.
    :rtype : list
    """
    keys = []
    for key in typeid_dict.keys():
        if exact_match(key, partial):
            return [key]
        if re.search(partial, key, flags=re.IGNORECASE) is not None:
            keys.append(key)
    return keys


def exact_match(string, word):
    """Returns True if a string is an exact match for a given word.
       get_matching_keys calls this to prevent exact searches from
       returning too many related results ie: searches for 'tengu'
       intending that are only looking for the hull, rather than
       all subsystems.

       string: the string to be searched for a match

       word: the string to attempt to match
    """
    exact_match_pattern = r'^{}$'.format(word)
    res = re.search(exact_match_pattern, string, flags=re.IGNORECASE)
    return bool(res)


def get_price_messages(args, system_id, max_results=10):
    """Returns a list of message strings that will be sent by an IRC bot in response to a price check trigger."""
    messages = []
    for arg in args:
        names = get_matching_keys(re.escape(arg))
        if len(names) > max_results:
            messages.append('Too many results for \'{}\'. This limit is ignored in PMs.'.format(arg))
        else:
            typeids = []
            for name in names:
                typeids.append(typeid_dict[name])
            try:
                xml = get_marketstat_xml(typeids, solar_system_id[system_id])
                buy_max_prices = []
                sell_min_prices = []
                if xml is not None:
                    #xml = xml.getroot()
                    for item in xml.findall('marketstat/type'):
                        sell_min_prices.append(float(item.find('sell/min').text))
                        buy_max_prices.append(float(item.find('buy/max').text))

                    for name, sell, buy in zip(names, sell_min_prices, buy_max_prices):
                        messages.append('{}, sell: {:,.2f}, buy: {:,.2f}'.format(name, sell, buy))
                else:
                    messages.append('No results for {}.'.format(arg))
            except KeyError:
                messages.append('Could not find type_id for {}.'.format(arg))
    return messages


def get_marketstat_xml(typeids, system_id):
    """ Takes a list of typeids and makes a request to the eve-central
        marketstat API. Returns an XML element tree result of an eve-central
        marketstat api request.

        Returns an element tree from the XML retrieved if the request is successful.

        Returns None if request fails.
    """
    if len(typeids) > 0:
        endpoint = 'http://api.eve-central.com/api/marketstat'
        parameters = '?typeid={}'.format(str(typeids[0]))
        if len(typeids) > 1:
            for typeid in typeids[1:]:
                parameters += '&typeid={}'.format(typeid)
        parameters += '&usesystem={}'.format(system_id)
        request_url = endpoint + parameters
        print('INFO: ' + 'generated api request: {}'.format(request_url))
        try:
            response = requests.get(request_url, headers={'User-agent': 'Mozilla/5.0'}, allow_redirects=True, verify=False)
            print(response.content)
            xml = ET.fromstring(response.content)
        except IOError:
            xml = None
        except ET.ParseError:
            xml = None

    else:
        xml = None
    return xml


typeids_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), TYPEIDSFILENAME)
typeid_dict = typeids_from_csv(typeids_path)  # { type_name : type_id }
solar_system_id = {'amarr': '30002187',
                   'jita': '30000142',
                   'dodixie': '30002659',
                   'rens': '30002510',
                   'hek': '30002053'}