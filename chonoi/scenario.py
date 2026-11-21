"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks",
               "monsters", "ca_ho", "random_ho", "day", "active_upgrades"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks", "attack_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")
    if mode == "day":
        if not set(data) <= {"day", "gather", "quan"}:
            raise BadInput("scenario day chỉ được có khối day/gather/quan")
        day_block = data.get("day", {})
        gather_block = data.get("gather", {})
        quan_block = data.get("quan", {})
        if not isinstance(day_block, dict) or not isinstance(gather_block, dict) or not isinstance(quan_block, dict):
            raise BadInput("khối day/gather/quan phải là object")
        if "stock" in quan_block or "reputation" in quan_block:
            raise BadInput("day không cho quan.stock hoặc quan.reputation")
        _validate_gather(gather_block, tuning)
        _validate_quan(quan_block, tuning)
        _validate_day(day_block, tuning)
        return {"day": day_block, "gather": gather_block, "quan": quan_block}
    if not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp", "attack_cd_ticks"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    oxygen_level = int(b.get("active_upgrades", {}).get("oxygen", 0))
    oxygen_max_s = g["oxygen_max_s"]
    if oxygen_level:
        levels = tuning["shop"]["upgrades"]["oxygen"]
        if 1 <= oxygen_level <= len(levels):
            oxygen_max_s = levels[oxygen_level - 1]["oxygen_max_s"]
    omax = int(round(oxygen_max_s * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    hp_max = g["hp_max"]
    hp_level = int(b.get("active_upgrades", {}).get("hp", 0))
    if hp_level:
        levels = tuning["shop"]["upgrades"]["hp"]
        if 1 <= hp_level <= len(levels):
            hp_max = levels[hp_level - 1]["hp_max"]
    if "hp" in p and not (1 <= p["hp"] <= hp_max):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    if "monsters" in b:
        monsters = b["monsters"]
        if not isinstance(monsters, list):
            raise BadInput("monsters phải là mảng")
        _check_ids("monsters", monsters)
        known = set(tuning["gather"]["monsters"]["species"])
        for monster in monsters:
            if monster.get("kind") not in known:
                raise BadInput(f"monsters.{monster['id']}: kind không hợp lệ")
            _pos(f"monsters.{monster['id']}.pos", monster.get("pos"), bounds)
            waypoints = monster.get("waypoints")
            if not isinstance(waypoints, list) or len(waypoints) != 2:
                raise BadInput(f"monsters.{monster['id']}: cần 2 waypoint")
            for waypoint in waypoints:
                _pos(f"monsters.{monster['id']}.waypoints", waypoint, bounds)


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r):
            raise BadInput("reputation phải là số")
        if not (tuning["quan"]["reputation_min"] <= r <= tuning["quan"]["reputation_max"]):
            raise BadInput("reputation ngoài miền")
    if "hand" in b:
        hand = b["hand"]
        if hand is not None:
            if not isinstance(hand, dict):
                raise BadInput("hand phải là payload món hoặc null")
            if set(hand) - {"order_id", "dish_id", "base_price"}:
                raise BadInput("hand có trường lạ")
            if not isinstance(hand.get("order_id"), str) or not isinstance(hand.get("dish_id"), str):
                raise BadInput("hand.order_id và hand.dish_id phải là chuỗi")
            if hand["dish_id"] not in tuning["menu"]:
                raise BadInput("hand chứa món ngoài phạm vi")
            if isinstance(hand.get("base_price"), bool) or not isinstance(hand.get("base_price"), int) or hand["base_price"] <= 0:
                raise BadInput("hand.base_price phải là số nguyên dương")
            if hand["base_price"] != tuning["menu"][hand["dish_id"]]["price"]:
                raise BadInput("hand.base_price không khớp món")
    for table in b.get("tables", []):
        extra = set(table) - {"id", "pos"}
        if extra:
            raise BadInput(f"tables.{table['id']} có trường lạ: {sorted(extra)}")
        if "pos" in table:
            _pos(f"tables.{table['id']}.pos", table["pos"], tuning["quan"]["bounds"], axes=("x", "z"))
    known_stoves = {s["id"] for s in tuning["quan"]["stoves"]}
    for stove in b.get("stoves", []):
        extra = set(stove) - {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks", "order_id"}
        if extra:
            raise BadInput(f"stoves.{stove['id']} có trường lạ: {sorted(extra)}")
        if "pos" in stove:
            _pos(f"stoves.{stove['id']}.pos", stove["pos"], tuning["quan"]["bounds"], axes=("x", "z"))
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in stove:
                _nonneg_int(f"stoves.{stove['id']}.{key}", stove[key])
        if "state" in stove and stove["state"] not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{stove['id']}: state không hợp lệ")
        if "dish" in stove and stove["dish"] is not None and stove["dish"] not in tuning["menu"]:
            raise BadInput(f"stoves.{stove['id']}: dish ngoài phạm vi")
        if stove["id"] not in known_stoves:
            raise BadInput(f"stoves.{stove['id']}: id bếp không tồn tại")
        state = stove.get("state", "idle")
        if state == "idle":
            if stove.get("dish") is not None or stove.get("cook_ticks_left", 0) != 0:
                raise BadInput(f"stoves.{stove['id']}: fixture idle không nhất quán")
        elif state == "cooking":
            if not isinstance(stove.get("dish"), str) or not isinstance(stove.get("order_id"), str):
                raise BadInput(f"stoves.{stove['id']}: cooking cần dish và order_id")
            if stove.get("cook_ticks_left", 0) <= 0:
                raise BadInput(f"stoves.{stove['id']}: cooking cần timer dương")
        elif state == "ready":
            if not isinstance(stove.get("dish"), str) or not isinstance(stove.get("order_id"), str):
                raise BadInput(f"stoves.{stove['id']}: ready cần dish và order_id")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
        allowed = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                   "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
        extra = set(c) - allowed
        if extra:
            raise BadInput(f"customers.{c['id']} có trường lạ: {sorted(extra)}")
        dish_id = c.get("dish_id")
        if not isinstance(dish_id, str) or dish_id not in tuning["menu"]:
            raise BadInput(f"customers.{c['id']}: dish_id ngoài phạm vi")
        if "order_tick" in c:
            _nonneg_int(f"customers.{c['id']}.order_tick", c["order_tick"])
        if "patience_ticks_left" in c:
            _nonneg_int(f"customers.{c['id']}.patience_ticks_left", c["patience_ticks_left"])
        if "eat_ticks_left" in c:
            _nonneg_int(f"customers.{c['id']}.eat_ticks_left", c["eat_ticks_left"])
        if "patience_ticks_left" in c and c["patience_ticks_left"] > int(round(tuning["quan"]["patience_s"] * 60)):
            raise BadInput(f"customers.{c['id']}: patience_ticks_left vượt kiên nhẫn tối đa")
        if "eat_ticks_left" in c and c["eat_ticks_left"] > int(round(tuning["quan"]["eat_s"] * 60)):
            raise BadInput(f"customers.{c['id']}: eat_ticks_left vượt thời gian ăn tối đa")
        state = c.get("state", "waiting")
        if state not in ("waiting", "eating"):
            raise BadInput(f"customers.{c['id']}: state không hợp lệ")
        order_status = c.get("order_status", "reserved")
        if order_status not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"customers.{c['id']}: order_status không hợp lệ")
        if order_status == "reserved" and state != "waiting":
            raise BadInput(f"customers.{c['id']}: reserved phải đang waiting")
        if order_status == "served" and state != "eating":
            raise BadInput(f"customers.{c['id']}: served phải đang eating")
        if order_status == "reserved":
            reserved = c.get("reserved", tuning["menu"][dish_id]["recipe"])
            try:
                validate_items(reserved)
            except BadInput:
                raise BadInput(f"customers.{c['id']}: reserved không hợp lệ")
            if reserved != tuning["menu"][dish_id]["recipe"]:
                raise BadInput(f"customers.{c['id']}: reserved khác công thức")
        if "reserved" in c:
            reserved = c["reserved"]
            if not isinstance(reserved, dict):
                raise BadInput(f"customers.{c['id']}: reserved phải là object")
            try:
                validate_items(reserved)
            except BadInput:
                raise BadInput(f"customers.{c['id']}: reserved không hợp lệ")
        if "base_price" in c:
            price = c["base_price"]
            if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
                raise BadInput(f"customers.{c['id']}: base_price phải là số nguyên dương")
            if price != tuning["menu"][dish_id]["price"]:
                raise BadInput(f"customers.{c['id']}: base_price không khớp món")
        if "tip" in c:
            tip = c["tip"]
            if isinstance(tip, bool) or not isinstance(tip, int) or tip < 0:
                raise BadInput(f"customers.{c['id']}: tip phải là số nguyên không âm")
        if state == "eating":
            if order_status != "served":
                raise BadInput(f"customers.{c['id']}: khách eating phải served")
            if c.get("eat_ticks_left", 0) <= 0:
                raise BadInput(f"customers.{c['id']}: eating cần eat_ticks_left dương")
            if "base_price" not in c or "tip" not in c:
                raise BadInput(f"customers.{c['id']}: eating cần base_price và tip")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")

    for c in b.get("customers", []):
        status = c.get("order_status", "reserved")
        if status in ("assigned", "unfulfillable"):
            if c.get("reserved", {}) != {}:
                raise BadInput(f"customers.{c['id']}: giữ chỗ phải rỗng")
        if status == "unfulfillable" and c.get("state", "waiting") != "waiting":
            raise BadInput(f"customers.{c['id']}: unfulfillable phải đang waiting")
        if status == "assigned":
            locations = 0
            for stove in b.get("stoves", []):
                if stove.get("order_id") == c["id"] and stove.get("dish") == c["dish_id"]:
                    locations += 1
            hand = b.get("hand")
            if hand is not None and hand.get("order_id") == c["id"]:
                if hand.get("dish_id") != c["dish_id"]:
                    raise BadInput(f"customers.{c['id']}: món trên tay không khớp")
                locations += 1
            if locations != 1:
                raise BadInput(f"customers.{c['id']}: đơn assigned phải có đúng một món")
    hand = b.get("hand")
    if hand is not None:
        customer_ids = {c["id"] for c in b.get("customers", [])}
        if hand["order_id"] not in customer_ids:
            raise BadInput("hand.order_id không tham chiếu khách có thật")


def _validate_day(day_block, tuning):
    allowed = {"money", "earned", "reputation", "upgrades", "day_plan"}
    extra = set(day_block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    money = day_block.get("money", 0)
    earned = day_block.get("earned", 0)
    if isinstance(money, bool) or not isinstance(money, int) or money < 0:
        raise BadInput("day.money phải là số nguyên không âm")
    if isinstance(earned, bool) or not isinstance(earned, int) or earned < 0:
        raise BadInput("day.earned phải là số nguyên không âm")
    if money > earned:
        raise BadInput("day.money không được vượt earned")
    if "reputation" in day_block:
        reputation = day_block["reputation"]
        if not _num(reputation):
            raise BadInput("day.reputation phải là số")
        if not (tuning["quan"]["reputation_min"] <= reputation <= tuning["quan"]["reputation_max"]):
            raise BadInput("day.reputation ngoài miền")
    upgrades = day_block.get("upgrades", {})
    if not isinstance(upgrades, dict):
        raise BadInput("day.upgrades phải là object")
