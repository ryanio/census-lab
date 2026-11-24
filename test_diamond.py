"""Exercise histories where comparing only the first and current owner is ambiguous."""

import unittest

from diamond import CONTRACT, TRANSFER, replay


def event(index, sender, recipient):
    return {
        "address": CONTRACT,
        "blockNumber": "0x1",
        "logIndex": hex(index) if index else "0x",
        "topics": [TRANSFER, f"0x{sender:064x}", f"0x{recipient:064x}", f"0x{1:064x}"],
        "timeStamp": hex(100 + index),
        "transactionHash": hex(index),
    }


class ReplayTests(unittest.TestCase):
    def test_self_transfer_preserves_mint_tenure(self):
        row = replay([event(1, 1, 1), event(0, 0, 1)])[1]
        self.assertTrue(row["continuous"])
        self.assertEqual(row["since"], 100)

    def test_return_after_transfer_or_burn_restarts_tenure(self):
        for intermediate in (0, 2):
            with self.subTest(intermediate=intermediate):
                row = replay(
                    [
                        event(0, 0, 1),
                        event(1, 1, intermediate),
                        event(2, intermediate, 1),
                    ]
                )[1]
                self.assertFalse(row["continuous"])
                self.assertEqual(row["original"], row["owner"])
                self.assertEqual(row["since"], 102)

    def test_burn_removes_token_from_supply(self):
        self.assertEqual(replay([event(0, 0, 1), event(1, 1, 0)]), {})

    def test_incomplete_history_rejected(self):
        with self.assertRaises(ValueError):
            replay([event(1, 1, 2)])
