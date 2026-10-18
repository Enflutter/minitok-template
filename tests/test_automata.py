# CANONICAL AUTOGRADING TESTS — DO NOT EDIT.
# Tampering invalidates autograding (see README §Integrity) and is verified
# by grading/run_tests.py via SHA-256 checksums.
"""Part A3 — determinization and the combined token DFA (20 pts)."""

import unittest

from minitok.automata import EPS, NFA, build_token_dfa, determinize, eps_closure
from minitok.spec import load_spec

SPEC_JSON = """{
  "tokens": [
    {"name": "WS",    "regex": "( |\\t)*",  "skip": true},
    {"name": "FLOAT", "regex": "<digit>*.<digit>*", "skip": false},
    {"name": "INT",   "regex": "<digit>*",  "skip": false},
    {"name": "IDENT", "regex": "<letter>(<letter>|<digit>|_)*", "skip": false},
    {"name": "OP",    "regex": "==|=|\\+|\\-", "skip": false}
  ]
}"""


def _tiny_nfa() -> NFA:
    # NFA accepting "ab": 0 -a-> 1, 1 -b-> 2(accept); plus an eps edge 0->3
    # and a self-loop on 3 for 'c' to exercise closures.
    nfa = NFA(states={0, 1, 2, 3}, alphabet={"a", "b", "c"},
              transitions={0: {"a": {1}, EPS: {3}},
                           1: {"b": {2}},
                           3: {"c": {3}}},
              start=0, accepts={2})
    return nfa


class TestEpsClosure(unittest.TestCase):
    def test_closure_includes_eps_reachable(self):
        nfa = _tiny_nfa()
        self.assertEqual(eps_closure(nfa, {0}), {0, 3})

    def test_closure_of_empty(self):
        nfa = _tiny_nfa()
        self.assertEqual(eps_closure(nfa, set()), set())

    def test_eps_cycle_terminates(self):
        nfa = NFA(states={0, 1}, alphabet=set(),
                  transitions={0: {EPS: {1}}, 1: {EPS: {0}}},
                  start=0, accepts={1})
        self.assertEqual(eps_closure(nfa, {0}), {0, 1})


class TestDeterminize(unittest.TestCase):
    def test_language_preserved(self):
        nfa = _tiny_nfa()
        dfa = determinize(nfa, label_of={2: "TOK"}, priority=["TOK"])
        self.assertEqual(dfa.simulate("ab"), "TOK")
        self.assertIsNone(dfa.simulate("a"))
        self.assertIsNone(dfa.simulate("abc"))
        self.assertIsNone(dfa.simulate(""))

    def test_labels_propagate(self):
        nfa = _tiny_nfa()
        dfa = determinize(nfa, label_of={2: "TOK"}, priority=["TOK"])
        labels = set(dfa.accepts.values())
        self.assertEqual(labels, {"TOK"})


class TestBuildTokenDFA(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec(SPEC_JSON)
        self.dfa = build_token_dfa(self.spec)

    def test_recognizes_each_class(self):
        self.assertEqual(self.dfa.simulate("hello_9"), "IDENT")
        self.assertEqual(self.dfa.simulate("42"), "INT")
        self.assertEqual(self.dfa.simulate("3.14"), "FLOAT")
        self.assertEqual(self.dfa.simulate("=="), "OP")
        self.assertEqual(self.dfa.simulate(" "), "WS")

    def test_int_prefix_is_not_float(self):
        # "3." must NOT be accepted as FLOAT (needs digits after the dot)
        self.assertIsNone(self.dfa.simulate("3."))

    def test_rejects_garbage(self):
        self.assertIsNone(self.dfa.simulate("@"))
        self.assertIsNone(self.dfa.simulate("9lives"))

    def test_start_state_reachable_and_labeled(self):
        self.assertIn(self.dfa.start, self.dfa.states)
        for st, label in self.dfa.accepts.items():
            self.assertIn(st, self.dfa.states)
            self.assertIn(label, self.spec.names)


if __name__ == "__main__":
    unittest.main()
