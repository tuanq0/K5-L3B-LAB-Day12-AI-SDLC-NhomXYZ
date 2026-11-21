# Chi tiết khung kỹ thuật (starter Python)

> Starter chỉ là **gợi ý**: công nghệ không ràng buộc. Trang này giải thích cái gì đã có sẵn và cách chơi thử.

## Chạy thử

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v     # smoke test (phải xanh; nếu dùng starter Python)
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl
```

Hai chế độ của contract v1.0: `gather` (buổi sáng: lặn và hái, nhìn ngang, vị trí `[x, d]`, `d` là độ sâu) và `quan` (buổi tối: mở quán, nhìn từ trên xuống, vị trí `[x, z]`). Chế độ `day` có từ phase sau.

## Chơi thử trực tiếp trên trình duyệt (không cần cài gì)

```bash
python3 -m chonoi.live --mode gather      # hoặc: --mode quan   [--seed N] [--port 8000]
```

Lệnh in một địa chỉ (mặc định `http://127.0.0.1:8000/`); mở nó bằng trình duyệt. Phím: **WASD / mũi tên** di chuyển, **E** (`interact`), **Space** (`catch`), **R** chơi lại. Cửa sổ chạy **cùng một lớp sim** với headless (60 tick/s) và chỉ **đọc snapshot**, nên nhóm viết luật tới đâu thì thanh oxy, Máu, giỏ, cá, nút hái... hiện tới đó (trường chưa có sẽ bị bỏ qua). Đây chỉ là hình khối tạm để thử luật; đồ họa thật do nhóm làm. Khi chạy `--mode gather` trên trình duyệt, buổi lặn kết thúc thì cửa sổ tự chuyển sang quán và truyền giỏ thành kho; `--inventory-out` vẫn có thể dùng để lưu file kho riêng. Hai chế độ headless vẫn có thể chạy nối bằng `--inventory-out kho.json` rồi `--inventory kho.json`. File chỉ dùng thư viện chuẩn Python (`chonoi/live.py`, `chonoi/web/index.html`); đổi ngôn ngữ thì xóa hoặc thay bằng cửa sổ của nhóm.

Trong quán, nhấn **G** để quay sang buổi Gather. Kho quán được chuyển vào giỏ (tối đa sức chứa giỏ); khi buổi Gather kết thúc, hàng mới và phần kho còn lại sẽ trở lại quán.

UI quán có một cửa **GATHER** tại góc trên bên phải. Đến cửa đó và nhấn **E** hoặc dùng phím tắt **G** để sang Gather; có thể thực hiện trong lúc quán vẫn còn thời gian.

## Công nghệ: tự chọn (starter chỉ là gợi ý, KHÔNG bắt buộc)

Nhóm được dùng **bất kỳ ngôn ngữ/engine nào**. Thứ duy nhất bắt buộc là **Test Contract** (chế độ headless theo tài liệu phase) và `game.contract.json` khai đúng `build_cmd`, `headless_cmd`.

`chonoi/` là một khung **Python 3** (chỉ thư viện chuẩn) giảng viên làm sẵn để tiết kiệm thời gian: đọc tham số, đọc inputs/scenario/kho, kiểm lỗi (mã thoát 2), vòng tick 60 Hz, RNG có seed, cấp/sắp id, ghi JSONL tất định, ghi file kho an toàn. **Luật chơi do nhóm viết** (tìm `TODO(nhóm)`). Dùng hay không tùy nhóm.

| Khung Python đã có | Nhóm viết |
|---|---|
| CLI + kiểm lỗi, mã thoát 0/1/2 | `chonoi/sim/gather.py`: oxy, ngạt, Máu, ngất, hái nút, bắt cá, giỏ (LIFO) |
| Đọc inputs, cạnh lên, chuẩn hóa vector | `chonoi/sim/quan.py`: khách, giữ chỗ, bếp, bưng, phục vụ, tiền, uy tín |
| Bơi, tăng/giảm tốc, chặn mép (`d` không âm), cập bến, hết giờ | Điều chỉnh nút hái / bầy cá mặc định (dữ liệu ở `game.contract.json`) |
| Đọc/ghi file kho, ghi nguyên tử | Kiểm mâu thuẫn scenario mức luật (`scenario.py`) |
| JSONL tất định, làm tròn 3 chữ số, sắp id | Hiển thị / HUD thật (khung chỉ có cửa sổ thử `chonoi.live` bằng hình khối tạm) |
| Cửa sổ thử trên trình duyệt (`python3 -m chonoi.live`) | Đồ họa, âm thanh, menu, HUD hoàn chỉnh theo PRD |

### Nếu nhóm đổi sang ngôn ngữ khác
1. Sửa `build_cmd`, `run_cmd` (hiện là `python3 -m chonoi.live --mode gather`), `headless_cmd` trong `game.contract.json` cho ngôn ngữ của nhóm.
2. Nếu nhóm dùng CI: sửa bước **Build** và **Test** trong `.github/workflows/ci.yml` (cài runtime cần thiết); không dùng CI thì xóa file đó.
3. **Giữ** `tests/test_smoke_p1.py`: đây là test **hộp đen**, chỉ chạy `headless_cmd` rồi đọc JSONL/file kho, nên dùng nguyên cho mọi ngôn ngữ. **Xóa** `chonoi/`, `tests/test_python_starter_units.py` và `tests/test_live.py` nếu không dùng; viết unit test bằng ngôn ngữ của nhóm.
4. Vẫn phải qua cùng Test Contract: cùng seed → output giống từng byte.

Lưu ý: `tools/check_team.py` (kiểm danh sách thành viên) là script Python độc lập, không liên quan tới ngôn ngữ của game.

## Quy tắc vàng

- Số liệu chỉ nằm trong `game.contract.json`; luật chỉ đọc từ đó.
- Ngẫu nhiên chỉ qua `Streams`; không dùng đồng hồ hệ thống. Cùng seed → output giống từng byte.
- Nhánh chính luôn **chạy được** (nhất là lúc gắn tag). Cách đạt điều đó do nhóm chọn.
- Cùng commit vào một repo chung; mỗi người có dấu vết của mình.

## Tài liệu trong repo

[`TEAM.md`](../TEAM.md) (vai + thỏa thuận nhóm) · [`AGENTS.md`](../AGENTS.md) · `docs/contracts/` (hợp đồng tích hợp: nên chốt sớm, hình thức tự chọn) · `docs/{plan,verification,proof,adr,members}/` (gợi ý) · `docs/{clarify,standup,retro,ai-usage-log}.md`.
