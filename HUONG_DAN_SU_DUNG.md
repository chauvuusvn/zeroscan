# 📘 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG ZEROSCAN (PROJECT MEMORY V2.1)

> **Dành cho:** Kỹ sư phần mềm & Toàn bộ AI Agents (Hermes, Claude Code, Cursor, Windsurf, Codex, OpenCode).  
> **Phiên bản:** `v2.1.2 (Production / Enterprise Ready)` — Zero External Dependencies (Pure Python 3.9+ Stdlib).  
> **Phát hành PyPI:** `pip install zeroscan`

---

## 🎯 1. TỔNG QUAN & MỤC TIÊU CỐT LÕI

Hệ thống **Zero-Scan Project Memory V2.1** (`.agent/`) giải quyết 4 điểm nghẽn lớn nhất trong việc phát triển phần mềm bằng AI Agents:

1. **Tránh lãng phí Context & Token (Zero-Scan):** Agent mới vào session không cần đọc lại 50.000–100.000 dòng code của repo. Chỉ cần nạp **Bootstrap Context (~2.5 KB)** là nắm trọn trạng thái, kiến trúc và task cần làm.
2. **Khóa kiến trúc (ADR Locking):** Ngăn chặn agent sau tự ý "sáng tạo" đập đi xây lại những quyết định kiến trúc cốt lõi đã chốt từ trước trong `DECISIONS.md`.
3. **Cổng bằng chứng (Evidence Gate):** Chỉ đánh dấu `DONE` khi có bằng chứng chạy test thật (`pytest`, `unittest`) và được gắn chặt với Git Commit Hash thật.
4. **Cơ chế tự chữa lành (Self-Healing Engine):** Tự động đồng bộ `BOOT.md`, phục hồi khi file JSON bị lỗi, và tự nén lưu trữ khi sổ cái task phình to.

---

## 📁 2. CẤU TRÚC BỘ NHỚ `.agent/`

```text
.agent/
├── BOOT.md              # [BẮT BUỘC ĐỌC ĐẦU TIÊN] File neo khởi động session (< 1 KB)
├── PROJECT_STATE.json   # State machine của repo (gắn với Git code_commit & memory_commit)
├── PROJECT_MAP.json     # Bản đồ GPS codebase: Phân chia Domain -> File Paths -> Tests
├── DECISIONS.md         # Danh mục Architectural Decision Records (ADRs) ở trạng thái [LOCKED]
├── NEXT_TASK.md         # Đặc tả chi tiết task đang active, domain liên quan & tiêu chí nghiệm thu
├── TASK_LEDGER.jsonl    # Sổ cái nhật ký bất biến (append-only ledger) lưu vết các task đã xong
├── MEMORY_PROTOCOL.md   # 10 điều luật bắt buộc agent phải tuân thủ
├── memory.py            # CLI Engine hỗ trợ kiểm tra, tính metrics và tạo checkpoint
└── archive/             # Lưu trữ tự động các task cũ khi ledger vượt quá 50 tasks
```

---

## 🚀 3. HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG CLI TOÀN CẦU

### A. Cài đặt 1-chạm qua pip
```bash
pip install zeroscan
```

### B. Khởi tạo bộ nhớ cho dự án mới hoặc dự án có sẵn
```bash
zeroscan-bootstrap --name "my-awesome-project" --mission "Xây dựng hệ thống AI" --domains "core,auth,api,db"
```

### C. Các lệnh vận hành cốt lõi
```bash
# 1. Kiểm tra trạng thái và độ tuân thủ quy chuẩn
zeroscan status
zeroscan validate

# 2. Đo lường ngân sách ngữ cảnh (Context Budget Metrics)
zeroscan metrics
zeroscan metrics --json

# 3. Đồng bộ hóa BOOT.md và tạo checkpoint Git
zeroscan sync

# 4. Khởi động máy chủ MCP Server cho Claude Desktop / Cursor / Windsurf
zeroscan-mcp
```

---

## 📊 4. CHUẨN ĐO LƯỜNG CONTEXT BUDGET

Để tránh trôi ngữ cảnh khi trao đổi giữa các LLM, hệ thống quy định 2 chỉ số tiêu chuẩn:

| Chỉ số | Định nghĩa | Ngưỡng cho phép | Thực tế Zero-Scan V2.1 |
|---|---|---|---|
| **`BOOTSTRAP_CONTEXT_BYTES`** | Tổng dung lượng `BOOT.md` + `PROJECT_STATE.json` + `NEXT_TASK.md` | $\le$ **10,240 bytes (10 KB)** | **~2,400 bytes (23.5%)** |
| **`TOTAL_AGENT_SYSTEM_BYTES`** | Toàn bộ dung lượng thư mục `.agent/` (gồm code helper, protocol, ADRs) | Thông tin tham khảo | **~29.4 KB** |

---

## 🔒 5. 10 NGUYÊN TẮC VÀNG QUẢN TRỊ BỘ NHỚ (MEMORY PROTOCOL)

1. **Đọc `BOOT.md` trước tiên:** Không bao giờ bắt đầu session bằng cách scan toàn bộ repo.
2. **Kiểm tra tính đồng bộ Git:** Luôn chạy `zeroscan validate` trước khi code.
3. **Tra cứu qua `PROJECT_MAP.json`:** Chỉ mở những file thuộc domain của task hiện tại.
4. **Tôn trọng quyết định `[LOCKED]`:** Tuyệt đối không thay đổi các ADR đã khóa trong `DECISIONS.md`.
5. **Cổng bằng chứng (Evidence Gate):** Không bao giờ đánh dấu `DONE` nếu chưa có test PASS thực tế.
6. **Không tự bịa dữ liệu:** Sự thật nằm ở source code, test log và Git commit.
7. **Tách biệt Commit Code và Memory:** Commit code trước, lấy SHA checkpoint memory sau.
8. **Append-only Task Ledger:** Không xóa sửa lịch sử trong `TASK_LEDGER.jsonl`.
9. **Kế thừa Session:** Mọi session mới phải có khả năng tiếp tục trơn tru chỉ từ `.agent/`.
10. **Báo cáo trung thực:** Báo cáo đúng dung lượng bootstrap và file test diff thực tế.

---

## ⚠️ 6. 8 BẪY LỖI THỰC CHIẾN & QUY TRÌNH KHẮC PHỤC

### Bẫy lỗi 1: Hoàn thành Task nhưng chưa Commit Git (Commit ảo)
* **Hiện tượng:** Ghi task `DONE` vào ledger nhưng chưa tạo commit mã nguồn.
* **Khắc phục:** Chạy `zeroscan validate`. Nếu phát hiện lệch commit, tiến hành commit code trước: `git add . && git commit -m "fix: hoàn thành task"`, sau đó mới ghi checkpoint.

### Bẫy lỗi 2: Tràn bộ nhớ do File Quyết Định phình to (Decisions Bloat)
* **Hiện tượng:** `DECISIONS.md` tích lũy quá nhiều quyết định nhỏ lẻ vượt 20 KB.
* **Khắc phục:** Áp dụng **Quy trình Nén (Compaction)**: Tổng kết các quyết định cốt lõi vào `PROJECT_STATE.json`, lưu trữ toàn bộ lịch sử chi tiết vào `DECISIONS_ARCHIVE.md`.

### Bẫy lỗi 3: Xung đột ghi đè đồng thời giữa các Agent (Race Condition)
* **Hiện tượng:** Nhiều Agent chạy song song cùng lúc ghi vào file trạng thái gây hỏng JSON.
* **Khắc phục:** Sử dụng cơ chế ghi nguyên tử (Atomic Write via `.tmp.<pid>` + `os.replace` + `fsync`).

### Bẫy lỗi 4: Quét toàn bộ Codebase mù quáng (Full-Scan Drift)
* **Hiện tượng:** Agent tự ý dùng lệnh `grep -r` hoặc `find .` quét qua `node_modules` hoặc `venv`.
* **Khắc phục:** Luôn tra cứu `PROJECT_MAP.json` để lấy đường dẫn chính xác của file thuộc domain hiện tại.

### Bẫy lỗi 5: Xung đột nhánh Git & Trôi ngữ cảnh (Git Branch Drift)
* **Hiện tượng:** Chuyển sang nhánh mới nhưng `.agent/` vẫn chứa task của nhánh cũ.
* **Khắc phục:** Chạy `zeroscan sync` để tự động lọc và đồng bộ trạng thái khớp với nhánh Git hiện tại.

### Bẫy lỗi 6: Client MCP nạp tham lam làm loãng Prompt (MCP Context Bleed)
* **Hiện tượng:** MCP Client nạp toàn bộ 50 dòng lịch sử vào prompt gây tốn token.
* **Khắc phục:** Sử dụng chế độ `compact mode` của công cụ `zeroscan_read_state` ($\le 1\text{ KB}$, chỉ lấy 3 task active).

### Bẫy lỗi 7: Treo tiến trình khi Git Rebase tự động (Git Rebase Deadlock)
* **Hiện tượng:** Hook kiểm tra commit chặn tiến trình rebase tự động của CI/CD.
* **Khắc phục:** Zero-Scan Validator tự động phát hiện môi trường rebase để cho qua (non-blocking bypass) an toàn.

### Bẫy lỗi 8: Hỏng file JSON do ngắt tiến trình đột ngột (Corrupted JSON Crash)
* **Hiện tượng:** File `PROJECT_STATE.json` bị 0 byte hoặc lỗi cú pháp khi cúp điện/ngắt process.
* **Khắc phục:** Engine V2.1 tự động phục hồi từ bản sao lưu `.bak` gần nhất.
