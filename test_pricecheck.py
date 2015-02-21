import pricecheck
import unittest


class GetTypeIds(unittest.TestCase):

    def test_uppercase_item_name(self):
        # Tritanium, 34
        result = pricecheck.get_type_ids('TRITANIUM')
        self.assertIn(34, result)

    def test_lowercase_item_name(self):
        # Tritanium, 34
        result = pricecheck.get_type_ids('tritanium')
        self.assertIn(34, result)

    def test_partial_item_name(self):
        # "30 Day Pilot's License Extension (PLEX)", 29668
        result = pricecheck.get_type_ids('30 day')
        self.assertIn(29668, result)

    def test_short_item_name(self):
        # item_names <= 3 characters are likely to return too many results
        result = pricecheck.get_type_ids('')
        self.assertEquals(result, [])

    def test_long_item_name(self):
        # item_names > 3 charaters should return results
        # "10MN Microwarpdrive I", 12052
        result = pricecheck.get_type_ids('10mn')
        self.assertIn(12052, result)

    def test_fake_item_name(self):
        result = pricecheck.get_type_ids('this_string_cannot_possibly_be_a_marketable_eve_item')
        self.assertEquals(result, [])


class GetSolarSystemId(unittest.TestCase):

    def test_uppercase_system_name(self):
        # Jita, 30000142
        result = pricecheck.get_solar_system_id('JITA')
        self.assertEquals(result, 30000142)

    def test_lowercase_system_name(self):
        # Jita, 30000142
        result = pricecheck.get_solar_system_id('jita')
        self.assertEquals(result, 30000142)

    def test_short_system_name(self):
        # The minimum length for a system name is 3.
        result = pricecheck.get_solar_system_id('Io')
        self.assertIsNone(result)

    def test_long_system_name(self):
        # Hek, 30002053
        result = pricecheck.get_solar_system_id('hek')
        self.assertEquals(result, 30002053)

    def test_fake_system_name(self):
        result = pricecheck.get_solar_system_id('this_string_cannot_possibly_be_an_eve_solar_system_name')
        self.assertIsNone(result)


class GetTypeNames(unittest.TestCase):

    def test_empty_type_ids(self):
        result = pricecheck.get_type_names()
        self.assertDictEqual(result, {})

    def test_one_valid_type_id(self):
        result = pricecheck.get_type_names(34)
        self.assertDictEqual(result, {34: u'Tritanium'})

    def test_one_invalid_type_id(self):
        result = pricecheck.get_type_names(9999999999)
        self.assertDictEqual(result, {})

    def test_valid_type_ids(self):
        result = pricecheck.get_type_names(34, 35, 36)
        self.assertDictEqual(result, {34: u'Tritanium', 35: u'Pyerite', 36: u'Mexallon'})

    def test_invalid_type_ids(self):
        result = pricecheck.get_type_names(1111111111, 222222222222, 9999999999)
        self.assertDictEqual(result, {})

    def test_some_invalid_type_ids(self):
        result = pricecheck.get_type_names(34, 35, 9999999999)
        self.assertDictEqual(result, {34: u'Tritanium', 35: u'Pyerite'})

    def test_one_string_type_id(self):
        result = pricecheck.get_type_names('not a number')
        self.assertDictEqual(result, {})

    def test_string_type_ids(self):
        result = pricecheck.get_type_names('not a number', 'also not a number')
        self.assertDictEqual(result, {})


class GetMarkettypesJson(unittest.TestCase):
    jita_id = 30000142
    tritanium_id = 34
    pyerite_id = 35
    bad_type_id = 1

    def test_invalid_one_typeid(self):
        result = pricecheck.get_marketstat_json(self.jita_id, [self.bad_type_id])
        self.assertIsNone(result)

    def test_valid_one_typeid(self):
        result = pricecheck.get_marketstat_json(self.jita_id, [self.tritanium_id])
        self.assertEquals(result[0]["buy"]["forQuery"]["types"][0], 34)

    def test_valid_multiple_typeids(self):
        result = pricecheck.get_marketstat_json(self.jita_id, [self.tritanium_id, self.pyerite_id])
        self.assertEquals(result[0]["buy"]["forQuery"]["types"][0], 34)
        self.assertEquals(result[1]["buy"]["forQuery"]["types"][0], 35)


class GetPriceMessages(unittest.TestCase):

    def test_valid_item_name(self):
        expected_result = ['Tritanium, sell: 5.85, buy: 5.84, volume: 39,970,440,116',
                           'Alloyed Tritanium Bar, sell: 15,379.91, buy: 14,500.00, volume: 702,195']
        result = pricecheck.get_price_messages('tritanium', 'jita')
        self.assertEquals(len(result), 2)

    def test_vague_item_name(self):
        result = pricecheck.get_price_messages('shield', 'jita')
        self.assertListEqual(result, ["Too many results for 'shield'. This limit is ignored in PMs."])

    def test_invalid_item_name(self):
        result = pricecheck.get_price_messages('not_even_remotely_a_valid_item_name', 'jita')
        self.assertListEqual(result, [])


class Wildcards(unittest.TestCase):

    def test_no_items(self):
        result = pricecheck._wildcards([])
        self.assertEquals(result, '')

    def test_one_item(self):
        result = pricecheck._wildcards([1])
        self.assertEquals(result, '?')

    def test_multiple_items(self):
        result = pricecheck._wildcards([1, 2, 3])
        self.assertEquals(result, '?,?,?')


if __name__ == '__main__':
    unittest.main()