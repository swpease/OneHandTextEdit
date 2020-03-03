import unittest
import os

from regex_map import word_to_regex, _create_regex_map


class TestRegexMaker(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(word_to_regex('a'), '^[a;]$')

    def test_casing(self):
        self.assertEqual(word_to_regex('AaA'), '^[a;][a;][a;]$')

    def test_missing_keys(self):
        self.assertEqual(word_to_regex('2@'), '^[2][@]$')

    def test_raw_backslash(self):
        self.assertEqual(word_to_regex(r'\n'), r'^[\][vn]$')


class TestRegexMapMaker(unittest.TestCase):
    def setUp(self) -> None:
        self.src = 'test_words.txt'
        self.dest = 'test_out.json'
        words = ["a", "A", "the"]
        with open(self.src, 'w') as f:
            for word in words:
                f.write("%s\n" % word)

    def tearDown(self) -> None:
        os.remove(self.src)
        os.remove(self.dest)
    
    def test_basic(self):
        _create_regex_map(self.src, self.dest)
        with open(self.dest) as f:
            output = f.readline()
        self.assertEqual(output, '{"^[a;]$": {"default": "a", "words": ["a", "A"]}, "^[ty][gh][ei]$": {"default": "the", "words": ["the"]}}')


if __name__ == '__main__':
    unittest.main()
