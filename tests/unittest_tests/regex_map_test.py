import unittest
import os
import json

from OHTE.regex_map import word_to_lc_regex, create_regex_map, map_word_to_entry, map_string_to_word, add_word_to_dict


class TestRegexMaker(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(word_to_lc_regex('a'), '^[a;]$')

    def test_casing(self):
        self.assertEqual(word_to_lc_regex('AaA'), '^[a;][a;][a;]$')
        self.assertEqual(word_to_lc_regex(':<>'), '^[a;][x,][z.]$', msg="symbols lowerize")

    def test_missing_keys(self):
        self.assertEqual(word_to_lc_regex('2@'), '^[2][@]$')

    def test_raw_backslash(self):
        self.assertEqual(word_to_lc_regex(r'\n'), r'^[\][vn]$')


class TestWordMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.src = 'test_words.txt'
        cls.dest = 'test_out.json'
        words = ["A", "a", "the", "and", "ax", "it's", "may", "cat", "May", "Hi", "hi", "he"]
        with open(cls.src, 'w') as f:
            for word in words:
                f.write("%s\n" % word)
        create_regex_map([cls.src], [True], cls.dest)
        with open(cls.dest) as f:
            cls.regex_map = json.load(f)

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove(cls.src)
        os.remove(cls.dest)

    def test_missing_word(self):
        self.assertIsNone(map_string_to_word('kwyjibo', self.regex_map))
        self.assertIsNone(map_string_to_word('', self.regex_map))

    def test_trailing_symbols(self):
        self.assertEqual(map_string_to_word(';,.,;', self.regex_map), 'ax.,;',
                         msg=";, == ax while .,; is tacked on")
        self.assertEqual(map_string_to_word('ax:<>AZX', self.regex_map), 'ax:<>:><')

    def test_possessives(self):
        self.assertEqual(map_string_to_word('ax\'sA', self.regex_map), 'ax\'s:')

    def test_caps(self):
        self.assertEqual(map_string_to_word('Ax', self.regex_map), 'Ax')


class TestEntryMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.src = 'test_words.txt'
        cls.dest = 'test_out.json'
        words = ["A", "a", "the", "and", "ax", "it's", "may", "cat", "May", "Hi", "hi", "he"]
        with open(cls.src, 'w') as f:
            for word in words:
                f.write("%s\n" % word)
        create_regex_map([cls.src], [True], cls.dest)
        with open(cls.dest) as f:
            cls.regex_map = json.load(f)

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove(cls.src)
        os.remove(cls.dest)

    def test_missing_word(self):
        self.assertIsNone(map_word_to_entry('kwyjibo', self.regex_map))
        self.assertIsNone(map_word_to_entry('', self.regex_map))

    def test_deepcopy(self):
        entry = map_word_to_entry(';,', self.regex_map)
        entry['words'].append('hi')
        self.assertNotEqual(entry, map_word_to_entry(';,', self.regex_map))

    def test_possessives(self):
        word = 'ax\'s'
        entry = map_word_to_entry(word, self.regex_map)
        self.assertEqual(word, entry['default'])
        self.assertEqual([word], entry['words'])

    def test_caps_stuff(self):
        entry = map_word_to_entry('may', self.regex_map)
        self.assertEqual(entry['default'], 'may')
        self.assertEqual(entry['words'], ['may', 'cat', 'May'])

        entry = map_word_to_entry('May', self.regex_map)
        self.assertEqual(entry['default'], 'May')
        self.assertEqual(entry['words'], ['May', 'Cat'])

        entry = map_word_to_entry('Hi', self.regex_map)
        self.assertEqual(entry['default'], 'Hi')
        self.assertEqual(entry['words'], ['Hi', 'hi', 'he', 'He'])


class TestRegexMapMaker(unittest.TestCase):
    def setUp(self) -> None:
        self.src1 = 'test_words.txt'
        self.src2 = 'test_words2.txt'
        self.src3 = 'test_words3.txt'
        self.dest = 'test_out.json'
        words1 = ["a", "A", "the", "thi", "a"]
        words2 = ["B"]
        words3 = ["a", "a"]
        with open(self.src1, 'w') as f:
            for word in words1:
                f.write("%s\n" % word)
        with open(self.src2, 'w') as f:
            for word in words2:
                f.write("%s\n" % word)
        with open(self.src3, 'w') as f:
            for word in words3:
                f.write("%s\n" % word)

    def tearDown(self) -> None:
        for f in [self.src1, self.src2, self.src3]:
            os.remove(f)
        os.remove(self.dest)
    
    def test_basic(self):
        create_regex_map([self.src1, self.src2, self.src3], [False, True], self.dest)
        with open(self.dest) as f:
            output = f.readline()
        self.assertEqual(output, '{"^[a;]$": {"default": "a", "words": ["a"]}, "^[ty][gh][ei]$": {"default": "the", "words": ["the", "thi"]}, "^[b]$": {"default": "B", "words": ["B"]}}')


class TestAddWord(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.src = 'test_words.txt'
        cls.dest = 'test_out.json'
        words = ["may", "cat"]
        with open(cls.src, 'w') as f:
            for word in words:
                f.write("%s\n" % word)
        create_regex_map([cls.src], [True], cls.dest)
        with open(cls.dest) as f:
            cls.regex_map = json.load(f)

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove(cls.src)
        os.remove(cls.dest)

    def test_duplicate_word(self):
        self.assertEqual(str(self.regex_map), "{'^[cm][a;][ty]$': {'default': 'may', 'words': ['may', 'cat']}}")
        add_word_to_dict('may', self.regex_map)
        self.assertEqual(str(self.regex_map), "{'^[cm][a;][ty]$': {'default': 'may', 'words': ['may', 'cat']}}")

    def test_existing_entry(self):
        self.assertEqual(str(self.regex_map), "{'^[cm][a;][ty]$': {'default': 'may', 'words': ['may', 'cat']}}")
        add_word_to_dict('cay', self.regex_map)
        self.assertEqual(str(self.regex_map), "{'^[cm][a;][ty]$': {'default': 'may', 'words': ['may', 'cat', 'cay']}}")

    def test_no_entry(self):
        self.assertEqual(str(self.regex_map), "{'^[cm][a;][ty]$': {'default': 'may', 'words': ['may', 'cat', 'cay']}}")
        add_word_to_dict('a', self.regex_map)
        self.assertEqual(str(self.regex_map), "{'^[cm][a;][ty]$': {'default': 'may', 'words': ['may', 'cat', 'cay']}, '^[a;]$': {'default': 'a', 'words': ['a']}}")


if __name__ == '__main__':
    unittest.main()
