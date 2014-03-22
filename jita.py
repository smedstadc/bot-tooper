__author__ = 'Corey'

from xml.etree.ElementTree import parse
import urllib.request
import time


def typeids_from_csv(filename):
    """
    Returns a dict of {type_name : type_id} from a csv file ordered as type_id, type_name.
    :rtype : dict
    """
    pairs = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                pairs.append(line.lower().strip('\r\n').split(',', 1))
        return {type_name: type_id for type_id, type_name in pairs}  #
    except IOError:
        return {}


def partial_key_matches(partial):
    """
    Returns a list of keys that a partial string matches.
    :rtype : list
    """
    keys = []
    for key in typeid_dict.keys():
        if key.startswith(partial):
            keys.append(key)
    return keys


# TODO return list of messages for multiple arguments or partial matches.
# TODO generate multi-parameter marketstat requests and interpret the xml results.
def get_price_messages(args):
    """Returns a list of message strings that will be sent by an IRC bot in response to a price check trigger."""
    messages = []
    for arg in args:
        names = partial_key_matches(arg)
        if len(names) > 5:
            messages.append('Too many partial matches for \'{}\'. Try to be more specific.'.format(arg))
        else:
            for name in names:
                try:
                    xml = get_marketstat_xml(typeid_dict[name])
                    if xml is not None:
                        xml = xml.getroot()
                        max_buy = xml.find('./marketstat/type/buy/max').text
                        min_sell = xml.find('./marketstat/type/sell/min').text
                        # Set message string <item> sell: <price> Jita buy: <price>
                        messages.append('{}, sell: {:,.2f}, buy: {:,.2f}'.format(name, float(min_sell), float(max_buy)))
                    else:
                        messages.append('Problem with API result for {}.'.format(name))
                    time.sleep(.5)
                except KeyError:
                    messages.append('Could not find type_id for {}.'.format(name))
    return messages


def get_marketstat_xml(typeid):
    """Returns the XML element tree result of an eve-central marketstat api request. Returns None if request fails."""
    # Build api request url
    jita = '30000142'
    endpoint = 'http://api.eve-central.com/api/marketstat'
    parameters = '?typeid={}&usesystem={}'.format(str(typeid), jita)
    request_url = endpoint + parameters
    try:
        # Retrieve request url, parse result into an xml element tree
        xml = parse(urllib.request.urlopen(request_url))
    except IOError:
        xml = None
    return xml

typeid_filename = 'market_only_typeids.csv'
typeid_dict = typeids_from_csv(typeid_filename)  # { type_name : type_id }