import unittest

from helpers import events, frames, read_jsonl, run_headless, snapshots, write_json, Workdir


def monster(identifier, pos=(50, 10)):
    return {
        "id": identifier,
        "kind": "ca_sau",
        "pos": list(pos),
        "waypoints": [list(pos), list(pos)],
    }


class GatherMonsters(unittest.TestCase):
    def test_hit_selects_nearest_id_drops_lifo_and_starts_recoil(self):
        with Workdir() as work:
            scenario = write_json(work.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [50, 10]},
                    "hold": ["ca_loc", "ca_linh", "bong_sung", "ca_keo", "keo_neo"],
                    "random_fish": False,
                    "fish": [],
                    "monsters": [monster("M10"), monster("M2")],
                },
            })
            out = work.path("run.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--snapshot-every", "1", "--scenario", scenario, "--out", out)

            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            hit = events(rows, "monster_hit")
            self.assertEqual(len(hit), 1)
            self.assertEqual(hit[0]["data"]["monster_id"], "M2")
            self.assertEqual(hit[0]["data"]["lost"], ["keo_neo", "ca_keo"])
            by_tick = {row["tick"]: row for row in snapshots(rows)}
            self.assertEqual(by_tick[1]["hold"], ["ca_loc", "ca_linh", "bong_sung"])
            selected = next(m for m in by_tick[1]["monsters"] if m["id"] == "M2")
            self.assertEqual(selected["state"], "recoil")
            self.assertEqual(selected["state_ticks_left"], 60)
            self.assertEqual(selected["recoil_dir"], [1.0, 0.0])
            self.assertAlmostEqual(next(m for m in by_tick[2]["monsters"] if m["id"] == "M2")
                                   ["pos"][0], 50 + 2 / 60)

    def test_invulnerability_blocks_full_configured_ticks(self):
        with Workdir() as work:
            scenario = write_json(work.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [50, 10], "invuln_ticks": 2},
                    "random_fish": False,
                    "fish": [],
                    "monsters": [monster("M1")],
                },
            })
            out = work.path("run.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                     "--snapshot-every", "1", "--scenario", scenario, "--out", out)

            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([row["tick"] for row in events(rows, "monster_hit")], [3])

    def test_fatal_hit_faints_and_day_enters_evening_with_empty_stock(self):
        with Workdir() as work:
            scenario = write_json(work.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [50, 10], "hp": 1},
                    "hold": ["ca_loc", "ca_linh"],
                    "random_fish": False,
                    "fish": [],
                    "monsters": [monster("M1")],
                },
            })
            out = work.path("run.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "1",
                                     "--snapshot-every", "1", "--scenario", scenario, "--out", out)

            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            faint = events(rows, "faint")
            end = events(rows, "gather_end")
            self.assertEqual(faint[0]["data"], {
                "cause": "monster", "lost": ["ca_loc"], "hp": 0,
            })
            self.assertEqual(end[0]["data"]["reason"], "fainted")
            self.assertEqual(end[0]["data"]["inventory"], {"items": {}})
            evening = [row for row in snapshots(rows) if row["phase"] == "quan"]
            self.assertEqual(evening[-1]["stock"], {})


if __name__ == "__main__":
    unittest.main()
