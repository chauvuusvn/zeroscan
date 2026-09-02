# Project Memory V2.0 Template & Generator (`.agent/`)

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README.vi.md)

> **Cơ chế quản trị ngữ cảnh Zero-Scan gắn kết với Git dành cho AI Coding Agents**  
> Tương thích hoàn toàn với Hermes Agent, Claude Code, OpenAI Codex, và OpenCode.

---

## 🌟 Tổng quan

**Project Memory V2.0** là chuẩn mở được thiết kế nhằm xóa bỏ tình trạng phình ngữ cảnh (context bloat), ảo tưởng tiến độ (hallucination) và chi phí quét cây thư mục lặp đi lặp lại trong quy trình phát triển phần mềm bằng AI.

Các coding agent truyền thống thường lãng phí hàng chục ngàn token để quét toàn bộ codebase mỗi khi bắt đầu phiên làm việc. Project Memory thay thế việc quét bừa bãi bằng một **File neo khởi động Cấp 0** (`BOOT.md` < 1 KB) và một **Bản đồ kiến trúc GPS** (`PROJECT_MAP.json`), đảm bảo agent khởi động tức thì với tổng ngữ cảnh `<= 10 KB`.

---

## 💡 Vì sao hệ thống tiết kiệm 90–95% Token?

### 1. Khởi động Zero-Scan (Level 0 Boot Anchor)
Các agent thông thường đọc toàn bộ kho mã nguồn trong mỗi lượt hội thoại, dễ dàng đốt 30.000–100.000+ token trước khi viết dòng code đầu tiên. Với Project Memory, agent **chỉ đọc duy nhất `BOOT.md` (~1 KB / ~500 tokens)**, ngay lập tức nắm vững kiến trúc cốt lõi và nhiệm vụ cần làm mà không cần đọc các thư mục không liên quan.

### 2. Định vị GPS qua `PROJECT_MAP.json`
Thay vì tìm kiếm regex tốn kém trên toàn bộ cây thư mục, agent tra cứu bản đồ domain để nạp đúng file mã nguồn và file test cần thiết ngay lúc chạy. Các module không liên quan sẽ không bao giờ bị nạp vào ngữ cảnh làm việc.

### 3. Ủy thác nhiệm vụ đa Agent tinh gọn (Multi-Agent Delegation)
Khi một agent điều phối (Orchestrator) chia nhỏ công việc cho các subagent hoặc worker, nó chỉ truyền `BOOT.md` và `NEXT_TASK.md`. Các worker agent hoạt động trong cửa sổ ngữ cảnh cô lập, sắc bén mà không phải trả phí token cho toàn bộ repository.

### 📊 Bảng so sánh mức độ tiêu thụ Token

| Giai đoạn vòng đời | Cách tiếp cận truyền thống (Quét toàn bộ) | Project Memory V2.0 (`.agent/`) | Tỉ lệ tiết kiệm |
|---|---|---|:---:|
| **Khởi động phiên (Session Boot)** | Nạp toàn bộ repo (30k–100k+ tokens) | Đọc `BOOT.md` (< 1 KB / ~500 tokens) | **~95%** |
| **Điều hướng module (Domain Navigation)** | Chạy grep đệ quy & quét cây thư mục | Tra cứu `PROJECT_MAP.json` (< 3 KB) | **~90%** |
| **Khởi động Worker Subagent** | Đọc lại cả repo cho mỗi agent con | Nạp `NEXT_TASK.md` + file đích | **~92%** |
| **Trôi ngữ cảnh (Memory Drift)** | Phình prompt & sinh ảo giác | Sổ cái bất biến (Ledger) & khóa ADR | **Triệt tiêu trôi nhớ** |

---

## 📁 Cấu trúc chuẩn `.agent/`

Mỗi dự án tuân thủ chuẩn đều chứa một thư mục `.agent/` với cấu trúc sau:

```
.agent/
├── BOOT.md               # [Level 0] File neo khởi động siêu nhẹ (< 1 KB / ~30 dòng)
├── PROJECT_STATE.json    # [Level 1] State machine gắn kết với git verified_commit & metrics
├── PROJECT_MAP.json      # Bản đồ GPS: Ánh xạ domain chức năng tới files & tests
├── DECISIONS.md          # Danh mục quyết định kiến trúc (ADRs) ở trạng thái [LOCKED]
├── TASK_LEDGER.jsonl     # Sổ cái nhật ký bất biến lưu vết các task đã xong & bằng chứng
├── NEXT_TASK.md          # Đặc tả task đang active, tiêu chí nghiệm thu & lệnh test
├── MEMORY_PROTOCOL.md    # 10 điều luật vàng cho agent thực thi & xác minh bằng chứng
└── memory.py             # Engine Python 3.11+ thuần túy không dependencies bên ngoài
```

---

## 🚀 Hướng dẫn nhanh: Khởi tạo dự án mới

Sử dụng `bootstrap.py` để tạo hệ thống bộ nhớ `.agent/` chuẩn cho bất kỳ repository nào:

```bash
# Sử dụng cơ bản trong thư mục hiện tại
python3 bootstrap.py

# Khởi tạo tùy biến cho một dự án cụ thể
python3 bootstrap.py \
  --target /path/to/my-project \
  --name "Quantum Engine" \
  --mission "Hệ thống xử lý sự kiện phân tán hiệu năng cao" \
  --phase "Phase 1 - Kiến trúc cốt lõi" \
  --domains "engine,storage,network,api" \
  --git-init
```

### Tham số CLI của `bootstrap.py`:
| Tùy chọn | Viết tắt | Mặc định | Mô tả |
|---|---|---|---|
| `--target` | `-t` | `.` | Đường dẫn thư mục dự án đích |
| `--name` | `-n` | Tên thư mục | Tên dự án |
| `--mission` | `-m` | "Autonomous..." | Tuyên ngôn sứ mệnh của dự án |
| `--phase` | `-p` | "Phase 1..." | Tên phase khởi đầu |
| `--domains` | `-d` | "core" | Danh sách các domain phân tách bằng dấu phẩy |
| `--force` | `-f` | `False` | Ghi đè thư mục `.agent/` nếu đã tồn tại |
| `--git-init` | | `False` | Tự động chạy `git init` nếu thư mục chưa có Git |

---

## 🛠️ Vận hành `.agent/memory.py` trong dự án

Sau khi khởi tạo, agent tương tác trực tiếp với engine bộ nhớ:

### 1. Xem trạng thái & hạn mức bộ nhớ
```bash
python3 .agent/memory.py status
```
Hiển thị sứ mệnh, phase hiện tại, task active, git HEAD vs commit đã xác thực, và chi tiết dung lượng context.

### 2. Kiểm tra tính toàn vẹn của bộ nhớ
```bash
python3 .agent/memory.py validate
```
Kiểm tra JSON schemas, đối soát commit git, và xác nhận `BOOTSTRAP_CONTEXT_BYTES <= 10,240 bytes` (10 KB).

### 3. Checkpoint trạng thái nguyên tử
```bash
python3 .agent/memory.py checkpoint \
  --phase "Phase 2 - Phát triển tính năng" \
  --status "IN_PROGRESS" \
  --active-task "Xây dựng middleware xác thực người dùng" \
  --record-ledger \
  --task-id "TASK-002" \
  --task-summary "Hoàn thành đăng ký và băm mật khẩu" \
  --evidence "pytest_exit_0_hash_abc123" \
  --test-status "ALL_PASS (48/48)"
```
- Cập nhật nguyên tử file `PROJECT_STATE.json`.
- Đồng bộ tái tạo file `BOOT.md`.
- Ghi thêm bằng chứng task vào sổ cái `TASK_LEDGER.jsonl`.
- Tự động tính toán lại dung lượng context.

### 4. Ghi nhận quyết định kiến trúc (ADR)
```bash
python3 .agent/memory.py add-decision \
  --id "ADR-002" \
  --title "Sử dụng SQLite chế độ WAL làm bộ nhớ đệm cục bộ" \
  --status "LOCKED" \
  --context "Yêu cầu đọc đồng thời cao mà không cần dịch vụ DB bên ngoài" \
  --decision "Sử dụng SQLite nhúng với chế độ WAL và 64MB mmap" \
  --consequences "Không phụ thuộc dịch vụ ngoài; chỉ chạy đơn node"
```

---

## 📊 Hạn mức kích thước ngữ cảnh (Context Budget)

Project Memory V2.0 thực thi nghiêm ngặt hạn ngạch token:

- **Hạn mức Bootstrap Context (`BOOTSTRAP_CONTEXT_BYTES`)**:\n  $$\text{Dung lượng}(\text{BOOT.md}) + \text{Dung lượng}(\text{PROJECT_STATE.json}) + \text{Dung lượng}(\text{NEXT_TASK.md}) \le 10,240 \text{ bytes (10 KB)}$$
- **Không duyệt cây thư mục**: Agent đọc `BOOT.md` và tra cứu `PROJECT_MAP.json` để mở thẳng các file liên quan thay vì quét toàn bộ cây thư mục.

---

## 📜 10 Điều Luật Vàng

1. **Khởi động từ Level 0**: Đọc `.agent/BOOT.md` đầu tiên. Tuyệt đối không quét đệ quy codebase.
2. **Gắn kết Git Commit thật**: Mọi cập nhật trạng thái phải tham chiếu commit hash hợp lệ.
3. **Định tuyến qua Bản đồ GPS**: Sử dụng `PROJECT_MAP.json` để chỉ tải các file domain liên quan.
4. **Bảo vệ ADR đã khóa**: Không bao giờ vi phạm các quyết định có nhãn `[LOCKED]` trong `DECISIONS.md`.
5. **Cập nhật nguyên tử**: Luôn sử dụng `memory.py checkpoint` cho mọi thao tác lưu tiến độ.
6. **Sổ cái bất biến**: Không bao giờ chỉnh sửa hoặc cắt xén `TASK_LEDGER.jsonl`.
7. **Tập trung đơn nhiệm**: `NEXT_TASK.md` xác định một mục tiêu duy nhất đang thực hiện.
8. **Nghiệm thu bằng bằng chứng**: Chỉ đánh dấu hoàn thành khi có kết quả chạy test thật thành công.
9. **Kiểm soát hạn mức ngữ cảnh**: Giữ tổng các file bootstrap dưới 10 KB.
10. **Tự động kiểm tra**: Chạy `memory.py validate` trong pre-commit hook hoặc CI pipeline.

---

## 🧪 Bản quyền
Apache-2.0 / MIT. Thiết kế chuyên biệt cho các quy trình AI Agent tự chủ cao.
