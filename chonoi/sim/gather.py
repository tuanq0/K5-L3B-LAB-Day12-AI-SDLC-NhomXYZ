"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  TODO(nhóm, lát 1): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids):
        t = tuning["gather"]
        self.t = t
        active_upgrades = scenario.get("active_upgrades", {})
        oxygen_level = int(active_upgrades.get("oxygen", 0))
        hp_level = int(active_upgrades.get("hp", 0))
        oxygen_max_s = t["oxygen_max_s"]
        hp_max = t["hp_max"]
        shop = tuning.get("shop", {}).get("upgrades", {})
        if oxygen_level:
            levels = shop.get("oxygen", [])
            if 1 <= oxygen_level <= len(levels):
                oxygen_max_s = levels[oxygen_level - 1]["oxygen_max_s"]
        if hp_level:
            levels = shop.get("hp", [])
            if 1 <= hp_level <= len(levels):
                hp_max = levels[hp_level - 1]["hp_max"]
        self.t = dict(t)
        self.t["oxygen_max_s"] = oxygen_max_s
        self.t["hp_max"] = hp_max
        t = self.t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.phase_tick = 0
        self.random_fish = scenario.get("random_fish", True)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        # Đàn cá đứng yên ở phase này. Cá bơi / sinh thêm là việc của phase sau.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0),
                      "age_ticks": f.get("age_ticks", 0)} for f in src_fish]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        monster_cfg = t.get("monsters", {})
        monster_species = monster_cfg.get("species", {})
        src_monsters = scenario.get("monsters")
        if src_monsters is None:
            src_monsters = [
                dict(m) for m in monster_cfg.get("spawns", [])
                if int(m.get("from_day", 1)) <= int(scenario.get("day", 1))
            ]
        self.monsters = []
        for m in src_monsters:
            waypoints = [[float(c) for c in w] for w in m.get("waypoints", [m["pos"]])]
            if len(waypoints) == 1:
                waypoints.append([float(c) for c in waypoints[0]])
            self.monsters.append({
                "id": m["id"], "kind": m["kind"],
                "pos": [float(c) for c in m["pos"]],
                "waypoints": waypoints,
                "target_idx": int(m.get("target_idx", 1)),
                "state": m.get("state", "patrol"),
                "state_ticks_left": int(m.get("state_ticks_left", 0)),
                "recoil_dir": list(m["recoil_dir"]) if m.get("recoil_dir") is not None else None,
            })
        self.monster_species = monster_species
        for monster in self.monsters:
            ids.reserve(monster["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None
        self.paused = False

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{
                "id": m["id"], "kind": m["kind"], "pos": m["pos"],
                "waypoints": m["waypoints"], "target_idx": m["target_idx"],
                "state": m["state"], "state_ticks_left": m["state_ticks_left"],
                "recoil_dir": m["recoil_dir"],
            } for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
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
        invulnerable = self.invuln_ticks > 0
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép
        before_d = self.pos[1]
        self._move(inp)
        after_d = self.pos[1]
        surface_depth = self.t["surface_depth"]
        if before_d <= surface_depth and after_d > surface_depth:
            events.append(("dive", {"pos": [self.pos[0], self.pos[1]]}))
        elif before_d > surface_depth and after_d <= surface_depth:
            events.append(("surface", {"pos": [self.pos[0], self.pos[1]]}))

        old_oxygen = self.oxygen_ticks
        if after_d <= surface_depth:
            self.oxygen_ticks = min(self.oxygen_max,
                                    self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if old_oxygen > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp == 0:
                        lost = list(reversed(self.hold))
                        self.hold = []
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events
        monster_result = self._update_monsters(invulnerable)
        events.extend(monster_result)
        if self.done:
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if after_d <= surface_depth:
                candidates = [n for n in self.nodes
                              if n["regrow_ticks"] == 0
                              and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]]
                candidates.sort(key=lambda n: (math.dist(self.pos, n["pos"]), id_key(n["id"])))
                if candidates:
                    node = candidates[0]
                    amount = int(self.t["node_yield"])
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free >= amount:
                        for _ in range(amount):
                            self.hold.append(node["kind"])
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"],
                                                  "kind": node["kind"], "amount": amount}))
                    else:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                                     "required": amount, "free": free}))
        # 4. bắt cá
        if inp.pressed("catch"):
            if self.catch_cd_ticks == 0 and after_d > surface_depth:
                candidates = [f for f in self.fish
                              if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]]
                candidates.sort(key=lambda f: (math.dist(self.pos, f["pos"]), id_key(f["id"])))
                if candidates:
                    fish = candidates[0]
                    yield_count = int(self.t["fish_yield"][fish["kind"]])
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free >= yield_count:
                        for _ in range(yield_count):
                            self.hold.append(fish["kind"])
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"],
                                                       "yield": yield_count}))
                    else:
                        events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                                     "required": yield_count, "free": free}))
        if not self.done:
            fish_events = self._update_fish()
            events.extend(fish_events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    def _update_monsters(self, invulnerable):
        events = []
        bounds = self.t["bounds"]

        for monster in sort_by_id(self.monsters):
            species = self.monster_species.get(monster["kind"], {})
            if monster["state"] == "recoil":
                step = float(species.get("recoil_dist", 2)) / TICK
                direction = monster["recoil_dir"] or [1.0, 0.0]
                monster["pos"][0] += direction[0] * step
                monster["pos"][1] += direction[1] * step
                monster["pos"][0] = max(bounds["x"][0], min(bounds["x"][1], monster["pos"][0]))
                depth_lo, depth_hi = species.get("depths", [10, 30])
                monster["pos"][1] = max(depth_lo, min(depth_hi, monster["pos"][1]))
                monster["state_ticks_left"] = max(0, monster["state_ticks_left"] - 1)
                if monster["state_ticks_left"] == 0:
                    monster["state"] = "patrol"
                    monster["recoil_dir"] = None
                continue

            distance = math.dist(self.pos, monster["pos"])
            depth_lo = species.get("depths", [10, 30])[0]
            detect = float(species.get("detect_radius", 10))
            exit_radius = float(species.get("exit_radius", 16))

            if self.pos[1] >= depth_lo and distance <= detect:
                monster["state"] = "chase"
            elif monster["state"] == "chase" and (
                distance > exit_radius or self.pos[1] < depth_lo
            ):
                monster["state"] = "patrol"

            if monster["state"] == "chase":
                speed = float(species.get("chase_speed", 3.0)) / TICK
                dx = self.pos[0] - monster["pos"][0]
                dd = self.pos[1] - monster["pos"][1]
                length = math.hypot(dx, dd)
                if length > 0:
                    travel = min(speed, length)
                    monster["pos"][0] += dx / length * travel
                    monster["pos"][1] += dd / length * travel
            else:
                monster["state"] = "patrol"
                speed = float(species.get("patrol_speed", 1.0)) / TICK
                target_idx = monster["target_idx"]
                target = monster["waypoints"][target_idx]
                dx = target[0] - monster["pos"][0]
                dd = target[1] - monster["pos"][1]
                length = math.hypot(dx, dd)
                if length <= speed:
                    monster["pos"] = [float(target[0]), float(target[1])]
                    monster["target_idx"] = 1 - target_idx
                elif length > 0:
                    monster["pos"][0] += dx / length * speed
                    monster["pos"][1] += dd / length * speed

            monster["pos"][0] = max(bounds["x"][0], min(bounds["x"][1], monster["pos"][0]))
            depth_lo, depth_hi = species.get("depths", [10, 30])
            monster["pos"][1] = max(depth_lo, min(depth_hi, monster["pos"][1]))

        if invulnerable:
            return events

        candidates = []
        for monster in self.monsters:
            species = self.monster_species.get(monster["kind"], {})
            depth_lo = species.get("depths", [10, 30])[0]
            distance = math.dist(self.pos, monster["pos"])
            if (self.pos[1] >= depth_lo
                    and distance <= float(species.get("hit_radius", 1.5))
                    and monster["state"] != "recoil"):
                candidates.append((distance, id_key(monster["id"]), monster))
        if candidates:
            monster = min(candidates, key=lambda candidate: candidate[:2])[2]
            lost_count = len(self.hold) // 2
            lost = list(reversed(self.hold))[:lost_count]
            if lost_count:
                del self.hold[-lost_count:]
            self.hp = max(0, self.hp - 1)
            self.invuln_ticks = int(self.t.get("invuln_ticks", 90))
            species = self.monster_species.get(monster["kind"], {})
            dx = monster["pos"][0] - self.pos[0]
            dd = monster["pos"][1] - self.pos[1]
            length = math.hypot(dx, dd)
            if length == 0:
                recoil_dir = [1.0, 0.0]
            else:
                recoil_dir = [dx / length, dd / length]
            monster["state"] = "recoil"
            monster["state_ticks_left"] = int(species.get("recoil_ticks", 60))
            monster["recoil_dir"] = recoil_dir
            events.append(("monster_hit", {
                "monster_id": monster["id"],
                "hp": self.hp,
                "lost": lost,
                "pos": [self.pos[0], self.pos[1]],
            }))
            if self.hp == 0:
                lost_all = list(reversed(self.hold))
                self.hold = []
                events.append(("faint", {"cause":"monster","lost":lost_all,"hp":0}))
                self._finish("fainted", events)
        return events

    def _update_fish(self):
        events = []
        if not self.random_fish:
            return events

        speed = float(self.t.get("fish_speed", 1.5))
        turn_ticks = int(self.t.get("fish_turn_ticks", 120))
        x_bounds = self.t.get("fish_x", [4, 96])
        depths = self.t.get("fish_depths", {})

        for fish in sort_by_id(self.fish):
            fish["age_ticks"] = fish.get("age_ticks", 0) + 1
            if fish["age_ticks"] % turn_ticks == 0:
                fish["heading_deg"] = float(self.rng.get("fish_turn").uniform(0, 360))

            angle = math.radians(fish.get("heading_deg", 0))
            dx = math.cos(angle) * speed / TICK
            dd = math.sin(angle) * speed / TICK
            lo_x, hi_x = x_bounds
            dlo, dhi = depths.get(fish["kind"], [0, 30])

            fish["pos"][0] += dx
            fish["pos"][1] += dd
            if fish["pos"][0] < lo_x:
                fish["pos"][0] = lo_x + (lo_x - fish["pos"][0])
                fish["heading_deg"] = (180 - fish["heading_deg"]) % 360
            elif fish["pos"][0] > hi_x:
                fish["pos"][0] = hi_x - (fish["pos"][0] - hi_x)
                fish["heading_deg"] = (180 - fish["heading_deg"]) % 360
            if fish["pos"][1] < dlo:
                fish["pos"][1] = dlo + (dlo - fish["pos"][1])
                fish["heading_deg"] = (-fish["heading_deg"]) % 360
            elif fish["pos"][1] > dhi:
                fish["pos"][1] = dhi - (fish["pos"][1] - dhi)
                fish["heading_deg"] = (-fish["heading_deg"]) % 360

        spawn_ticks = int(self.t.get("fish_spawn_ticks", 360))
        max_fish = int(self.t.get("fish_max", 12))
        if self.phase_tick % spawn_ticks == 0 and len(self.fish) < max_fish:
            clearance = float(self.t.get("fish_spawn_clearance", 1))
            spawn_x = self.t.get("fish_spawn_x", [15,30,45,60,75,90])
            spawn_depths = self.t.get("fish_spawn_depths", {})
            weights = self.t.get("fish_weights", {})
            valid_kinds = []
            for kind in ("ca_linh", "ca_loc", "ca_keo"):
                points = [(x, d) for x in spawn_x for d in spawn_depths.get(kind, [])]
                if any(all(math.dist([x, d], f["pos"]) > clearance for f in self.fish)
                       for x, d in points):
                    valid_kinds.append(kind)
            if valid_kinds:
                total = sum(float(weights.get(k, 0)) for k in valid_kinds)
                roll = self.rng.get("fish_spawn").random() * total
                kind = valid_kinds[-1]
                upto = 0
                for candidate in valid_kinds:
                    upto += float(weights.get(candidate, 0))
                    if roll < upto:
                        kind = candidate
                        break
                points = [(x, d) for x in spawn_x for d in spawn_depths.get(kind, [])
                          if all(math.dist([x, d], f["pos"]) > clearance for f in self.fish)]
                if points:
                    pos = self.rng.get("fish_spawn").choice(points)
                    fish_id = self.ids.new("F")
                    heading = float(self.rng.get("fish_spawn").uniform(0, 360))
                    self.fish.append({"id":fish_id,"kind":kind,"pos":[float(pos[0]),float(pos[1])],
                                      "heading_deg":heading,"age_ticks":0})
                    events.append(("fish_spawned", {"id": fish_id, "kind": kind,
                                                    "pos": [float(pos[0]), float(pos[1])]}))
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
