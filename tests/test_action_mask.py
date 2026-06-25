import unittest

from sts2_ai_stream.env import action_mask


class ActionMaskTest(unittest.TestCase):
    def test_action_mask_sets_legal_indices(self):
        self.assertEqual(action_mask([0, 2], 4), [1, 0, 1, 0])

    def test_action_mask_rejects_out_of_range_indices(self):
        with self.assertRaises(ValueError):
            action_mask([4], 4)


if __name__ == "__main__":
    unittest.main()

