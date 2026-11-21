"""Vòng Ngày tích hợp Gather -> Quan -> Shop."""

from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        day_cfg = scenario.get("day", {}) if isinstance(scenario, dict) else {}
        self.max_days = min(5, max(1, int(days)))
        self.day = int(day_cfg.get("day", 1))
        self.day = max(1, min(5, self.day))
        self.money = int(day_cfg.get("money", 0))
        self.earned = int(day_cfg.get("earned", 0))
        self.reputation = float(day_cfg.get("reputation",
                                            tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(day_cfg.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)
        self.days_completed = 0
        self.done = False
        self.reason = None
        self.time_left_ticks = tuning["gather"]["duration_s"] * 60
        self.shop_time_left = int(tuning["shop"]["max_ticks"])
        self.phase_tick = 0
        self.phase = "gather"
        self.paused = False
        self.day_plan = tuning["day_plan"][self.day - 1]
        gather_scenario = dict(scenario.get("gather", {}) if isinstance(scenario, dict) else {})
        gather_scenario["day"] = self.day
        gather_scenario["active_upgrades"] = dict(self.active_upgrades)
        self.gather = GatherSim(tuning, gather_scenario, streams, ids)

    def snapshot(self):
        if self.phase == "gather":
            data = self.gather.snapshot()
            time_left = self.gather.time_left_ticks
        elif self.phase == "quan":
            data = self.quan.snapshot()
            time_left = self.quan.time_left_ticks
        else:
            data = {"stock": dict(self.stock), "hand": None}
            time_left = self.shop_time_left
        data.update({
            "phase": self.phase,
            "time_left_ticks": time_left,
            "day": self.day,
            "day_plan": self.day_plan,
            "upgrades": self.upgrades,
            "active_upgrades": self.active_upgrades,
        })
        return data

    def inventory_items(self):
        if self.phase == "gather":
            return self.gather.inventory_items()
        if hasattr(self, "quan"):
            return dict(self.quan.stock)
        return dict(getattr(self, "stock", {}))

    def step(self, inp):
        events = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            events.append(("resumed", {}) if not self.paused else ("paused", {}))
            if self.paused:
                return events
        if self.paused:
            return events
        self.phase_tick += 1
        if self.phase == "gather":
            rows = self.gather.step(inp)
            events.extend(rows)
            if self.gather.done:
                inventory = self.gather.inventory_items()
                quan_scenario = {
                    "stock": inventory,
                    "time_left_ticks": int(self.tuning["quan"]["duration_s"] * 60),
                    "reputation": self.reputation,
                    "money": self.money,
                    "earned": self.earned,
                }
                day_scenario = {} if not isinstance(locals().get("quan_scenario"), dict) else quan_scenario
                # The plan filters available dishes in Quan.
                day_scenario["day_plan"] = self.day_plan
                self.quan = QuanSim(self.tuning, day_scenario, self.rng, self.ids,
                                    allow_midshift_shop=False)
                self.quan.plan_dishes = set(self.day_plan["dishes"])
                self.phase = "quan"
                self.phase_tick = 0
                events.append(("phase_start", {"phase":"quan"}))
            else:
                self.time_left_ticks = self.gather.time_left_ticks
        elif self.phase == "quan":
            rows = self.quan.step(inp)
            events.extend(rows)
            if self.quan.done:
                self.money = self.quan.money
                self.earned = self.quan.earned
                self.reputation = self.quan.reputation
                self.stock = dict(self.quan.stock)
                self.shop_time_left = int(self.tuning["shop"]["max_ticks"])
                self.phase = "shop"
                self.phase_tick = 0
                events.append(("phase_start", {"phase":"shop"}))
        else:
            if getattr(inp, "buy", None):
                events.extend(self._buy(inp.buy))
            if inp.pressed("shop_done"):
                self._close_shop("done")
                events.append(("shop_end", {"reason":"done"}))
            elif inp.pressed("buy"):
                pass
            self.shop_time_left = max(0, self.shop_time_left - 1)
            if self.shop_time_left == 0 and not self.done:
                self._close_shop("time")
                events.append(("shop_end", {"reason":"time"}))
        return events

    def _buy(self, action):
        if action not in ("oxygen", "hp"):
            return [("buy_failed", {"action":action,"reason":"unknown"})]
        current = int(self.upgrades.get(action, 0))
        levels = self.tuning["shop"]["upgrades"][action]
        if current >= len(levels):
            return [("buy_failed", {"action":action,"reason":"max_level"})]
        upgrade = levels[current]
        price = int(upgrade["price"])
        if self.money < price:
            return [("buy_failed", {"action":action,"reason":"funds"})]
        updated = dict(self.upgrades)
        updated[action] = current + 1
        persist = getattr(self, "persist_upgrades", None)
        if persist is not None:
            try:
                persist(updated)
            except OSError as error:
                return [("buy_failed", {"action": action, "reason": "save_error",
                                        "message": str(error)})]
        self.money -= price
        self.upgrades = updated
        return [("bought", {"upgrade":action,"level":current+1,"price":price,"money":self.money})]

    def _close_shop(self, reason):
        self.days_completed += 1
        self.active_upgrades = dict(self.upgrades)
        if self.days_completed >= self.max_days or self.day >= 5:
            self.done = True
            self.reason = "days_complete"
        else:
            self.day += 1
            self.day_plan = self.tuning["day_plan"][self.day - 1]
            gather_scenario = {"day": self.day, "active_upgrades": dict(self.active_upgrades)}
            self.gather = GatherSim(self.tuning, gather_scenario, self.rng, self.ids)
            self.phase = "gather"
            self.phase_tick = 0
            self.time_left_ticks = self.gather.time_left_ticks
