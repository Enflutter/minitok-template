"""BONUS — Byte-Pair Encoding from scratch (+2% course-total bonus).

Standard library ONLY in this module (tiktoken is for Part B comparisons,
not here). Implement:

  train_bpe(corpus: str, num_merges: int) -> list[tuple[str, str]]
      Learn `num_merges` merge rules from the corpus. Start from the
      character-level vocabulary; repeatedly merge the most frequent
      adjacent pair; record rules in order. Ties: deterministic (e.g.,
      lexicographically smallest pair first).

  encode(text: str, merges: list[tuple[str, str]]) -> list[str]
      Apply merge rules in training order to `text` (start from its
      character sequence) and return the final token list.

  decode(tokens: list[str]) -> str
      Inverse of encode (concatenation).

Autograded by tests/test_bpe_bonus.py. Keep the exact signatures above.
"""

from __future__ import annotations


def train_bpe(corpus: str, num_merges: int) -> list[tuple[str, str]]:
    # TODO(BONUS): implement
    raise NotImplementedError("train_bpe is not implemented yet (bonus)")


def encode(text: str, merges: list[tuple[str, str]]) -> list[str]:
    # TODO(BONUS): implement
    raise NotImplementedError("encode is not implemented yet (bonus)")


def decode(tokens: list[str]) -> str:
    # TODO(BONUS): implement
    raise NotImplementedError("decode is not implemented yet (bonus)")
