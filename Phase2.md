Phase 2 · hạn tag phase-2 lúc 1:55 · phát hành 10:19

TICKET-02 — Một ngày ở chợ nổi (Phase 2)
55 phút (1:00–1:55) · Test Contract v1.1 · Hạn đẩy tag phase-2 1:55.

Hai buổi đã nối được. Khách hàng chốt số liệu chuẩn và muốn chơi trọn một vòng ngày. Sáng, Út Sen xem thực đơn để biết cần tìm nguyên liệu gì. Tối, quán dùng phần mang về để phục vụ. Cuối ngày, người chơi dùng tiền mua nâng cấp cho lần lặn sau.

1. Lõi (mọi nhóm) — Số liệu chuẩn
Thay số đã chọn ở Phase 1 bằng các giá trị dưới đây. Cập nhật cấu hình, spec và test cùng lúc. Tiền tính theo nghìn đồng, mô phỏng chạy 60 tick/s.

1.1. Buổi sáng — Lặn & Hái
Hằng số	Giá trị chuẩn
Thời lượng	180 s (10.800 tick).
Vùng nước	x ∈ [0,100], d ∈ [0,30]. Chặn ở các mép. Mặt nước ở d ≤ 0.5. Các vùng gồm nông d < 10, giữa 10 ≤ d < 20, sâu d ≥ 20.
Bến và xuất phát	Bến tâm [2,0], bán kính 3 m. Xuất phát [2,0], hướng 0° (+x).
Bơi	4.0 m/s, đạt tốc độ hoặc dừng trong ≤ 0.1 s (6 tick).
Oxy và ngạt	Cơ sở 30 s (1.800 tick). Dưới nước −1 oxy/tick, mặt nước +6/tick, kẹp ở mức tối đa. Ở dưới nước với oxy bằng 0, mất 1 Máu mỗi 60 tick, tính cả bước vừa chạm 0. Reset nhịp khi oxy > 0 hoặc lên mặt nước. Ngạt xuyên bất tử và không làm rơi hàng.
Giỏ và hái	12 ô, mỗi nguyên liệu 1 ô. Hái ở mặt nước trong ≤ 2.0 m, lấy 1, mọc lại sau 20 s (1.200 tick). Xét bến trước nút hái.
Nút hái	Bông điên điển N1 [12,0], N2 [28,0] · Bông súng N3 [44,0], N4 [60,0] · Kèo nèo N5 [76,0], N6 [90,0].
Bắt cá	catch (Space), chỉ dưới nước, chọn đàn gần nhất trong ≤ 2.0 m, hòa theo id. Cần đủ chỗ cho cả đàn. Hồi 0.5 s (30 tick) tính từ lần bắt thành công. Yield cá linh 3, cá lóc 1, cá kèo 2.
Đàn cá bơi	1.5 m/s trong x ∈ [4,96]. Cá linh bơi ở d ∈ [3,12], cá lóc [8,20] và cá kèo [22,28]. Đổi hướng theo seed ở bước bơi thứ 120, 240… trước khi di chuyển. Tới mép thì phản xạ phần quãng đường còn lại và đảo thành phần hướng vuông góc với mép, chạm góc đảo cả hai.
Điểm sinh	x ∈ {15,30,45,60,75,90}. Cá linh sinh ở d ∈ {5,10}, cá lóc {10,16} và cá kèo {24,27}. Có 36 cặp loài–vị trí, trong đó 30 vị trí hình học khác nhau.
Sinh cá	Đầu ca 8 đàn ở 8 điểm khác nhau, trần 12 đàn. Tại phase_tick = 360·k (k ≥ 1), sau khi cá bơi, sinh tối đa một đàn nếu còn dưới trần và có điểm cách mọi đàn đang sống > 1 m. Bỏ lượt nếu hết điểm. Loài được chọn với trọng số linh 40%, lóc 30%, kèo 30%, chuẩn hóa lại theo các loài còn điểm hợp lệ. Sau đó chọn đều một điểm của loài và lấy hướng ban đầu theo seed. Cá mới tham gia từ bước sau.
Kết thúc	docked khi tương tác trong bán kính bến, time khi hết giờ ở bất kỳ độ sâu nào. Cả hai giữ phần còn trong giỏ. fainted khi Máu bằng 0, mất toàn bộ giỏ.
1.2. Cá Sấu Năm Chèo, Máu và ngất
Máu cơ sở 3, hồi đầy đầu mỗi Ngày. Cá Sấu ở d ∈ [10,30]. M1 tuần tra từ [60,24] đến [64,24]. M2 từ Ngày 3, tuần tra từ [85,18] đến [89,18]. Waypoint đầu là vị trí xuất phát. Trong gather độc lập, dùng bố trí Ngày 1.
patrol đi 1.0 m/s tới waypoint, đổi sang mục tiêu kia cho bước sau khi đến. Nếu người chơi ở d ≥ 10 và cách ≤ 10 m, chuyển chase và bơi về phía người chơi ở 3.0 m/s. Trở về patrol khi cách > 16 m hoặc người chơi lên d < 10. Chặn Cá Sấu theo biên map và dải độ sâu của loài.
Sau khi cả hai di chuyển, nếu khoảng cách ≤ 1.5 m, người chơi ở d ≥ 10 và hết bất tử, chạm làm mất 1 Máu, bỏ floor(số đang mang/2) nguyên liệu theo LIFO (nhặt sau mất trước) và đặt bất tử 90 tick. Mỗi bước tối đa một hit, chọn con gần nhất, hòa theo id. Trong thời gian bất tử không phát hit hay chuyển Cá Sấu sang recoil do chạm.
Con gây hit vào recoil 60 bước tính từ bước sau, lùi theo hướng xa người chơi đã chốt lúc chạm (trùng tâm dùng +x), mỗi bước 2/60 m trước chặn mép và không gây hit. Hết recoil về patrol, xét phát hiện/chạm từ bước kế. Máu chạm 0 thì ngất ngay và vẫn mở quán tối với kho bàn giao rỗng.
1.3. Buổi tối — Mở Quán
Hằng số	Giá trị chuẩn
Thời lượng	180 s (10.800 tick).
Phòng / xuất phát / đi	x ∈ [0,16], z ∈ [0,10] / [8,5] / 4.0 m/s, đạt tốc độ hoặc dừng trong ≤ 6 tick. Chặn biên và đi xuyên nội thất.
Bếp	B1 [2,8], B2 [5,8].
Bàn	T1 [9,2], T2 [13,2], T3 [9,6], T4 [13,6].
Tương tác	≤ 1.5 m. Chọn gần nhất, hòa ưu tiên bếp trước bàn rồi id. Tay cầm 1 món. Bếp lấy đơn reserved cũ nhất theo order_tick rồi id bàn.
Khách	Lượt đầu tick 120, sau đó 120 + 900·k (k ≥ 0), nếu có bàn trống. Đến ghế trống id nhỏ nhất, giữ nguyên liệu khi gọi món. Kiên nhẫn 60 s (3.600 tick), ăn 10 s (600 tick).
Boa và uy tín	Boa floor(giá × 0.2) nếu còn ≥ 50% kiên nhẫn (≥ 30 s) lúc giao. Khi thu boa dương, uy tín +0.2. Uy tín đầu game 3.0, kẹp [0,5]. Khách hết kiên nhẫn khi ca còn giờ làm giảm 0.5.
Đóng ca	Khách còn ăn trả ngay, khách còn chờ rời mà không trừ uy tín. Dọn món và phần giữ của đơn. burn_s: null trong lõi.
Điểm	earned + 100 × floor(reputation). earned là tổng thu, gồm tiền món và boa.
Thực đơn. Lưu công thức, thời gian nấu và giá dưới dạng dữ liệu. Hai nguyên liệu mới là ca_keo (cá kèo) và keo_neo (kèo nèo).

ID	Món	Công thức	Nấu	Giá
ca_loc_nuong_trui	Cá lóc nướng trui	ca_loc ×1	6 s	60
goi_bong_sung	Gỏi bông súng	bong_sung ×2	4 s	40
lau_ca_linh_dien_dien	Lẩu cá linh bông điên điển	ca_linh ×3 + bong_dien_dien ×1	10 s	120
canh_chua_ca_loc	Canh chua cá lóc bông điên điển	ca_loc ×1 + bong_dien_dien ×1	8 s	90
ca_keo_nuong	Cá kèo nướng muối ớt	ca_keo ×2	6 s	70
lau_mam	Lẩu mắm miền Tây	ca_linh ×2 + ca_keo ×1 + keo_neo ×1 + bong_dien_dien ×1	12 s	200
2. Lõi — Vòng ngày, kế hoạch và Shop
Vòng ngày và kế hoạch
DayIntro → gather → EveningIntro → quan → DayResult → Shop → DayIntro (hoặc tổng kết sau Ngày 5).

Đầu Ngày, Má Tư công bố món định nấu và tổng nguyên liệu cần lấy. HUD sáng hiển thị đã lấy/cần. Khi cập bến, hết giờ hoặc ngất, quán mở với kho bàn giao. Tiền, earned, uy tín và cấp nâng cấp giữ qua Ngày. Oxy và Máu hồi đầy theo cấp có hiệu lực, giỏ làm mới và kho dư bị bỏ sau Shop.
Trong day, khách chọn đều theo seed từ các id món trong kế hoạch có đủ nguyên liệu sau khi trừ phần đang giữ. Số suất trong kế hoạch dùng để tính mục tiêu thu gom. Khách có thể gọi tiếp món đủ nguyên liệu kể cả khi đã bán đủ số suất dự kiến. Quán chạy riêng dùng cả 6 món. Có bàn mà thiếu món thì no_dish. Không có thưởng riêng khi lấy đủ danh sách.
Ngày chỉ hoàn tất khi Shop đóng, kể cả Ngày cuối. Một Ngày không pause dài tối đa 22.200 tick. Shop có thể đóng sớm.
Ngày	Món và số suất kế hoạch	Nguyên liệu cần	Số ô cần (thực tế nếu bắt theo đàn)
D1	ca_loc_nuong_trui ×3, goi_bong_sung ×3	ca_loc ×3, bong_sung ×6	9
D2	ca_loc_nuong_trui ×2, lau_ca_linh_dien_dien ×2	ca_loc ×2, ca_linh ×6, bong_dien_dien ×2	10
D3	goi_bong_sung ×2, canh_chua_ca_loc ×2, ca_keo_nuong ×2	bong_sung ×4, ca_loc ×2, bong_dien_dien ×2, ca_keo ×4	12
D4	lau_mam ×1, ca_loc_nuong_trui ×2, goi_bong_sung ×1	ca_linh ×2, ca_keo ×1, keo_neo ×1, bong_dien_dien ×1, ca_loc ×2, bong_sung ×2	9 (11)
D5	lau_mam ×1, lau_ca_linh_dien_dien ×1, ca_loc_nuong_trui ×1	ca_linh ×5, ca_keo ×1, keo_neo ×1, bong_dien_dien ×2, ca_loc ×1	10 (12)
Shop và nâng cấp
ID	Nâng cấp	Cấp 1	Cấp 2
oxygen	Bình oxy	200 → 45 s (2.700 tick)	400 → 60 s (3.600 tick)
hp	Áo phao (thêm Máu)	250 → 4 Máu	500 → 5 Máu
Nâng cấp theo dữ liệu, mua cấp kế tiếp một lần mỗi cấp. Đủ đúng giá vẫn mua được. Trừ vào money, giữ earned và điểm. Cấp vừa mua hiển thị ngay, có hiệu lực từ Ngày kế tiếp. Không đủ tiền hoặc đã tối đa thì buy_failed, tiền và cấp giữ nguyên. Shop chờ shop_done hoặc tự đóng sau 600 tick hoạt động.

Menu, pause và HUD
Menu chính có Chơi và Thoát. DayIntro hiện Ngày và danh sách Má Tư đọc, tự chuyển sau 4 s hoặc khi nhấn phím. EveningIntro hiện số lượng nhập kho và món nấu được. DayResult hiện khách đã phục vụ/bỏ đi, tiền, boa và thay đổi uy tín. Summary hiện tổng tiền, tổng điểm, uy tín, món bán chạy.
Esc/P tạm dừng. Menu pause làm mờ nền, có Tiếp tục và Về menu, thêm Cài đặt nếu có mở rộng. Dừng đồng hồ và mọi timer gameplay, kể cả trong Shop.
HUD sáng có Máu, oxy (dưới 25% đổi màu/nhấp nháy), thời gian (đổi màu còn ≤ 30 s), độ sâu, giỏ theo loại, danh sách cần lấy và hồi bắt. Hiện gợi ý hái/cập bến khi đến gần, “Thủy quái!” cùng viền tím khi có thủy quái gần và “Hết hơi!” khi oxy cạn. HUD quán có đồng hồ ca, tiền ca và uy tín, món và kiên nhẫn tại từng bàn (đổi màu khi < 25%), tiến độ bếp/trạng thái món chín, món đang cầm và kho khả dụng. Chữ không chân ≥ 18 px ở 1280×720.
Trên máy chấm, headless một Ngày không pause (≤ 22.200 tick) chạy ≤ 20 s. Bản chơi thường đạt trung bình ≥ 30 FPS ở 1280×720.
3. Mở rộng
Kỳ vọng tính cả buổi lab. Nhóm 4 người không bắt buộc, nhóm 5 hoàn thành ít nhất 1 mục, nhóm 6 ít nhất 2 mục. Hoàn thành lõi trước. Ghi mục đã làm trong README, kèm bằng chứng. Với các mục có mã trong Test Contract, khai mã ở extensions tại gốc manifest.

Tự do sáng tạo. Khi lõi đã đúng, nhóm có thể thêm ý tưởng riêng, như món ăn hoặc câu chuyện. Tắt phần tự thêm ở headless hoặc giữ nguyên kết quả theo Test Contract. Ghi vào mục “Sáng tạo của nhóm” trong README.md, kèm bằng chứng ngắn cho thấy lõi vẫn đúng.

Mở rộng	Luật
Lao xua + weapon	Q (attack), cần mua cấp 1. Hồi 3 s (180 tick) từ lần dùng hợp lệ, kể cả không trúng. Cấp 1 giá 300, bán kính 4 m, choáng 2 s. Cấp 2 giá 600, bán kính 6 m, choáng 3 s. Duyệt mục tiêu theo id, đẩy mỗi con 3 m ra xa (chặn mép, trùng tâm dùng +x), choáng ghi đè recoil/choáng cũ. Đứng yên và không hit trong 120/180 bước kể cả bước bị Lao. Hết choáng về patrol ở vị trí sau đẩy.
Vợt hút cá + net	Cấp 1 giá 250, 4.0 m, tối đa 2 đàn/lần. Cấp 2 giá 500, 6.0 m, tối đa 3 đàn/lần. Từ cấp 1 duyệt theo id, đếm số đàn bắt thành công. Đàn thiếu chỗ phát hold_full và giữ lại, được xét đàn kế. Có đàn bắt thành công mới đặt hồi. Cấp 0 dùng luật gần nhất của lõi.
Rắn Hổ Mây (snake)	M3 từ Ngày 1, [72,14] ↔ [76,14], d ∈ [8,20]. Patrol 1.0 m/s, chase 3.5 m/s, phát hiện ≤ 8 m, rời chase khi > 16 m hoặc người chơi lên d < 8. Dùng luật chạm/recoil chung và ngưỡng độ sâu của loài.
Cháy món (burn)	burn_s: 20. Nếu ready_ticks > 1200, bỏ món, nguyên liệu mất, bếp rảnh ngay. Thử giữ lại ngay cho đơn. Đủ thì reserved, nếu thiếu thì unfulfillable, khách tiếp tục chờ tới hết kiên nhẫn. Đúng 1.200 tick vẫn bưng được.
Chợ Chú Sáu (vendor)	Trong Shop, bán cá lóc với giá 20, cá linh 8, cá kèo 10 và mỗi loại bông điên điển, bông súng, kèo nèo 5. Giá mua floor(giá bán × 1.5), hàng bán cho người chơi không giới hạn. Mỗi lệnh một đơn vị. Tiền bán cộng money và earned. Hàng mua chờ nhập thẳng vào kho quán tối Ngày kế, tách khỏi gather_end.inventory.
Sổ tay & Cá Hô (ca_ho)	Một con H1, 1.0 m/s. Chọn vị trí từ các điểm sinh chuẩn d ≥ 10 theo seed. Bơi trong x ∈ [4,96], d ∈ [10,30], phản xạ mép như cá thường. Một cạnh bắt hợp lệ trúng Cá Hô thì phát released sau event bắt cá thường, không thêm hàng và không tự đặt hồi. F (photo) trong ≤ 6 m cộng 0.5 uy tín, một lần/Ngày. Sổ tay ghi 8 loài đã gặp.
Settings & âm thanh	Âm lượng Master/Music/SFX lưu được giữa các lần mở game.
4. Test Contract v1.1 — Thay đổi từ v1.0
4.1. CLI và manifest
<headless_cmd> --mode gather|quan|day --seed <int>
  [--scenario <file.json>] [--inputs <file.json>]
  [--inventory <file.json>] [--inventory-out <file.json>]
  [--days <N>] --ticks <N> --out <file.jsonl> [--snapshot-every <N>]
--days chỉ với day, số nguyên từ 1 đến 5, mặc định 1. day tự bàn giao theo schema kho đếm ở v1.0, có thể truyền trong bộ nhớ. Hai cờ file kho vẫn dành cho hai mode độc lập.

Đặt contract_version: "1.1", dùng số chuẩn và dữ liệu mục 1–2. Bảng dưới liệt kê các khóa thêm hoặc đổi.

Phạm vi	Khóa
gather	fish_initial là số 8. Thêm fish_speed,fish_turn_ticks,fish_max,fish_spawn_ticks,fish_spawn_clearance,fish_x,fish_depths,fish_spawn_x,fish_spawn_depths,fish_weights. Các map theo loài và fish_yield có đủ 3 loài. fish_x là miền x, fish_spawn_x là danh sách x. Thêm nút N5/N6.
gather.monsters	species.ca_sau {patrol_speed,chase_speed,detect_radius,exit_radius,depths,hit_radius,recoil_ticks,recoil_dist}, spawns[] {id,kind,pos,waypoints,from_day} và invuln_ticks:90,loss_ratio:0.5.
quan, menu	Thêm B2, T2–T4 và 3 món mới.
day_plan	Mảng 5 object {day,dishes,ingredients}. dishes và ingredients là map id → số nguyên dương. Tính ingredients bằng tổng công thức nhân số suất.
shop	{max_ticks,upgrades}. upgrades.oxygen[] {level,price,oxygen_max_s}, upgrades.hp[] {level,price,hp_max}, mảng theo cấp.
Mở rộng	weapon: gather.weapon_cooldown_s, shop.upgrades.weapon[] {level,price,weapon_radius,stun_s} · net: shop.upgrades.net[] {level,price,catch_radius,max_schools} · snake: gather.monsters.species.ran cùng schema loài, thêm M3 vào spawns · burn: quan.burn_s hữu hạn · vendor: shop.vendor {buy_multiplier,sell_prices} · ca_ho: gather.ca_ho {count,speed,depths,photo_radius,reputation_bonus,bonus_per_day}.
4.2. Inputs và pause
Các nút boolean mới gồm pause ở cả ba mode, shop_done trong Shop, attack và photo trong gather khi bật mở rộng tương ứng. Chỉ tác động ở cạnh lên. Giữ nút qua đổi pha không tạo cạnh mới.
buy là chuỗi khác rỗng, chạy chỉ tại frame khai báo. Nhận oxygen, hp và các mở rộng weapon, net, buy:<kind>/sell:<kind> (Chợ). Shop phát buy_failed nếu gặp lệnh không hỗ trợ. Nút đúng kiểu nhưng sai pha hoặc mở rộng chưa bật thì bỏ qua.
Xét cạnh pause trước. Bước vào pause chỉ tăng tick ngoài, cập nhật chốt và phát paused. Khi còn pause, bỏ qua cạnh hành động và buy. sim_tick, phase_tick, lịch và timer đứng yên. Cạnh lên tiếp theo phát resumed, chạy gameplay ngay trong bước đó.
4.3. Scenario
day nhận gather và quan làm mẫu khởi tạo mỗi Ngày. Khối day {money,earned,reputation,upgrades,day_plan} dựng trạng thái xuyên Ngày. Mặc định tiền và earned 0, uy tín theo tuning, cấp là {} và kế hoạch theo preset. Cần 0 ≤ money ≤ earned, khai cả hai khi có tiền đầu kỳ. day.day_plan ghi đè theo số Ngày, mỗi mục có dishes. Tính lại ingredients và so với giá trị khai nếu có.
Cấm quan.stock và quan.reputation khi chạy day. Dùng gather.hold để dựng hàng. Kho, khách, bếp và món thuộc kế hoạch được kiểm trên kho thực lúc mở quán, mâu thuẫn → mã 2.
gather.player thêm invuln_ticks và attack_cd_ticks nếu bật Lao. gather.fish[] thêm age_ticks (mặc định 0), số bước cá đã tham gia bơi. random_fish:false tắt cá mặc định, bơi và sinh, cá fixture đứng yên. Khai fish khi cờ bật thì thay đàn ban đầu, vẫn bơi/sinh.
gather.monsters[] thay danh sách mặc định, nhận {id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir}. Hai waypoint, target_idx 0 hoặc 1 (mặc định 1), state mặc định patrol. recoil_dir là vector đơn vị khi recoil, mặc định null ở trạng thái khác. recoil/stunned cần timer dương. Bỏ mảng thì dùng bố trí đúng Ngày.
Nếu bật Sổ tay, gather.ca_ho là {id,pos,heading_deg,photographed} hoặc null, thay con tự sinh. Mặc định hướng 0°, ảnh false. random_ho:false tắt sinh và di chuyển tự động. Nếu bật cháy, quan.stoves[].ready_ticks dựng tuổi món chín.
Ví dụ mở một Ngày đã có tiền và kho mang về. Tương tác lúc ở bến sẽ đóng ca sáng ngay.

{"day":{"money":200,"earned":200},"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}
4.4. Output
Snapshot thêm state:"paused". Gather thêm monsters[], player.invuln_ticks, player.attack_cd_ticks nếu có Lao, ca_ho (object hoặc null) nếu có Sổ tay. Trong day, snapshot mọi pha có day,day_plan,upgrades,active_upgrades. Hai map cấp lần lượt là cấp đã mua và cấp đang áp dụng. phase là gather, quan hoặc shop. Snapshot Shop có stock dư từ ca và time_left_ticks tới lúc đóng. Snapshot đổi pha ghi pha mới với phase_tick:0. Event kết thúc mang pha cũ. Vỏ event bật chế độ day có thêm day.

name	data
monster_hit	monster_id,hp,lost,pos (vị trí người chơi, lost là mảng kind theo LIFO).
fish_spawned	id,kind,pos khi sinh theo lịch.
faint	Thêm cause:"monster" nếu do bị chạm, lost liệt kê phần giỏ còn lại, hp:0.
day_start, phase_start	{}.
day_plan	dishes,ingredients của Ngày đó.
paused, resumed	{}.
bought	upgrade,level,price,money.
buy_failed	action,reason (funds/max_level/out_of_stock/unknown).
shop_end	reason (done/time).
attack, monster_stunned (Lao)	pos,monster_ids (theo id) / monster_id,pos,stun_ticks sau đẩy.
photo, released (Sổ tay)	id,reputation sau cộng / id.
dish_burnt (Cháy)	stove_id,order_id,dish_id,order_status sau xử lý.
vendor_trade (Chợ)	action (buy/sell), kind,price,money.
{"type":"event","tick":0,"phase":"gather","day":1,"name":"day_plan","data":{"dishes":{"ca_loc_nuong_trui":3,"goi_bong_sung":3},"ingredients":{"ca_loc":3,"bong_sung":6}}}
Dòng end của day thêm days_completed (số Shop đã đóng). Hoàn thành đủ Ngày thì reason:"days_complete".

4.5. Thứ tự xử lý bổ sung
Gather. Đồng hồ, cooldown, giảm bất tử và hồi nút → bơi, oxy, ngạt → Lao nếu có, cập nhật quái theo id rồi xét tối đa một hit → tương tác (bến trước hái) → bắt cá theo vị trí cá trước khi bơi, rồi ảnh nếu có → xét hết giờ. Nếu còn giờ thì cá bơi, sinh thêm theo lịch, rồi cập nhật Cá Hô nếu bật. Khi Máu về 0, xử lý faint rồi gather_end(fainted) ngay sau choke hoặc monster_hit và bỏ các bước còn lại. Tại cùng tick, ngạt có thể đi trước hit rồi mới xét hết giờ. Cập bến vẫn ưu tiên trước bắt cá và hết giờ nếu còn Máu.
Quán. Giữ thứ tự v1.0. Nếu bật cháy, xét món chín/cháy theo id bếp trước di chuyển và tương tác. Trong day, lọc menu theo id món trong kế hoạch trước khi lọc nguyên liệu khả dụng.
Đổi pha. day_start → day_plan → phase_start(gather). Sau gather_end dựng quán và phát phase_start(quan) cùng tick, kể cả khi ngất. Sau quan_end dựng Shop và phát phase_start(shop) cùng tick. Pha mới chỉ chạy gameplay từ bước sau.
Shop. Xử lý một buy trước cạnh shop_done, kể cả bước cuối. Đóng bằng nút ở bước cuối phát shop_end(done). Tự hết giờ phát shop_end(time). Đóng Shop thì tăng days_completed, kết thúc hoặc dựng Ngày kế ngay tick đó. Chỉ khi dựng Ngày mới mới sao cấp đã mua sang active_upgrades.
5. Quy trình nhóm và lịch gợi ý
Nhóm tự chọn cách phối hợp và cùng commit vào fork chung bằng tài khoản GitHub của từng người. Gợi ý làm song song (1) số chuẩn và cá bơi/sinh, (2) Cá Sấu, Máu và ngất, (3) 2 bếp/4 bàn, 6 món và kế hoạch ngày, (4) day, Shop, pause, menu và HUD. Dùng fixture cố định để người làm day tích hợp sớm với hai buổi đang có. Có thể kiểm chéo các lát, pair và đổi vai. Ghi Co-authored-by: khi cùng làm một commit.

Phút trong phase	Việc
0–5	Lên lại kế hoạch. So số chuẩn với giả định cũ, chốt giao diện chuyển pha, chia người và phần phụ thuộc theo AC-P2-xx. Ghi ở nơi nhóm tiện theo dõi.
5–20	Build và kiểm thử bốn lát, cập nhật hợp đồng v1.1 và cấu hình/dữ liệu chuẩn. Chuẩn bị ca smoke.
20	Chạy smoke tích hợp theo luồng gather --inventory-out → quan --inventory, có thể pair/mob. Đối chiếu snapshot kho ở tick 0 và lưu docs/proof/phase-2/integration.*. Standup 2–3 phút và điều người đã xong sang lát trễ.
20–35	Build tiếp, phối hợp giữa các lát và chốt luồng day.
35–45	Chạy smoke day --days 1, chạy nhiều Ngày để kiểm cấp nâng cấp và chạy regression P1 với số chuẩn. Lưu bằng chứng, hoàn thiện docs/verification/phase-2.md và gắn tag.
45–50	Retro nhanh. Ghi điều tốt, điều vướng và một hành động có người nhận trong docs/retro.md.
50–55	Dự phòng. Đẩy tag phase-2 chậm nhất 1:55.
Ghi lý do nếu test cũ cần cập nhật vì luật mới. Trong docs/verification/phase-2.md, nối từng AC với bằng chứng và kết quả chạy trên commit bàn giao. Cập nhật docs/clarify.md và docs/ai-usage-log.md.

Định nghĩa hoàn thành (DoD)
 contract_version:"1.1", tuning chuẩn, đủ 6 nguyên liệu và 6 món theo dữ liệu. Cá bơi/sinh, Cá Sấu, Máu/ngất, 2 bếp/4 bàn hoạt động đúng.
 Chơi trọn vòng ngày với menu, pause và HUD. --mode day công bố đúng kế hoạch D1–D5, chốt Ngày khi Shop đóng và áp đúng cấp oxygen/hp từ Ngày kế.
 Smoke tích hợp có bằng chứng. Regression P1 còn hiệu lực đạt với số chuẩn, test thay đổi có ghi lý do. docs/verification/phase-2.md và bằng chứng khớp commit gắn tag.
 Công việc các lát đã tích hợp trong fork chung, có bằng chứng đóng góp của từng người. Ghi chép làm rõ, nhật ký AI và retro đã cập nhật.
 Nếu làm mở rộng, README khai mục đã làm và có test/bằng chứng.
 Đẩy phase-2 trỏ tới commit bàn giao trên main chậm nhất 1:55.