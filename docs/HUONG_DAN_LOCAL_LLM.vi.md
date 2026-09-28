# Hướng Dẫn Tối Ưu Local LLM: Cắt Giảm 97.5% VRAM & KV-Cache Với Zero-Scan

> **Cách Zero-Scan triệt tiêu lỗi CUDA Out-Of-Memory (OOM) và giải phóng VRAM động khi chạy LLM trên GPU cá nhân (RTX 3060/4060/4070/4090 & Apple Silicon).**

---

## 1. Bài Toán VRAM Của Local LLM: Trọng Số Model vs. KV-Cache

Khi chạy mô hình AI cục bộ qua **Ollama, vLLM, LM Studio, llama.cpp, OpenCode, hoặc Hermes**, tổng dung lượng VRAM tiêu thụ được cấu thành bởi:

$$\text{Tổng VRAM} = \text{VRAM Trọng số (Model Weights)} + \text{VRAM Bộ nhớ đệm (KV-Cache)} + \text{VRAM Overhead Hệ điều hành}$$

1. **Trọng số Model (Cố định):** Dung lượng tĩnh phụ thuộc vào số lượng tham số và mức lượng tử hóa (VD: Qwen2.5-Coder-14B Q4_K_M $\approx 8.5\text{ GB}$). Zero-Scan không can thiệp vào trọng số tĩnh này.
2. **KV-Cache (Bộ nhớ đệm động):** Bộ nhớ GPU lưu trữ ma trận Key-Value cho toàn bộ token ngữ cảnh hội thoại và mã nguồn nạp vào. **Zero-Scan cắt giảm tới 97.5% KV-Cache** bằng cách thay thế việc quét toàn bộ repository bằng Boot Anchor chuẩn hóa ($\le 1\text{ KB}$).

---

## 2. Bằng Chứng Toán Học Về Cắt Giảm KV-Cache

Với kiến trúc **Grouped-Query Attention (GQA)** hiện đại:

$$\text{Dung lượng KV-Cache mỗi Token (Bytes)} = 2 \times N_{\text{layers}} \times N_{\text{kv\_heads}} \times d_{\text{head}} \times B_{\text{precision}}$$

*Ở định dạng FP16 ($B_{\text{precision}} = 2\text{ bytes}$):*

### A. Qwen2.5-Coder-14B ($48\text{ layers}, 8\text{ KV heads}, d_{\text{head}}=128$):
- **Dung lượng trên mỗi token:** $2 \times 48 \times 8 \times 128 \times 2 = 196,608\text{ bytes} \approx 0.1966\text{ MB/token}$.
- **Quét Full Repo thông thường ($40,000\text{ tokens}$):** $40,000 \times 0.1966\text{ MB} = \mathbf{7.86\text{ GB VRAM}}$ (chỉ riêng KV-Cache).
- **Giao thức Zero-Scan ($1,000\text{ tokens}$):** $1,000 \times 0.1966\text{ MB} = \mathbf{0.196\text{ GB (196 MB) VRAM}}$.
- **VRAM Tiết Kiệm Được:** **$7.66\text{ GB}$ (Giảm $97.5\%$)**.

### B. Qwen2.5-Coder-32B ($64\text{ layers}, 8\text{ KV heads}, d_{\text{head}}=128$):
- **Dung lượng trên mỗi token:** $2 \times 64 \times 8 \times 128 \times 2 = 262,144\text{ bytes} \approx 0.262\text{ MB/token}$.
- **Quét Full Repo thông thường ($40,000\text{ tokens}$):** $40,000 \times 0.262\text{ MB} = \mathbf{10.48\text{ GB VRAM}}$.
- **Giao thức Zero-Scan ($1,000\text{ tokens}$):** $1,000 \times 0.262\text{ MB} = \mathbf{0.262\text{ GB (262 MB) VRAM}}$.
- **VRAM Tiết Kiệm Được:** **$10.22\text{ GB}$ (Giảm $97.5\%$)**.

---

## 3. Bảng Tương Thích Phần Cứng Thực Tế

| Card Đồ Họa / Thiết Bị | VRAM Thực Tế | Model Mục Tiêu | Không Có Zero-Scan ($40\text{k}$ tokens) | Có Zero-Scan ($1\text{k}$ tokens) | Trạng Thái Vận Hành |
|---|---|---|---|---|---|
| **RTX 3060 / 4060** | **12 GB** | Qwen2.5-Coder 14B Q4 | $8.5\text{ GB} + 7.86\text{ GB} = \mathbf{16.36\text{ GB}}$ | $8.5\text{ GB} + 0.20\text{ GB} = \mathbf{8.70\text{ GB}}$ | **CHẠY MƯỢT ✅ (Trước đó bị OOM ❌)** |
| **RTX 4070 / 4070 Ti**| **12 GB** | DeepSeek-Coder 14B Q4 | $8.5\text{ GB} + 7.86\text{ GB} = \mathbf{16.36\text{ GB}}$ | $8.5\text{ GB} + 0.20\text{ GB} = \mathbf{8.70\text{ GB}}$ | **CHẠY MƯỢT ✅ (Trước đó bị OOM ❌)** |
| **RTX 4080** | **16 GB** | Qwen2.5-Coder 32B Q4 | $19.5\text{ GB} + 10.48\text{ GB} = \mathbf{29.98\text{ GB}}$ | $19.5\text{ GB} + 0.26\text{ GB} = \mathbf{19.76\text{ GB}}$ (Offload 4GB) | **CHẠY TỐT ✅** |
| **RTX 4090** | **24 GB** | Qwen2.5-Coder 32B Q4 | $19.5\text{ GB} + 10.48\text{ GB} = \mathbf{29.98\text{ GB}}$ | $19.5\text{ GB} + 0.26\text{ GB} = \mathbf{19.76\text{ GB}}$ | **100% NẰM TRONG VRAM ✅** |
| **MacBook M2/M3 Pro**| **18 GB Unified**| Qwen2.5-Coder 14B Q8 | $14.5\text{ GB} + 7.86\text{ GB} = \mathbf{22.36\text{ GB}}$ | $14.5\text{ GB} + 0.20\text{ GB} = \mathbf{14.70\text{ GB}}$ | **KHÔNG BỊ TRÀN SWAP RAM ✅** |

---

## 4. Lợi Ích Về Tốc Độ & Độ Chuẩn Xác

1. **Triệt Tiêu Độ Trễ Phản Hồi Ban Đầu (TTFT):**
   - Quá trình nạp và tính toán ma trận (prefill) cho $40,000$ tokens trên RTX 4070 mất từ **15–25 giây**.
   - Với Zero-Scan, prefill chỉ $1,000$ tokens chỉ mất **0.15–0.30 giây**, giúp AI phản hồi gõ chữ tức thì.
2. **Khắc Phục Hiện Tượng "Mất Tập Trung" (Lost-in-the-Middle):**
   - Các mô hình cục bộ quy mô nhỏ ($7\text{B}–14\text{B}$) rất dễ bị loãng sự chú ý khi nạp toàn bộ repo rác.
   - Zero-Scan cung cấp ngữ cảnh tinh gọn và trọng tâm nhất (`BOOT.md` + `NEXT_TASK.md`), triệt tiêu hiện tượng ảo giác (hallucination).
