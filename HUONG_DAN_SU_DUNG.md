# 📘 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG PROJECT MEMORY V2.0

> **Dành cho:** Châu Vũ & Toàn bộ AI Agents (Hermes, Hagi, Claude Code, OpenCode, Codex).  
> **Phiên bản:** `v2.0 (Frozen Standard)` — Zero External Dependencies (Pure Python 3.11+ Stdlib).

---

## 🎯 1. TỔNG QUAN & MỤC TIÊU CỐT LÕI

Hệ thống **Project Memory V2.0** (`.agent/`) được thiết kế để giải quyết 3 điểm nghẽn lớn nhất trong việc phát triển phần mềm bằng AI Agents:

1. **Tránh lãng phí Context & Token (Zero-Scan):** Agent mới vào session không cần đọc lại 50.000–100.000 dòng code của repo. Chỉ cần nạp **Bootstrap Context (~2.5 KB)** là nắm trọn trạng thái, kiến trúc và task cần làm.
2. **Khóa kiến trúc (ADR Locking):** Ngăn chặn agent sau tự ý "sáng tạo" đập đi xây lại những quyết định kiến trúc cốt lõi đã chốt từ trước.
3. **Chống ảo tưởng tiến độ (Evidence Gate):** Chỉ đánh dấu `DONE` khi có bằng chứng chạy test thật (`pytest`, `unittest`) và được gắn chặt với Git Commit Hash thật.

---

## 📁 2. CẤU TRÚC BỘ NHỚ `.agent/`

Bên trong mỗi repository chuẩn sẽ có thư mục `.agent/` gồm 8 thành phần:

```text
.agent/
├── BOOT.md              # [BẮT BUỘC ĐỌC ĐẦU TIÊN] File neo khởi động session (< 1 KB)
├── PROJECT_STATE.json   # State machine của repo (gắn với Git code_commit & memory_commit)
├── PROJECT_MAP.json     # Bản đồ GPS codebase: Phân chia Domain -> File Paths -> Tests
├── DECISIONS.md         # Danh mục Architectural Decision Records (ADRs) ở trạng thái [LOCKED]
├── NEXT_TASK.md         # Đặc tả chi tiết task đang active, domain liên quan & tiêu chí nghiệm thu
├── TASK_LEDGER.jsonl    # Sổ cái nhật ký bất biến (append-only ledger) lưu vết các task đã xong
├── MEMORY_PROTOCOL.md   # 10 điều luật bắt buộc agent phải tuân thủ
└── memory.py            # CLI Engine hỗ trợ kiểm tra, tính metrics và tạo checkpoint
```

---

## 🚀 3. HƯỚNG DẪN DÙNG CÔNG CỤ CLI

### A. Khởi tạo Project Memory cho một Repo mới (`bootstrap.py`)

#### Cách 1: One-Liner trực tiếp (Không cần clone repo ZeroScan)
```bash
curl -fsSL https://raw.githubusercontent.com/chauvuusvn/zeroscan/main/bootstrap.py | python3 - \
  --target /path/to/du-an-moi \
  --name "TenDuAn" \
  --mission "Mô tả ngắn gọn mục tiêu của dự án" \
  --phase "1" \
  --domains "core-engine,api-gateway,storage,test-suite" \
  --git-init
```

#### Cách 2: Chạy trực tiếp từ file cục bộ
Tại thư mục `zeroscan`, chạy lệnh để scaffold toàn bộ `.agent/`:

```bash
python3 bootstrap.py \
  --target /path/to/du-an-moi \
  --name "TenDuAn" \
  --mission "Mô tả ngắn gọn mục tiêu của dự án" \
  --phase "1" \
  --domains "core-engine,api-gateway,storage,test-suite"
```

*Tùy chọn bổ sung:*
* `--git-init`: Tự động khởi tạo git repo nếu chưa có.
* `--force`: Ghi đè lại cấu trúc `.agent/` nếu đã tồn tại.

---

### B. Các lệnh điều phối trong dự án (`.agent/memory.py`)

Trong bất kỳ repository nào đã có `.agent/`, sử dụng các lệnh sau:

#### 1. Kiểm tra tổng quan trạng thái dự án
```bash
python3 .agent/memory.py status
```
*In ra Dashboard gồm: Phase hiện tại, commit đã verify, active task, test status, và bảng phân bổ dung lượng context.*

#### 2. Xác thực tính toàn vẹn bộ nhớ & Đồng bộ Git
```bash
python3 .agent/memory.py validate
```
*Kiểm tra:*
* 8 file bắt buộc có đầy đủ không.
* `BOOTSTRAP_CONTEXT_BYTES` có vượt trần 10 KB không.
* Git HEAD có khớp với `code_commit` hoặc `memory_commit` không. Nếu lệch (desync), tự động in danh sách file bị lệch.

#### 3. Lưu mốc tiến độ (Checkpoint) sau khi code xong
Sau khi code và chạy test thành công:
```bash
python3 .agent/memory.py checkpoint \
  --phase "1" \
  --status "COMPLETED" \
  --commit "$(git rev-parse HEAD)" \
  --record-ledger \
  --task-id "P1-T01" \
  --task-summary "Mô tả ngắn gọn tính năng vừa hoàn thành"
```

#### 4. Thêm quyết định kiến trúc mới (ADR)
```bash
python3 .agent/memory.py add-decision \
  --title "Use PostgreSQL for Timeseries Data" \
  --decision "Sử dụng TimescaleDB trên Postgres thay vì InfluxDB" \
  --reason "Tận dụng relational query có sẵn và giảm chi phí infra" \
  --status "LOCKED"
```

---

## 🔄 4. QUY TRÌNH 5 BƯỚC CHO AGENT KHI LÀM VIỆC (STANDARD WORKFLOW)

Mọi Agent khi nhận việc trong repository đều phải tuân thủ nghiêm ngặt 5 bước:

```
  ┌────────────────────────────────────────────────────────┐
  │ BƯỚC 1: BOOT SESSION                                   │
  │ • Đọc duy nhất `.agent/BOOT.md` (< 1 KB)               │
  │ • Nắm rõ Mission, Phase, Ràng buộc và Task đang active │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ BƯỚC 2: VALIDATE STATE                                 │
  │ • Chạy: `python3 .agent/memory.py validate`            │
  │ • Nếu [IN_SYNC] -> Tiếp tục                            │
  │ • Nếu [DESYNC] -> Đọc git diff của các file lệch       │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ BƯỚC 3: DOMAIN LOOKUP & SELECTIVE READ                 │
  │ • Đọc `.agent/NEXT_TASK.md` lấy Domain liên quan       │
  │ • Tra `.agent/PROJECT_MAP.json` để lấy đúng 2-3 files  │
  │ • KHÔNG scan toàn bộ repo bừa bãi                      │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ BƯỚC 4: EXECUTE & TEST                                 │
  │ • Viết code / sửa lỗi theo yêu cầu                     │
  │ • Chạy test suite thật lấy Evidence (100% PASS)        │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ BƯỚC 5: COMMIT & CHECKPOINT                            │
  │ • `git add <files> && git commit -m "..."`             │
  │ • Chạy `python3 .agent/memory.py checkpoint ...`       │
  │ • Cập nhật `.agent/NEXT_TASK.md` cho task tiếp theo    │
  └────────────────────────────────────────────────────────┘
```

---

## 📊 5. CHUẨN ĐO LƯỜNG CONTEXT BUDGET

Để tránh trôi ngữ cảnh khi trao đổi giữa các LLM, hệ thống quy định 2 chỉ số tiêu chuẩn:

| Chỉ số | Định nghĩa | Ngưỡng cho phép | Thực tế AutoNovel & AI Council |
|---|---|---|---|
| **`BOOTSTRAP_CONTEXT_BYTES`** | Tổng dung lượng `BOOT.md` + `PROJECT_STATE.json` + `NEXT_TASK.md` | $\le$ **10,240 bytes (10 KB)** | **~2,490 bytes (24.3%)** |
| **`TOTAL_AGENT_SYSTEM_BYTES`** | Toàn bộ dung lượng thư mục `.agent/` (gồm code helper, protocol, ADRs) | Thông tin tham khảo | **~30.6 KB** |

---

## 🔒 6. 10 NGUYÊN TẮC VÀNG QUẢN TRỊ BỘ NHỚ (MEMORY PROTOCOL)

1. **Đọc `BOOT.md` trước tiên:** Không bao giờ bắt đầu session bằng cách scan toàn bộ repo.
2. **Kiểm tra tính đồng bộ Git:** Luôn chạy `memory.py validate` trước khi code.
3. **Tra cứu qua `PROJECT_MAP.json`:** Chỉ mở những file thuộc domain của task hiện tại.
4. **Tôn trọng quyết định `[LOCKED]`:** Tuyệt đối không thay đổi các ADR đã khóa trong `DECISIONS.md`.
5. **Cổng bằng chứng (Evidence Gate):** Không bao giờ đánh dấu `DONE` nếu chưa có test PASS thực tế.
6. **Không tự bịa dữ liệu:** Sự thật nằm ở source code, test log và Git commit.
7. **Tách biệt Commit Code và Memory:** Commit code trước, lấy SHA checkpoint memory sau.
8. **Append-only Task Ledger:** Không xóa sửa lịch sử trong `TASK_LEDGER.jsonl`.
9. **Kế thừa Session:** Mọi session mới phải có khả năng tiếp tục trơn tru chỉ từ `.agent/`.
10. **Báo cáo trung thực:** Báo cáo đúng dung lượng bootstrap và file test diff thực tế.
