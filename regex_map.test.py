import unittest
import os
import json

from regex_map import word_to_lc_regex, create_regex_map, map_word_to_entry


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
        words = ["A", "a", "the", "and", "ax", "it's"]
        with open(cls.src, 'w') as f:
            for word in words:
                f.write("%s\n" % word)
        create_regex_map([cls.src], [False], cls.dest)
        with open(cls.dest) as f:
            cls.regex_map = json.load(f)

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove(cls.src)
        os.remove(cls.dest)

    def test_missing_word(self):
        self.assertIsNone(map_word_to_entry('kwyjibo', self.regex_map))
        self.assertIsNone(map_word_to_entry('', self.regex_map))

    def test_trailing_symbols(self):
        self.assertEqual(map_word_to_entry(';,.,;', self.regex_map)['default'], 'ax',
                         msg=";, == ax while .,; are cut out")

    def test_deepcopy(self):
        entry = map_word_to_entry(';,.,;', self.regex_map)
        entry['words'].append('hi')
        self.assertNotEqual(entry, map_word_to_entry(';,.,;', self.regex_map))


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


if __name__ == '__main__':
    unittest.main()
