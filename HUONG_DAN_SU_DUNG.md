# 📘 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG ZEROSCAN (PROJECT MEMORY V2.2.1)

> **Dành cho:** Kỹ sư phần mềm & Toàn bộ AI Agents (Claude 3.5, GPT-4o, Gemini 1.5, DeepSeek-V3, Qwen 2.5, Llama 3.3, Cursor, Windsurf, Trae, Codex, Hermes).  
> **Phiên bản:** `v2.2.1 (Production / Enterprise Ready)` — Không phụ thuộc thư viện ngoài (Pure Python 3.9+ Stdlib).  
> **Phát hành PyPI:** `pip install --upgrade zeroscan`

---

## 🎯 1. TỔNG QUAN & MỤC TIÊU CỐT LÕI

Hệ thống **Zero-Scan Project Memory V2.2.1** (`.agent/`) giải quyết 4 điểm nghẽn lớn nhất trong việc phát triển phần mềm bằng AI Agents:

1. **Tránh lãng phí Context & Token (Zero-Scan):** Agent mới vào session không cần đọc lại 50.000–200.000 dòng code của repo. Chỉ cần nạp **Bootstrap Context (~2.4 KB)** là nắm trọn trạng thái, kiến trúc và task cần làm.
2. **Khóa kiến trúc (ADR Locking):** Ngăn chặn agent sau tự ý "sáng tạo" đập đi xây lại những quyết định kiến trúc cốt lõi đã chốt từ trước trong `DECISIONS.md`.
3. **Cổng bằng chứng (Evidence Gate):** Chỉ đánh dấu `DONE` khi có bằng chứng chạy test thật (`pytest`, `unittest`) và được gắn chặt với Git Commit Hash thật.
4. **Cơ chế tự chữa lành & Khóa đa tiến trình (Self-Healing & Concurrency Engine):** Khóa file đa nền tảng (`fcntl.flock` + Windows spinlock 30s timeout), tự động đồng bộ `BOOT.md`, phục hồi khi file JSON bị lỗi, và tự động hóa qua Git Hooks.

---

## 📁 2. CẤU TRÚC BỘ NHỚ `.agent/`

```text
.agent/
├── BOOT.md              # [BẮT BUỘC ĐỌC ĐẦU TIÊN] File neo khởi động session (< 1 KB)
├── PROJECT_STATE.json   # State machine của repo (gắn với Git code_commit & memory_commit)
├── PROJECT_MAP.json     # Bản đồ GPS codebase: Phân chia Domain -> File Paths -> Tests
├── DECISIONS.md         # Danh mục Architectural Decision Records (ADRs) ở trạng thái [LOCKED]
├── NEXT_TASK.md         # Đặc tả chi tiết task đang active, domain liên quan & tiêu chí nghiệm thu
├── TASK_LEDGER.jsonl    # Sổ cái bất biến ghi nhận toàn bộ lịch sử các task đã hoàn thành
└── memory.py            # Động cơ quản trị và đo lường metrics (thuần Python stdlib)
```

---

## 🛠️ 3. CÀI ĐẶT & DANH MỤC LỆNH CLI

### Cài đặt nhanh qua pip:
```bash
pip install --upgrade zeroscan
```

### Danh mục lệnh CLI:
```bash
# 1. Khởi tạo Zero-Scan trong dự án bất kỳ
zeroscan-bootstrap --name "du-an-cua-ban" --mission "Xây dựng hệ sinh thái AI"

# 2. Cài đặt Git Post-Commit Hook tự động đồng bộ (Tính năng mới V2.2.1)
zeroscan install-hooks

# 3. Xem báo cáo ngân sách ngữ cảnh & trạng thái thực tế
zeroscan status
zeroscan metrics

# 4. Kiểm định tính toàn vẹn nghiêm ngặt theo chuẩn JSON Schema
zeroscan validate --strict

# 5. Đánh dấu hoàn thành task và chuyển giao nhiệm vụ tiếp theo
zeroscan checkpoint \
  --task "TASK-102" \
  --desc "Hoàn thiện cơ chế bảo vệ JWT auth" \
  --commit "8a9f3b2" \
  --next-task "TASK-103" \
  --next-desc "Tích hợp cổng OAuth2"

# 6. Ghi nhận và khóa quyết định kiến trúc mới (ADR)
zeroscan add-decision \
  --id "ADR-014" \
  --title "Sử dụng Pure-Python Schema Validator" \
  --decision "Duy trì triết lý zero-dependency không cài thêm gói ngoài" \
  --context "Đảm bảo tốc độ khởi động nhanh và bảo mật chuỗi cung ứng" \
  --status "LOCKED"

# 7. Khởi động MCP Server cho Cursor / Windsurf / Claude Desktop
zeroscan-mcp
```

---

## 🌟 4. 4 TIÊU CHUẨN DOANH NGHIỆP TRONG BẢN V2.2.1

1. **Tự Động Hóa Git Hook (`zeroscan install-hooks`):**
   - Tự động tạo `.git/hooks/post-commit`. Mỗi lần dev/agent thực hiện `git commit`, `zeroscan sync` tự chạy ngầm để cập nhật `BOOT.md` và `verified_commit` với **độ trôi trạng thái bằng 0 (Zero Drift)**.
2. **Trình Kiểm Tra Schema Sâu Thuần Python:**
   - Sử dụng hàm đệ quy `validate_pure_python_schema` tích hợp sẵn, không phụ thuộc thư viện `jsonschema` bên ngoài.
   - Kiểm tra chặt chẽ các kiểu dữ liệu, mảng, object con và trường bắt buộc theo `schema/project_state.schema.json`.
3. **Bọc Khóa File `file_lock` Toàn Diện Cho Cả `BOOT.md`:**
   - Cả file trạng thái máy đọc (`PROJECT_STATE.json`) và file neo người đọc (`BOOT.md`) đều được bảo vệ bởi `file_lock` và ghi nguyên tử qua file tạm (`.tmp.{pid}` $\rightarrow$ `replace()`), chống triệt để lỗi ghi đè khi chạy đa agent song song.
4. **Tự Động Nhận Diện Không Gian Làm Việc (Workspace Discovery):**
   - MCP Server tự động đọc biến môi trường `ZEROSCAN_PROJECT_ROOT` hoặc `WORKSPACE_FOLDER` từ IDE trước khi fallback về `cwd`.

---

## 📊 5. CHỈ SỐ NGÂN SÁCH NGỮ CẢNH (CONTEXT BUDGET)

| Chỉ số | Định nghĩa | Ngưỡng giới hạn | Thực tế Zero-Scan V2.2.1 |
|---|---|---|---|
| **`BOOTSTRAP_CONTEXT_BYTES`** | Tổng dung lượng `BOOT.md` + `PROJECT_STATE.json` + `NEXT_TASK.md` | $\le$ **10.240 bytes (10 KB)** | **~2.360 bytes (23.1%)** |
| **`TOTAL_AGENT_SYSTEM_BYTES`** | Toàn bộ dung lượng thư mục `.agent/` | Tham khảo | **~29.4 KB** |
| **`KV_CACHE_SAVINGS`** | Mức độ cắt giảm VRAM GPU so với quét full repo | $\ge$ **95.0%** | **97.5% – 99.0%** |

---

## 🔒 6. 10 NGUYÊN TẮC VÀNG (GIAO THỨC BỘ NHỚ)

1. **Đọc `BOOT.md` đầu tiên:** Tuyệt đối không bắt đầu phiên bằng việc quét mù quáng cả dự án.
2. **Kích hoạt Git Hooks:** Chạy `zeroscan install-hooks` để đảm bảo đồng bộ commit thời gian thực.
3. **Điều hướng bằng `PROJECT_MAP.json`:** Chỉ mở các file thuộc domain của task hiện tại.
4. **Tôn trọng quyết định `[LOCKED]`:** Không tự ý sửa các ADRs đã bị khóa trong `DECISIONS.md`.
5. **Cổng bằng chứng nghiệm thu:** Chỉ mark `DONE` khi có bằng chứng chạy test thành công.
6. **Chống bịa đặt:** Sự thật chỉ nằm trong code, file log và Git commit hash thực tế.
7. **Tách biệt Code commit và Memory commit:** Commit code trước, ghi nhận commit SHA vào memory sau.
8. **Sổ cái Task bất biến:** Chỉ thêm mới vào `TASK_LEDGER.jsonl`, không sửa/xóa dòng cũ.
9. **Khôi phục ngữ cảnh chuẩn Zero-Scan:** Mọi phiên mới phải phục hồi 100% chỉ từ thư mục `.agent/`.
10. **Báo cáo trung thực:** Báo cáo đúng số liệu token tiêu thụ và diff kiểm thử thực tế.

---

## ⚠️ 7. 8 BẪY THƯỜNG GẶP & QUY TRÌNH PHỤC HỒI

### Bẫy 1: Phantom Commits (Đánh dấu hoàn thành nhưng chưa commit)
* **Hiện tượng:** Task được mark DONE trong sổ cái nhưng không có Git commit hash tương ứng trên nhánh.
* **Cách khắc phục:** Chạy `zeroscan validate`. Commit code trước: `git add . && git commit -m "fix: done task"`, sau đó mới chạy `zeroscan checkpoint`.

### Bẫy 2: Phình to danh mục quyết định (Decisions Bloat)
* **Hiện tượng:** File `DECISIONS.md` vượt quá 20 KB sau nhiều sprint phát triển.
* **Cách khắc phục:** Áp dụng giao thức Compaction: Gom các quyết định đã ổn định vào `PROJECT_STATE.json`, lưu trữ lịch sử sang `DECISIONS_ARCHIVE.md`.

### Bẫy 3: Xung đột ghi đè giữa nhiều Agent (Multi-Agent Race Condition)
* **Hiện tượng:** Nhiều sub-agent ghi đồng thời vào file state gây mất dữ liệu.
* **Cách khắc phục:** Động cơ tự động bọc `file_lock()` + atomic rename (`.tmp.{pid}` $\rightarrow$ `replace()`) cho cả file JSON và Markdown.

### Bẫy 4: Trôi ngữ cảnh do quét đệ quy (Accidental Full-Scan Drift)
* **Hiện tượng:** Agent tự ý chạy grep quét đệ quy vào `node_modules` hoặc `venv`.
* **Cách khắc phục:** Ép agent đọc `PROJECT_MAP.json` để định tuyến trực tiếp vào file domain.

### Bẫy 5: Lệch nhánh Git (Branch & Worktree Drift)
* **Hiện tượng:** Chuyển nhánh git khiến `.agent/` hiển thị sai nhánh đang active.
* **Cách khắc phục:** Chạy `zeroscan sync` (hoặc commit để hook tự chạy) nhằm đưa `BOOT.md` về đúng nhánh hiện tại.

### Bẫy 6: MCP Server nạp thừa context cũ (Greedy Context Bleed)
* **Hiện tượng:** IDE nạp toàn bộ lịch sử 50 task vào prompt làm loãng context.
* **Cách khắc phục:** Dùng `zeroscan_read_state` ở chế độ `compact` mặc định ($\le 1\text{ KB}$, chỉ lấy 3 task gần nhất).

### Bẫy 7: Khóa chết khi Git Rebase (Rebase Passthrough)
* **Hiện tượng:** Validator chặn các tiến trình squash merge / rebase tự động của CI.
* **Cách khắc phục:** Validator tự phát hiện môi trường `.git/rebase-merge` để cho phép bỏ qua kiểm tra nghiêm ngặt tạm thời.

### Bẫy 8: File JSON bị lỗi định dạng (Corrupted JSON Crash)
* **Hiện tượng:** File `PROJECT_STATE.json` bị 0 bytes do tiến trình bị tắt ngang.
* **Cách khắc phục:** Bộ nạp thông minh tự động khôi phục từ snapshot `.bak` liền kề.
