# ZeroScan (`.agent/`) — Project Memory V2.2.0

[![CI Suite](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml/badge.svg)](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/badge/pypi-v2.2.0-blue.svg)](https://pypi.org/project/zeroscan/)
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

## 🌟 Tổng Quan & Bản Chất Kỹ Thuật Thực Tế

**Zero-Scan (`.agent/`)** là một quy chuẩn quản trị trạng thái dự án trên hệ thống tệp Git, được thiết kế nhằm giải quyết **chi phí token khởi động phiên** và **hiện tượng AI quên quyết định cũ** trong quy trình lập trình bằng AI.

### Zero-Scan Thực Sự Giải Quyết Được Gì:
1. **Tiết Kiệm Token Khởi Động Phiên (Bootstrap Tokens):** Thay vì để AI (Claude Code, Cursor, Aider, Hermes) chạy lệnh quét mù quáng 50–100 file mỗi khi mở phiên chat mới (đốt mất 30.000–80.000 tokens mỗi lần), AI chỉ cần đọc 1 file `BOOT.md` (~500 bytes / ~150 tokens) để nắm ngay task đang làm, ràng buộc kỹ thuật và phạm vi kiểm thử.
2. **Không Còn Độ Trễ Khởi Động:** Bỏ qua toàn bộ bước quét cây thư mục; AI sẵn sàng làm việc ngay sau < 1 giây.
3. **Chống Quên Quyết Định Cũ & Tránh Vỡ Code (Regressions):** Lưu toàn bộ quyết định kiến trúc bất biến ra file `DECISIONS.md` trên đĩa cứng, đảm bảo AI không tự ý phá vỡ các quy tắc đã chốt khi ngữ cảnh chat dài bị nén.
4. **Hỗ Trợ Chuyển Đổi Model Linh Hoạt:** Cho phép dùng model đắt tiền (Claude) để lên kiến trúc ban đầu, sau đó chuyển sang model giá rẻ (GPT-4o, DeepSeek-V3, Gemini Flash) viết code tiếp mà không bị mất dấu nhiệm vụ.

### Những Gì Zero-Scan KHÔNG Làm (Sự Thật Kỹ Thuật):
* Zero-Scan **không thể và không nén toàn bộ mã nguồn** vào 10 KB. Khi AI bắt tay vào viết code hoặc debug module thực tế, nó vẫn phải đọc/ghi các file mã nguồn thật và tiêu thụ token như bình thường.
* Quy chuẩn phụ thuộc vào **tính kỷ luật**: Lập trình viên hoặc AI phải chạy lệnh ghi nhận tiến độ (`zeroscan checkpoint`) để đồng bộ trạng thái trên đĩa với thay đổi code thực tế.

```text
┌─────────────────────────────────────────────────────────────┐
│                    MỌI LLM / AI CODING AGENT                │
│  (Claude · GPT-4o · Gemini · DeepSeek · Qwen · Llama)       │
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

## 💡 Lợi Ích Thực Tế & Cơ Chế Hoạt Động

### 1. Khởi Động Nhanh (`BOOT.md` < 1 KB)
Thay vì đọc toàn bộ kho mã nguồn mỗi khi bắt đầu phiên, AI chỉ đọc `BOOT.md` (~150 tokens) để nắm bắt tiến độ, bỏ qua các bước quét thư mục tốn kém ban đầu.

### 2. Định Vị GPS Qua `PROJECT_MAP.json`
Thay vì tìm kiếm regex toàn bộ cây thư mục, AI tra cứu `PROJECT_MAP.json` để mở thẳng các file và test case thuộc domain đang xử lý.

### 3. Khóa Cứng Quyết Định Kiến Trúc (`DECISIONS.md`)
Mọi quyết định kiến trúc và bảo mật quan trọng được lưu vĩnh viễn trong `DECISIONS.md`. AI không thể tự ý thay đổi hoặc quên các quyết định đã được duyệt khi chat dài.

### 4. Cổng Bằng Chứng Bất Biến & Gắn Mã Git SHA
Một task chỉ được coi là `DONE` khi vượt qua kiểm thử thực tế (`pytest`, `unittest`) và được gắn hash với Git Commit thật.

---

## 🧠 Cơ Chế Quản Lý Vòng Đời Trạng Thái

### 1. Dữ Liệu Trên Đĩa vs. Ngữ Cảnh Chat Dễ Biến Động
Cửa sổ chat của LLM sẽ tự động nén hoặc cắt ngắn khi hội thoại vượt quá 50k–100k tokens. Zero-Scan chuyển toàn bộ dữ liệu trạng thái sang hệ thống tệp Git bất biến:
- **`BOOT.md` (< 1 KB):** Định hướng tức thì trong 1 mili-giây (Mục tiêu, Phase hiện tại, Task đang làm, Git Commit SHA).
- **`PROJECT_MAP.json`:** Bản đồ định vị file theo domain.
- **`DECISIONS.md`:** Danh sách quy tắc kiến trúc bắt buộc `[LOCKED]`.
- **`TASK_LEDGER.jsonl`:** Sổ cái ghi nhận các task đã xong và bằng chứng test thật.

### 2. Tự Động Nén Sổ Cái (Chống Phình Dung Lượng Đĩa)
- Khi `TASK_LEDGER.jsonl` vượt quá **50 tasks**, hệ thống tự động dọn các task cũ vào `.agent/archive/TASK_LEDGER_ARCHIVE.jsonl`, giữ sổ cái chính luôn $< 5\text{ KB}$.
- `BOOT.md` được render lại từ đầu mỗi lần checkpoint, tuyệt đối không bị tích lũy rác lịch sử.

### 3. Tiếp Quản Liền Mạch Giữa Đa Mô Hình (Multi-LLM Handoff)
- **Phiên 1 (ví dụ Claude):** Xây dựng module $\rightarrow$ chạy test PASS $\rightarrow$ lưu `zeroscan checkpoint`.
- **Phiên 2 (ví dụ GPT-4o / DeepSeek / Gemini):** Đọc `BOOT.md` trong 1 mili-giây và tiếp quản công việc tức thì với độ chính xác 100%.

---

## 🛡️ Điểm Mới Trong Phiên Bản V2.2.0 (Enterprise Ready)

1. **⚡ Tự Động Đồng Bộ Cấp Nguyên Tử (Atomic State-to-Boot Auto-Sync):** Sửa `PROJECT_STATE.json` là `BOOT.md` tự cập nhật theo thời gian thực, triệt tiêu nguy cơ trôi ngữ cảnh.
2. **🔄 Phục Hồi File JSON Hỏng (Resilient JSON Loader & `.bak` Fallback):** Tự động khôi phục từ bản backup `.bak` nếu file JSON bị đứt gãy giữa chừng (Zero-Crash Guarantee).
3. **🔒 Khóa File Đồng Thời Đa Nền Tảng (Cross-Platform Concurrency Locking):** Sử dụng `fcntl.flock` trên Linux/macOS và spinlock nguyên tử trên Windows kèm cơ chế ném lỗi Timeout, bảo vệ tuyệt đối khi nhiều subagent cùng ghi dữ liệu.
4. **🛡️ Khởi Tạo An Toàn Với Cơ Chế Rollback Nguyên Tử (Atomic Bootstrap Staging):** Dựng khung trong thư mục tạm trước, chỉ tráo đổi khi 100% file đã hoàn tất.
5. **📦 Đóng Gói Dữ Liệu Offline (Package Data Bundling):** Toàn bộ template được đóng gói sẵn trong wheel của PyPI, chạy offline 100% không cần internet.
6. **📦 Tự Động Lưu Trữ Sổ Ghi Tác Vụ (Ledger Auto-Pruning):** Tự động chuyển các tác vụ cũ sang `.agent/archive/` khi vượt quá 50 tasks, bảo vệ vĩnh viễn ngân sách $\le 10\text{ KB}$.
7. **🔍 Động Cơ Truy Xuất Động JIT RAG (Level-2 Just-In-Time RAG Engine):** Tích hợp truy xuất ngữ cảnh sâu siêu tốc (~17ms) khi cần tra cứu chi tiết lịch sử/kỹ thuật, xóa bỏ hoàn toàn thao tác quét đĩa thô lãng phí token.

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
