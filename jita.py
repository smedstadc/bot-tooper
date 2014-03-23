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


def get_price_messages_multi(args):
    """Alternate implementation that relies on results from get_marketstat_xml_multi."""
    messages = []
    for arg in args:
        names = partial_key_matches(arg)
        if len(names) > 5:
            messages.append('Too many partial matches for \'{}\'. Try to be more specific.'.format(arg))
        else:
            typeids = []
            for name in names:
                typeids.append(typeid_dict[name])
            try:
                xml = get_marketstat_xml_multi(typeids)
                buy_max_prices = []
                sell_min_prices = []
                if xml is not None:
                    xml = xml.getroot()
                    for child in xml[0]:
                        sell_min_prices.append(child[1][3].text)  # SELL MIN
                        buy_max_prices.append(child[0][2].text)  # BUY MAX
                    for index in range(len(names)):
                        messages.append('{}, sell: {:,.2f}, buy: {:,.2f}'.format(names[index], float(sell_min_prices[index]), float(buy_max_prices[index])))
                else:
                    messages.append('Problem with API results.')
                time.sleep(.5)
            except KeyError:
                messages.append('Could not find type_id for {}.'.format(name))
    return messages


def get_marketstat_xml_multi(typeids):
    """
    Alternate implementation that makes fewer api requests, instead of one per item name. Hulls with custom paint
    will cause requests to fail until eve-c updates their market data to include the new ships.
    """
    jita = '30000142'
    endpoint = 'http://api.eve-central.com/api/marketstat'
    parameters = '?typeid={}'.format(str(typeids[0]))
    if len(typeids) > 1:
        for typeid in typeids[1:]:
            parameters += '&typeid={}'.format(typeid)
    parameters += '&usesystem={}'.format(jita)
    request_url = endpoint + parameters
    try:
        xml = parse(urllib.request.urlopen(request_url))
    except IOError:
        xml = None
    return xml

typeid_filename = 'market_only_typeids.csv'
typeid_dict = typeids_from_csv(typeid_filename)  # { type_name : type_id }