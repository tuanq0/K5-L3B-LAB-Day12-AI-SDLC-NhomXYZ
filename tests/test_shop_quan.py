import os
import tempfile
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.live import LiveGame


class QuanShop(unittest.TestCase):
    def test_purchase_pauses_shift_and_persists_to_next_gather(self):
        tuning = load_contract()["tuning"]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "upgrades.json")
            with patch.dict(os.environ, {"CHONOI_UPGRADES_PATH": path}):
                game = LiveGame("quan", tuning, {}, seed=1)
                sim = game.session.sim
                sim.money = 200
                start_time = sim.time_left_ticks

                opened = game.session.step(InputState((0.0, 0.0), {}, set(), buy="shop"))
                self.assertEqual(opened[0]["name"], "shop_opened")
                self.assertEqual(sim.time_left_ticks, start_time)

                bought = game.session.step(InputState((0.0, 0.0), {}, set(), buy="oxygen"))
                self.assertEqual(bought[0]["name"], "bought")
                self.assertEqual(sim.money, 0)
                self.assertEqual(sim.upgrades, {"oxygen": 1})
                self.assertEqual(sim.time_left_ticks, start_time)

                next_gather = LiveGame("gather", tuning, {}, seed=1).session.sim
                self.assertEqual(next_gather.t["oxygen_max_s"], 45)


if __name__ == "__main__":
    unittest.main()
