# ZeroScan (`.agent/`) — Project Memory V2.1.3

[![CI Suite](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml/badge.svg)](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/badge/pypi-v2.1.3-blue.svg)](https://pypi.org/project/zeroscan/)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ff69b4.svg)](https://github.com/sponsors/chauvuusvn)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Context Budget](https://img.shields.io/badge/Context%20Budget-%3C=10%20KB-success.svg)](https://github.com/chauvuusvn/zeroscan)

```bash
# Cài đặt 1-chạm toàn cầu qua pip
pip install zeroscan

# Khởi tạo kiến trúc .agent/ cho bất kỳ repository nào
zeroscan-bootstrap --name "du-an-cua-ban" --mission "Xây dựng hệ sinh thái AI"
```

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README.vi.md) | [ 📘 Usage Guide ](USAGE_GUIDE.md) | [ 📕 Hướng dẫn sử dụng ](HUONG_DAN_SU_DUNG.md) | [ 🚀 Bài Viết Chuyên Sâu ](articles/zero-scan-llm-vram-optimization.vi.md)

> **Giao Thức Quản Trị Ngữ Cảnh Độc Lập Cho Mọi AI Coding Agent & LLM**  
> Tương thích toàn diện với Claude 3.5, GPT-4o, Gemini 1.5, DeepSeek-V3, Qwen 2.5, Llama 3.3, Cursor, Windsurf, Trae, Codex, và Hermes.

---

## 🌟 Tổng quan

**Zero-Scan Project Memory V2.1.3** là chuẩn mở được thiết kế nhằm xóa bỏ tình trạng phình ngữ cảnh (context bloat), ảo tưởng tiến độ (hallucination) và chi phí quét cây thư mục lặp đi lặp lại trong quy trình phát triển phần mềm bằng AI.

Các coding agent truyền thống thường lãng phí hàng chục ngàn token để quét toàn bộ codebase mỗi khi bắt đầu phiên làm việc. Project Memory thay thế việc quét bừa bãi bằng một **File neo khởi động Cấp 0** (`BOOT.md` < 1 KB) và một **Bản đồ kiến trúc GPS** (`PROJECT_MAP.json`), đảm bảo agent khởi động tức thì với tổng ngữ cảnh `<= 10 KB`.

```text
┌─────────────────────────────────────────────────────────────┐
│                    MỌI LLM / AI CODING AGENT                │
│  (Claude 3.5 · GPT-4o · Gemini 1.5 · DeepSeek · Qwen · Llama)│
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       Máy Chủ MCP Protocol              Engine CLI
      (Cursor / Windsurf / Trae)      (Terminal / CI/CD)
               │                               │
               └───────────────┬───────────────┘
                               ▼
              ┌─────────────────────────────────┐
              │      Lõi Ngữ Cảnh Zero-Scan     │
              │  • File Neo Khởi Động (BOOT)    │
              │  • Định Tuyến GPS Module (MAP)  │
              │  • Khóa File Đa Tiến Trình      │
              │  • Phục Hồi JSON Tự Động (.bak) │
              └────────────────┬────────────────┘
                               ▼
                   KHO MÃ NGUỒN GIT MỤC TIÊU
```

---

## 💡 Vì sao hệ thống tiết kiệm 90–95% Token?

### 1. Khởi động Zero-Scan (Level 0 Boot Anchor)
Các agent thông thường đọc toàn bộ kho mã nguồn trong mỗi lượt hội thoại, dễ dàng đốt 30.000–200.000+ token trước khi viết dòng code đầu tiên. Với Project Memory, agent **chỉ đọc duy nhất `BOOT.md` (~1 KB / ~500 tokens)**, ngay lập tức nắm vững kiến trúc cốt lõi và nhiệm vụ cần làm mà không cần đọc các thư mục không liên quan.

### 2. Định vị GPS qua `PROJECT_MAP.json`
Thay vì tìm kiếm regex tốn kém trên toàn bộ cây thư mục, agent tra cứu `PROJECT_MAP.json` để lấy đường dẫn chính xác của file mã nguồn và test case thuộc domain đang xử lý.

### 3. Khóa cứng quyết định kiến trúc (ADR Locking)
Mọi quyết định kiến trúc quan trọng được lưu trong `DECISIONS.md` ở trạng thái `[LOCKED]`. Agent không bao giờ tự ý đập đi xây lại các quyết định đã được Sếp phê duyệt.

### 4. Cổng bằng chứng bất biến (Immutable Evidence Gate)
Một task chỉ được coi là `DONE` khi vượt qua kiểm thử thực tế và được gắn hash với Git Commit thật (`code_commit` và `memory_commit`).

---

## 🧠 Vì Sao Zero-Scan Vĩnh Viễn Không Quên Ngữ Cảnh & Không Bị Phình To?

### 1. Chuyển Trí Nhớ Ra Ổ Đĩa Cứng (Triệt tiêu hiện tượng "Lạc Giữa Dòng" - Lost-in-the-Middle)
AI truyền thống bị mất trí nhớ khi chat dài do cửa sổ ngữ cảnh ($50\text{k} - 200\text{k}$ tokens) bị cắt xén và pha loãng. Zero-Scan đưa toàn bộ dữ liệu thực tế (Ground Truth) ra hệ thống tệp Git bất biến:
- **`BOOT.md` (< 1 KB):** Định hướng tức thì trong 1 mili-giây (Mục tiêu cốt lõi, Phase hiện tại, Task đang làm, mã Git SHA).
- **`PROJECT_MAP.json`:** Định vị GPS chính xác file mã nguồn cần chạm vào.
- **`DECISIONS.md`:** Khóa cứng toàn bộ quyết định kiến trúc đã chốt `[LOCKED]`.
- **`TASK_LEDGER.jsonl`:** Sổ cái ghi nhận bất biến các task đã xong và bằng chứng test thật.

### 2. Cơ Chế Trao Đổi Chất Tự Động (Giữ vững trần ngân sách $\le 10\text{ KB}$ trọn đời)
Dù dự án phát triển qua nhiều năm với hàng ngàn task, Zero-Scan luôn duy trì dung lượng khởi động siêu nhẹ:
- Khi `TASK_LEDGER.jsonl` vượt quá **50 tasks**, hệ thống tự động dọn các task cũ vào `.agent/archive/TASK_LEDGER_ARCHIVE.jsonl`, giữ sổ cái chính luôn $< 5\text{ KB}$.
- `BOOT.md` được render lại từ đầu mỗi lần checkpoint, tuyệt đối không bị tích lũy rác lịch sử.

### 3. Tiếp Quản Liền Mạch Giữa Đa Mô Hình (Multi-LLM Handoff)
Do bộ nhớ được chuẩn hóa trên filesystem, các AI khác nhau có thể phối hợp nhịp nhàng mà không mất ngữ cảnh:
- **Phiên 1 (Claude 3.5 Sonnet):** Xây dựng module $\rightarrow$ chạy test PASS $\rightarrow$ lưu `zeroscan checkpoint`.
- **Phiên 2 (GPT-4o hoặc DeepSeek-V3):** Đọc `BOOT.md` trong 1 mili-giây và tiếp quản công việc tức thì với độ chính xác 100%.

---

## 🛡️ Điểm Mới Trong Phiên Bản V2.1.3 (Enterprise Ready)

1. **⚡ Tự Động Đồng Bộ Cấp Nguyên Tử (Atomic State-to-Boot Auto-Sync):** Sửa `PROJECT_STATE.json` là `BOOT.md` tự cập nhật theo thời gian thực, triệt tiêu nguy cơ trôi ngữ cảnh.
2. **🔄 Phục Hồi File JSON Hỏng (Resilient JSON Loader & `.bak` Fallback):** Tự động khôi phục từ bản backup `.bak` nếu file JSON bị đứt gãy giữa chừng (Zero-Crash Guarantee).
3. **🔒 Khóa File Đồng Thời Đa Nền Tảng (Cross-Platform Concurrency Locking):** Sử dụng `fcntl.flock` trên Linux/macOS và spinlock nguyên tử trên Windows kèm cơ chế ném lỗi Timeout, bảo vệ tuyệt đối khi nhiều subagent cùng ghi dữ liệu.
4. **🛡️ Khởi Tạo An Toàn Với Cơ Chế Rollback Nguyên Tử (Atomic Bootstrap Staging):** Dựng khung trong thư mục tạm trước, chỉ tráo đổi khi 100% file đã hoàn tất.
5. **📦 Đóng Gói Dữ Liệu Offline (Package Data Bundling):** Toàn bộ template được đóng gói sẵn trong wheel của PyPI, chạy offline 100% không cần internet.
6. **📦 Tự Động Lưu Trữ Sổ Ghi Tác Vụ (Ledger Auto-Pruning):** Tự động chuyển các tác vụ cũ sang `.agent/archive/` khi vượt quá 50 tasks, bảo vệ vĩnh viễn ngân sách $\le 10\text{ KB}$.

---

## 📁 Cấu trúc bộ nhớ `.agent/`

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
└── archive/             # Thư mục lưu trữ tự động các task cũ khi vượt quá 50 tasks
```

---

## ⚠️ 8 Cạm Bẫy Thực Chiến & Quy Chuẩn Phòng Vệ (Pitfalls & Anti-Patterns)

| # | Cạm Bẫy (Pitfall / Anti-Pattern) | Nguyên Nhân Gốc Rễ | Tác Hại Thực Tế | Giao Thức Phòng Vệ Zero-Scan |
|---|---|---|---|---|
| **1** | **The Stale State Trap** | Agent làm xong việc nhưng quên cập nhật `BOOT.md` / `PROJECT_STATE.json`. | Phiên sau khởi động lại từ trạng thái cũ, làm trùng việc hoặc hỏng logic. | **Session Exit Gate**: Cưỡng chế chạy checkpoint trước khi kết thúc phiên. |
| **2** | **Decisions Bloat Trap** | Nhồi nhét hàng chục quyết định vụn vặt vào `DECISIONS.md` $> 20\text{ KB}$. | Vượt ngân sách $10\text{ KB}$, làm phình KV-cache và loãng ngữ cảnh. | **Compaction Protocol**: Nén các quyết định đã ổn định thành tiên đề, dọn phần cũ vào archive. |
| **3** | **Concurrent Corruption** | Nhiều subagent cùng lúc ghi vào `PROJECT_STATE.json`. | Ghi đè file đứt gãy hoặc mất dữ liệu (Lost Update). | **File Lock & Atomic Write**: `file_lock()` đa nền tảng + `.tmp.<pid>` + `fsync` + `os.replace`. |
| **4** | **Accidental Full-Scan Drift** | Agent gọi lệnh quét đệ quy vô tội vạ vào `node_modules` / `venv`. | Bơm $100\text{k}+$ tokens rác vào context, làm suy giảm khả năng suy luận. | **Strict GPS Routing**: Buộc Agent tra cứu `PROJECT_MAP.json` để chỉ đọc đúng file cần thiết. |
| **5** | **Phantom Commit Binding** | Đánh dấu hoàn thành task trong ledger nhưng chưa commit code thật vào git. | State ghi là "đã xong" nhưng git HEAD trỏ vào commit ảo/cũ. | **Git Verification Guard**: Validator đối chiếu hash thực tế của `git rev-parse HEAD`. |
| **6** | **Git Branch & Worktree Drift** | Đổi nhánh git nhưng `.agent/` vẫn lưu trạng thái của nhánh cũ. | Agent làm việc dựa trên mục tiêu của nhánh khác. | **Branch-Aware Ledger**: Gắn tag tên branch vào từng task, tự động lọc theo nhánh hiện hành. |
| **7** | **Greedy MCP Context Bleed** | Client MCP nạp tham lam toàn bộ 50 task vào System Prompt. | Lãng phí token và làm loãng câu lệnh prompt của người dùng. | **Selective View Filters**: Mặc định `compact mode`, chỉ trả về $\le 1\text{ KB}$ gồm 3 active tasks. |
| **8** | **Git Rebase Deadlock** | Kiểm tra commit quá cứng nhắc làm treo tiến trình `git rebase` tự động. | CI/CD hoặc lệnh squash/rebase bị fail khi ở trạng thái `detached HEAD`. | **Non-Blocking Rebase Bypass**: Validator phát hiện môi trường rebase để tự động cho qua an toàn. |

---

## 🚀 Hướng dẫn bắt đầu nhanh

```bash
# 1. Cài đặt thư viện
pip install zeroscan

# 2. Khởi tạo bộ nhớ cho dự án
zeroscan-bootstrap --name "my-project" --mission "Build Agent Fleet" --domains "core,api,auth,db"

# 3. Kiểm toán tuân thủ ngân sách ngữ cảnh
zeroscan status
zeroscan validate

# 4. Lưu checkpoint tiến độ với bằng chứng kiểm thử và cập nhật task tiếp theo
zeroscan checkpoint --task-id "TASK-001" --summary "Hoàn thành module auth" --evidence "pytest 15/15 pass" --next-task-id "TASK-002" --next-task-desc "Xây dựng API thanh toán"

# 5. Ghi nhận quyết định kiến trúc (ADR)
zeroscan add-decision --id "ADR-002" --title "Dùng PostgreSQL làm CSDL" --decision "Sử dụng Postgres 16 đảm bảo tính toàn vẹn ACID"

# 6. Chạy MCP Server cho Cursor / Claude Desktop / Windsurf
zeroscan-mcp
```

---

## 📜 Bản Quyền & Tác Giả
- **Tác giả:** Chau Vu / CPF-FAMILY (`@chauvuusvn`)
- **Giấy phép:** MIT License (Mã nguồn mở 100%)
- **Trang chủ PyPI:** [https://pypi.org/project/zeroscan/](https://pypi.org/project/zeroscan/)
