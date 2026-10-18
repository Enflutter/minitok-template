# CANONICAL AUTOGRADING TESTS — DO NOT EDIT.
# Tampering invalidates autograding (see README §Integrity) and is verified
# by grading/run_tests.py via SHA-256 checksums.
"""Part A2 — regex -> NFA compiler (20 pts)."""

import unittest

from minitok.regex_compiler import RegexSyntaxError, compile_regex


def accepts(regex: str, s: str) -> bool:
    return compile_regex(regex).simulate(s)


class TestSingleConstructs(unittest.TestCase):
    def test_literal(self):
        nfa = compile_regex("a")
        self.assertTrue(nfa.simulate("a"))
        self.assertFalse(nfa.simulate("b"))
        self.assertFalse(nfa.simulate(""))

    def test_union(self):
        self.assertTrue(accepts("a|b", "a"))
        self.assertTrue(accepts("a|b", "b"))
        self.assertFalse(accepts("a|b", "ab"))

    def test_concat(self):
        self.assertTrue(accepts("ab", "ab"))
        self.assertFalse(accepts("ab", "a"))
        self.assertFalse(accepts("ab", "ba"))

    def test_star_is_one_or_more(self):
        # In this spec, postfix * means "one or more" (plus).
        self.assertTrue(accepts("a*", "a"))
        self.assertTrue(accepts("a*", "aaa"))
        self.assertFalse(accepts("a*", ""))
        self.assertFalse(accepts("a*", "b"))

    def test_grouping(self):
        self.assertTrue(accepts("(a|b)c", "ac"))
        self.assertTrue(accepts("(a|b)c", "bc"))
        self.assertFalse(accepts("(a|b)c", "c"))

    def test_class_digit(self):
        self.assertTrue(accepts("<digit>*", "0"))
        self.assertTrue(accepts("<digit>*", "987"))
        self.assertFalse(accepts("<digit>*", "12a"))

    def test_class_letter(self):
        self.assertTrue(accepts("<letter>", "q"))
        self.assertFalse(accepts("<letter>", "7"))


class TestCombined(unittest.TestCase):
    def test_identifier(self):
        ok = accepts("<letter>(<letter>|<digit>|_)*", "x_9y")
        bad = accepts("<letter>(<letter>|<digit>|_)*", "9x")
        self.assertTrue(ok)
        self.assertFalse(bad)

    def test_operator_union(self):
        self.assertTrue(accepts("==|=", "=="))
        self.assertTrue(accepts("==|=", "="))
        self.assertFalse(accepts("==|=", "==="))

    def test_precedence_star_over_concat(self):
        # ab* == a(b)(b)* ... here: 'a' followed by one-or-more 'b'
        self.assertTrue(accepts("ab*", "ab"))
        self.assertTrue(accepts("ab*", "abb"))
        self.assertFalse(accepts("ab*", "a"))
        self.assertFalse(accepts("ab*", "abab"))

    def test_nested(self):
        self.assertTrue(accepts("(a|bb)*c", "abbc"))
        self.assertTrue(accepts("(a|bb)*c", "c"))
        self.assertFalse(accepts("(a|bb)*c", "acab"))


class TestSyntaxErrors(unittest.TestCase):
    def test_unbalanced_open(self):
        with self.assertRaises(RegexSyntaxError):
            compile_regex("(a|b")

    def test_unbalanced_close(self):
        with self.assertRaises(RegexSyntaxError):
            compile_regex("a|b)")

    def test_dangling_union(self):
        with self.assertRaises(RegexSyntaxError):
            compile_regex("a|")

    def test_empty_regex(self):
        with self.assertRaises(RegexSyntaxError):
            compile_regex("")


if __name__ == "__main__":
    unittest.main()
