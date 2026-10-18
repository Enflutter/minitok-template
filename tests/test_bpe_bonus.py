# CANONICAL BONUS TESTS — DO NOT EDIT.
# These are reported separately by grading/run_tests.py and never count
# toward the base 70 autograded points. Passing all of them (+ the Part B
# comparison section in report.pdf) earns the +2% course-total bonus.
"""BONUS — BPE from scratch."""

import unittest

from minitok.bpe_from_scratch import decode, encode, train_bpe

CORPUS = "the cat sat on the mat. the cat ate the rat."


class TestTrainBPE(unittest.TestCase):
    def test_most_frequent_pair_first(self):
        corpus = "abab abab"
        merges = train_bpe(corpus, 1)
        self.assertEqual(len(merges), 1)
        self.assertEqual(merges[0], ("a", "b"))

    def test_merge_count_respected(self):
        merges = train_bpe(CORPUS, 5)
        self.assertEqual(len(merges), 5)

    def test_merges_are_pairs_of_strings(self):
        merges = train_bpe(CORPUS, 3)
        for a, b in merges:
            self.assertIsInstance(a, str)
            self.assertIsInstance(b, str)

    def test_deterministic_tie_break(self):
        m1 = train_bpe("xyxy zaza", 4)
        m2 = train_bpe("xyxy zaza", 4)
        self.assertEqual(m1, m2)


class TestEncodeDecode(unittest.TestCase):
    def test_roundtrip(self):
        merges = train_bpe(CORPUS, 10)
        for text in ["the cat", "the rat sat", CORPUS]:
            self.assertEqual(decode(encode(text, merges)), text)

    def test_encode_uses_merges(self):
        merges = [("t", "h"), ("th", "e")]
        toks = encode("the the", merges)
        self.assertIn("the", toks)
        self.assertEqual(decode(toks), "the the")

    def test_no_merges_is_char_level(self):
        toks = encode("abc", [])
        self.assertEqual(toks, ["a", "b", "c"])

    def test_empty_text(self):
        self.assertEqual(encode("", []), [])
        self.assertEqual(decode([]), "")


if __name__ == "__main__":
    unittest.main()
