#!/usr/bin/env python3
""" pricecheck.py
    Checks the eve-central api marketdata for a given item name and returns price message strings.

"""

# TODO Alter get_marketstat_xml to use requests

from xml.etree.ElementTree import parse
import urllib.request
import re


def typeids_from_csv(filename):
    """Returns a dict of {type_name : type_id} from a csv file ordered as type_id, type_name."""
    pairs = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                pairs.append(line.strip('\r\n').split(',', 1))
        return {type_name: type_id for type_id, type_name in pairs}
    except IOError:
        return {}


def get_matching_keys(partial):
    """Returns a list of keys that a partial string matches."""
    keys = []
    for key in typeid_dict.keys():
        if exact_match(key, partial):
            return [key]
        if re.match(partial, key, flags=re.IGNORECASE) is not None:
            if re.search('edition', key, flags=re.IGNORECASE) is not None:
                print('skipping key for painted hull not supported by evec_api...')
            else:
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


def get_price_messages(args, system_id):
    """Returns a list of message strings that will be sent by an IRC bot in response to a price check trigger."""
    messages = []
    for arg in args:
        names = get_matching_keys(arg)
        if len(names) > 15:
            messages.append('Too many partial matches for \'{}\'. Try to be more specific.'.format(arg))
        else:
            typeids = []
            for name in names:
                typeids.append(typeid_dict[name])
            try:
                xml = get_marketstat_xml(typeids, solar_system_id[system_id])
                buy_max_prices = []
                sell_min_prices = []
                if xml is not None:
                    xml = xml.getroot()
                    # find better way to do this
                    for child in xml[0]:
                        sell_min_prices.append(child[1][3].text)  # SELL MIN
                        buy_max_prices.append(child[0][2].text)  # BUY MAX
                    for index in range(len(names)):
                        messages.append('{}, sell: {:,.2f}, buy: {:,.2f}'.format(names[index],
                                                                                 float(sell_min_prices[index]),
                                                                                 float(buy_max_prices[index])))
                else:
                    messages.append('No results for {}.'.format(arg))
            except KeyError:
                messages.append('Could not find type_id for {}.'.format(name))
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
        print('generated api request: {}'.format(request_url))
        try:
            xml = parse(urllib.request.urlopen(request_url))
        except IOError:
            xml = None
    else:
        xml = None
    return xml


typeid_filename = 'market_only_typeids.csv'
typeid_dict = typeids_from_csv(typeid_filename)  # { type_name : type_id }
solar_system_id = {'Amarr': '30002187',
                   'Jita': '30000142',
                   'Dodixie': '30002659',
                   'Rens': '30002510',
                   'Hek': '30002053'}