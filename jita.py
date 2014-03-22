__author__ = 'Corey'

from xml.etree.ElementTree import parse
import urllib.request
import os

typeid_url = 'http://eve-files.com/chribba/typeid.txt'
typeid_filename = 'typeid.txt'
typeid_old_filename = 'old_typeid.txt'
typeid_dict = {}


def update_typeid_file():
    """Downloads a new copy of the typeid.ext file and renames the previous file. Will overwrite."""
    if os.path.isfile(typeid_filename):
        os.rename(typeid_filename, typeid_old_filename)

    urllib.request.urlretrieve(typeid_url, typeid_filename)


def update_typeid_data(retry):
    """Attempt to update the typeid dictionary. Returns True if successful or False otherwise."""

    try:
        with open(typeid_filename, 'r', encoding='utf-8') as types_file:

            # Skip the first two lines
            types_file.readline()  # typeid ...
            types_file.readline()  # ----------- ...

            for line in types_file:
                if len(line) > 1:  # End of file readline() is an empty string, which makes string indexing unhappy.
                    s = line.split(None, 1)
                    typeid = s[0]
                    item_name = s[1].strip('\r\n').lower()
                    typeid_dict[item_name] = typeid
            print('Update successful.')

    except IOError:
        print('Failed to open {}, attempting to retrieve file from {}.'.format(typeid_filename, typeid_url))
        try:
            update_typeid_file()
            if retry:
                print('Retry once...')
                update_typeid_data(False)
        except IOError:
            print("Exception while retrieving {}, possibly a connection problem or problem opening file for writing.")
            return False
    return True

def get_price_message(item):
    message = ''
    try:
        # Get typeid using item as key
        typeid = typeid_dict[item]
        xml = get_marketstat_xml(typeid).getroot()
        max_buy = xml.find('./marketstat/type/buy/max').text
        min_sell = xml.find('./marketstat/type/sell/min').text
        # Set message string <item> sell: <price> Jita buy: <price>
        message = '{}, sell: {:,.2f}, buy: {:,.2f}'.format(item, float(min_sell), float(max_buy))
    except KeyError:
        message = 'Invalid or missing item name.'
    return message


def get_marketstat_xml(typeid):
    # Build api request url
    jita = '30000142'
    endpoint = 'http://api.eve-central.com/api/marketstat'
    query = '?typeid={}&usesystem={}'.format(str(typeid), jita)
    request_url = endpoint + query
    try:
        # Request, parse result into an element tree
        xml = parse(urllib.request.urlopen(request_url))
    except IOError:
        xml = None
    return xml

update_typeid_data(True)