#!/usr/bin/env python3
""" jita.py
    Checks the eve-central api marketdata for a given item name and returns price message strings.

"""

# TODO Alter get_marketstat_xml to use requests

from xml.etree.ElementTree import parse
import urllib.request
import time


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


def partial_key_matches(partial):
    """Returns a list of keys that a partial string matches."""
    keys = []
    for key in typeid_dict.keys():
        if key.lower().startswith(partial.lower()):
            if key.find('edition') != -1:
                print('skipping key for paint job hull until supported by evec_api...')
            else:
                keys.append(key)
    return keys


def get_price_messages(args):
    """Returns a list of message strings that will be sent by an IRC bot in response to a price check trigger."""
    messages = []
    for arg in args:
        names = partial_key_matches(arg)
        if len(names) > 10:
            messages.append('Too many partial matches for \'{}\'. Try to be more specific.'.format(arg))
        else:
            typeids = []
            for name in names:
                typeids.append(typeid_dict[name])
            try:
                xml = get_marketstat_xml(typeids)
                buy_max_prices = []
                sell_min_prices = []
                if xml is not None:
                    xml = xml.getroot()
                    # find better way to do this
                    for child in xml[0]:
                        sell_min_prices.append(child[1][3].text)  # SELL MIN
                        buy_max_prices.append(child[0][2].text)  # BUY MAX
                    for index in range(len(names)):
                        messages.append(
                            '{}, sell: {:,.2f}, buy: {:,.2f}'.format(names[index], float(sell_min_prices[index]),
                                                                     float(buy_max_prices[index])))
                else:
                    messages.append('No results for {}.'.format(arg))
                time.sleep(.5)
            except KeyError:
                messages.append('Could not find type_id for {}.'.format(name))
    return messages


def get_marketstat_xml(typeids):
    """Returns the XML element tree result of an eve-central marketstat api request. Returns None if request fails."""
    if len(typeids) > 0:
        jita = '30000142'
        endpoint = 'http://api.eve-central.com/api/marketstat'
        parameters = '?typeid={}'.format(str(typeids[0]))
        if len(typeids) > 1:
            for typeid in typeids[1:]:
                parameters += '&typeid={}'.format(typeid)
        parameters += '&usesystem={}'.format(jita)
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