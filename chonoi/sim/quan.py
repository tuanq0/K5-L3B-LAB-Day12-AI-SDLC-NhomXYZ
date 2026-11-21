"""Buổi tối — Mở Quán."""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allow_midshift_shop=True):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.upgrade_levels = tuning.get("shop", {}).get("upgrades", {})
        self.upgrades = dict(scenario.get("upgrades", {}))
        self.shop_open = False
        self.allow_midshift_shop = allow_midshift_shop
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.gather_portal = [14.0, 8.0]
        self.plan_dishes = set(scenario.get("plan_dishes", []))
        self.patience_max = int(round(t["patience_s"] * TICK))
        self.eat_ticks = int(round(t["eat_s"] * TICK))
        self.customers = []
        for c in scenario.get("customers", []):
            customer = dict(c)
            customer.setdefault("state", "waiting")
            customer.setdefault("order_tick", 0)
            customer.setdefault("patience_ticks_left", self.patience_max)
            customer.setdefault("eat_ticks_left", 0)
            customer.setdefault("order_status", "reserved")
            dish_id = customer.get("dish_id")
            if customer["order_status"] == "reserved":
                customer["reserved"] = dict(c.get("reserved",
                                                  self.menu[dish_id]["recipe"] if dish_id in self.menu else {}))
            else:
                customer["reserved"] = dict(c.get("reserved", {}))
            customer.setdefault("base_price",
                                self.menu[dish_id]["price"] if dish_id in self.menu else 0)
            customer.setdefault("tip", 0)
            self.customers.append(customer)
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = int(scenario.get("money", 0))
        self.earned = int(scenario.get("earned", 0))
        self.shift_earned = int(scenario.get("shift_earned", 0))
        self.done = False
        self.reason = None
        self.paused = False

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "gather_portal": self.gather_portal,
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
            "shop_open": self.shop_open,
            "upgrades": self.upgrades,
            "active_upgrades": self.upgrades,
        }

    def step(self, inp):
        events = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            events.append(("resumed", {}) if not self.paused else ("paused", {}))
            if self.paused:
                return events
        if self.paused:
            return events
        if self.shop_open:
            if getattr(inp, "buy", None):
                events.extend(self._buy_upgrade(inp.buy))
            if inp.pressed("shop_done"):
                self.shop_open = False
                events.append(("shop_closed", {}))
            return events
        if self.allow_midshift_shop and getattr(inp, "buy", None) == "shop":
            self.shop_open = True
            events.append(("shop_opened", {}))
            return events
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1
        closing = self.time_left_ticks == 0

        # Giảm nấu/ăn/kiên nhẫn bắt đầu sau bước dựng.
        for stove in sort_by_id(self.stoves):
            if stove["state"] == "cooking":
                stove["cook_ticks_left"] = max(0, stove["cook_ticks_left"] - 1)
                if stove["cook_ticks_left"] == 0:
                    stove["state"] = "ready"
                    stove["ready_ticks"] = 0
                    events.append(("dish_ready", {"stove_id": stove["id"],
                                                  "order_id": stove.get("order_id"),
                                                  "dish_id": stove["dish"]}))
            elif stove["state"] == "ready":
                stove["ready_ticks"] = max(0, stove["ready_ticks"] + 1)

        for customer in sort_by_id(self.customers):
            if customer["state"] == "eating":
                customer["eat_ticks_left"] = max(0, customer["eat_ticks_left"] - 1)
            elif customer["state"] == "waiting":
                customer["patience_ticks_left"] = max(0,
                                                      customer["patience_ticks_left"] - 1)

        self._move(inp)

        if inp.pressed("interact"):
            candidate = self._nearest_interactable()
            if candidate is not None:
                kind, obj = candidate
                if kind == "stove":
                    events.extend(self._interact_stove(obj))
                elif kind == "gather":
                    events.append(("gather_transition", {}))
                else:
                    events.extend(self._interact_table(obj))

        # Trả tiền ăn xong trước; khách kiên nhẫn hết rời nếu ca còn giờ.
        customer_count_before_leave = len(self.customers)
        events.extend(self._remove_finished_and_leave(closing))
        table_just_freed = len(self.customers) < customer_count_before_leave

        if not closing:
            events.extend(self._maybe_arrive(force=table_just_freed))

        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _buy_upgrade(self, action):
        if action not in ("oxygen", "hp"):
            return [("buy_failed", {"action": action, "reason": "unknown"})]
        current = int(self.upgrades.get(action, 0))
        levels = self.upgrade_levels.get(action, [])
        if current >= len(levels):
            return [("buy_failed", {"action": action, "reason": "max_level"})]
        upgrade = levels[current]
        price = int(upgrade["price"])
        if self.money < price:
            return [("buy_failed", {"action": action, "reason": "funds"})]

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
        return [("bought", {"upgrade": action, "level": current + 1,
                            "price": price, "money": self.money})]

    def _reserved_total(self):
        totals = {}
        for customer in self.customers:
            for kind, amount in customer.get("reserved", {}).items():
                totals[kind] = totals.get(kind, 0) + amount
        return totals

    def _dish_available(self, dish_id):
        reserved = self._reserved_total()
        recipe = self.menu[dish_id]["recipe"]
        return all(self.stock.get(kind, 0) - reserved.get(kind, 0) >= amount
                   for kind, amount in recipe.items())

    def _maybe_arrive(self, force=False):
        events = []
        first = int(self.t["first_customer_tick"])
        interval = int(round(self.t["customer_interval_s"] * TICK))
        due = self.phase_tick == first or (
            self.phase_tick > first and (self.phase_tick - first) % interval == 0
        )
        if (not due and not force) or not self.random_customers:
            return events

        # Một lượt khách chỉ chiếm bàn trống id nhỏ nhất.
        occupied = {c["table_id"] for c in self.customers}
        candidates = [table for table in sort_by_id(self.tables)
                      if table["id"] not in occupied]
        if not candidates:
            return events

        table = candidates[0]
        dish_ids = self.plan_dishes if getattr(self, "plan_dishes", set()) else set(self.menu)
        available = sorted(
            (dish_id for dish_id in dish_ids if dish_id in self.menu and self._dish_available(dish_id)),
            key=lambda dish_id: dish_id,
        )
        if not available:
            events.append(("no_dish", {}))
            return events

        dish_id = self.rng.get("customer_dishes").choice(available)
        recipe = dict(self.menu[dish_id]["recipe"])
        customer_id = self.ids.new("C")
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": self.patience_max,
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": recipe,
            "base_price": self.menu[dish_id]["price"],
            "tip": 0,
        }
        self.customers.append(customer)
        events.append(("customer_arrived",
                       {"order_id": customer_id, "table_id": table["id"], "dish_id": dish_id}))
        return events

    def _nearest_interactable(self):
        candidates = []
        gather_distance = math.dist(self.pos, self.gather_portal)
        if gather_distance <= self.t["interact_radius"]:
            candidates.append((gather_distance, 0, ("", -1, "Gather"), "gather", None))
        for stove in self.stoves:
            distance = math.dist(self.pos, stove["pos"])
            if distance <= self.t["interact_radius"]:
                candidates.append((distance, 0, id_key(stove["id"]), "stove", stove))
        for table in self.tables:
            distance = math.dist(self.pos, table["pos"])
            if distance <= self.t["interact_radius"]:
                candidates.append((distance, 1, id_key(table["id"]), "table", table))
        if not candidates:
            return None
        _, _, _, kind, obj = min(candidates, key=lambda item: item[:3])
        return kind, obj

    def _interact_stove(self, stove):
        events = []
        if stove["state"] == "idle":
            candidates = [
                c for c in self.customers
                if c["state"] == "waiting" and c["order_status"] == "reserved"
            ]
            candidates.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"]), id_key(c["id"])))
            if not candidates:
                return events
            customer = candidates[0]
            dish_id = customer["dish_id"]
            reserved = customer["reserved"]
            if any(self.stock.get(kind, 0) < amount for kind, amount in reserved.items()):
                return events
            items = []
            for kind, amount in sorted(reserved.items()):
                self.stock[kind] = self.stock.get(kind, 0) - amount
                items.extend([kind] * amount)
            customer["order_status"] = "assigned"
            customer["reserved"] = {}
            stove["state"] = "cooking"
            stove["dish"] = dish_id
            stove["order_id"] = customer["id"]
            stove["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * TICK))
            stove["ready_ticks"] = 0
            events.append(("cook_started", {"stove_id": stove["id"], "order_id": customer["id"],
                                            "dish_id": dish_id,
                                            "items": sorted(items),
                                            "base_price": customer["base_price"]}))
        elif stove["state"] == "ready" and self.hand is None:
            customer = next((c for c in self.customers
                             if c["id"] == stove.get("order_id")), None)
            if customer is None:
                return events
            dish_id = stove["dish"]
            self.hand = {"order_id": customer["id"], "dish_id": dish_id,
                         "base_price": customer["base_price"]}
            stove["state"] = "idle"
            stove["dish"] = None
            stove["order_id"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            events.append(("dish_picked", {"stove_id": stove["id"], "order_id": customer["id"],
                                           "dish_id": dish_id}))
        return events

    def _interact_table(self, table):
        events = []
        if self.hand is None:
            return events
        customer = next((c for c in self.customers
                         if c["table_id"] == table["id"] and c["state"] == "waiting"), None)
        if customer is None or customer["id"] != self.hand["order_id"]:
            return events
        if customer["dish_id"] != self.hand["dish_id"]:
            return events
        ratio = (customer["patience_ticks_left"] /
                 float(self.patience_max))
        tip = int(math.floor(self.hand["base_price"] * self.t["tip_rate"])) \
            if ratio >= self.t["tip_min_patience_ratio"] else 0
        customer["state"] = "eating"
        customer["order_status"] = "served"
        customer["eat_ticks_left"] = self.eat_ticks
        customer["base_price"] = self.hand["base_price"]
        customer["tip"] = tip
        dish_id = customer["dish_id"]
        patience = customer["patience_ticks_left"]
        self.hand = None
        events.append(("served", {"order_id": customer["id"], "table_id": table["id"],
                                  "dish_id": dish_id, "patience_ticks_left": patience,
                                  "base_price": customer["base_price"], "tip": tip}))
        return events

    def _remove_finished_and_leave(self, closing):
        events = []
        for customer in sorted(list(self.customers), key=lambda c: id_key(c["id"])):
            if customer["state"] == "eating":
                if customer["eat_ticks_left"] == 0 or closing:
                    events.extend(self._pay_and_leave(customer,
                                                       "closing" if closing else "finished_eating"))
            elif customer["state"] == "waiting":
                if closing:
                    events.extend(self._leave_customer(customer, "closing"))
                elif customer["patience_ticks_left"] == 0:
                    events.extend(self._leave_customer(customer, "patience"))
        return events

    def _pay_and_leave(self, customer, reason):
        events = []
        base = customer["base_price"]
        tip = customer["tip"]
        amount = base + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self.reputation = min(self.t["reputation_max"],
                                  self.reputation + self.t["tip_reputation"])
        events.append(("paid", {"order_id": customer["id"], "table_id": customer["table_id"],
                                "base_price": base, "tip": tip, "amount": amount,
                                "reason": reason}))
        events.extend(self._leave_customer(customer, None))
        return events

    def _leave_customer(self, customer, reason):
        events = []
        if reason is not None:
            events.append(("customer_left", {"order_id": customer["id"],
                                             "table_id": customer["table_id"],
                                             "reason": reason,
                                             "reputation": self.reputation
                                             if reason == "closing"
                                             else max(self.t["reputation_min"],
                                                      self.reputation + self.t["left_reputation_delta"])}))
            if reason == "patience":
                self.reputation = max(self.t["reputation_min"],
                                      self.reputation + self.t["left_reputation_delta"])

        if customer in self.customers:
            self.customers.remove(customer)

        if customer["order_status"] == "reserved":
            customer["reserved"] = {}
        if self.hand is not None and self.hand["order_id"] == customer["id"]:
            self.hand = None
        for stove in self.stoves:
            if stove.get("order_id") == customer["id"]:
                stove["state"] = "idle"
                stove["dish"] = None
                stove["order_id"] = None
                stove["cook_ticks_left"] = 0
                stove["ready_ticks"] = 0
        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
