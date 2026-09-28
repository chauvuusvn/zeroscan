# Local LLM Optimization Guide: Slashing VRAM & KV-Cache with Zero-Scan

> **How Zero-Scan cuts dynamic GPU VRAM by up to 97.5% and eliminates CUDA Out-Of-Memory (OOM) errors on consumer hardware (RTX 3060/4060/4070/4090 & Apple Silicon).**

---

## 1. The Local LLM Dilemma: Model Weights vs. KV-Cache

When running large language models locally via **Ollama, vLLM, LM Studio, llama.cpp, OpenCode, or Hermes**, total GPU VRAM consumption is governed by two fundamental components:

$$\text{Total VRAM} = \text{VRAM}_{\text{Model Weights}} + \text{VRAM}_{\text{KV-Cache}} + \text{VRAM}_{\text{CUDA Overhead}}$$

1. **Model Weights (Static):** Fixed footprint based on parameter count and quantization (e.g., Qwen2.5-Coder-14B Q4_K_M $\approx 8.5\text{ GB}$). Zero-Scan does not alter static weights.
2. **KV-Cache (Dynamic):** Memory allocated to store Key-Value attention tensors for all input and generated tokens. **Zero-Scan reduces dynamic KV-Cache by 95%–98%** by replacing raw repository scanning with compact, deterministic Boot Anchors ($\le 1\text{ KB}$).

---

## 2. Mathematical Proof of KV-Cache Reduction

In modern Transformer architectures with **Grouped-Query Attention (GQA)**:

$$\text{KV-Cache Per Token (Bytes)} = 2 \times N_{\text{layers}} \times N_{\text{kv\_heads}} \times d_{\text{head}} \times B_{\text{precision}}$$

*For FP16 ($B_{\text{precision}} = 2\text{ bytes}$):*

### A. Qwen2.5-Coder-14B ($48\text{ layers}, 8\text{ KV heads}, d_{\text{head}}=128$):
- **Per-Token Footprint:** $2 \times 48 \times 8 \times 128 \times 2 = 196,608\text{ bytes} \approx 0.1966\text{ MB/token}$.
- **Traditional Scan ($40,000\text{ tokens}$):** $40,000 \times 0.1966\text{ MB} = \mathbf{7.86\text{ GB VRAM}}$ (KV-Cache only).
- **Zero-Scan Protocol ($1,000\text{ tokens}$):** $1,000 \times 0.1966\text{ MB} = \mathbf{0.196\text{ GB (196 MB) VRAM}}$.
- **VRAM Saved:** **$7.66\text{ GB}$ ($97.5\%$ reduction)**.

### B. Qwen2.5-Coder-32B ($64\text{ layers}, 8\text{ KV heads}, d_{\text{head}}=128$):
- **Per-Token Footprint:** $2 \times 64 \times 8 \times 128 \times 2 = 262,144\text{ bytes} \approx 0.262\text{ MB/token}$.
- **Traditional Scan ($40,000\text{ tokens}$):** $40,000 \times 0.262\text{ MB} = \mathbf{10.48\text{ GB VRAM}}$.
- **Zero-Scan Protocol ($1,000\text{ tokens}$):** $1,000 \times 0.262\text{ MB} = \mathbf{0.262\text{ GB (262 MB) VRAM}}$.
- **VRAM Saved:** **$10.22\text{ GB}$ ($97.5\%$ reduction)**.

---

## 3. Consumer Hardware Feasibility Matrix

| Consumer Hardware | Total VRAM | Model Target | Without Zero-Scan ($40\text{k}$ tokens) | With Zero-Scan ($1\text{k}$ tokens) | Status |
|---|---|---|---|---|---|
| **RTX 3060 / 4060** | **12 GB** | Qwen2.5-Coder 14B Q4 | $8.5\text{ GB} + 7.86\text{ GB} = \mathbf{16.36\text{ GB}}$ | $8.5\text{ GB} + 0.20\text{ GB} = \mathbf{8.70\text{ GB}}$ | **PASSED ✅ (Was OOM Crash ❌)** |
| **RTX 4070 / 4070 Ti**| **12 GB** | DeepSeek-Coder 14B Q4 | $8.5\text{ GB} + 7.86\text{ GB} = \mathbf{16.36\text{ GB}}$ | $8.5\text{ GB} + 0.20\text{ GB} = \mathbf{8.70\text{ GB}}$ | **PASSED ✅ (Was OOM Crash ❌)** |
| **RTX 4080** | **16 GB** | Qwen2.5-Coder 32B Q4 | $19.5\text{ GB} + 10.48\text{ GB} = \mathbf{29.98\text{ GB}}$ | $19.5\text{ GB} + 0.26\text{ GB} = \mathbf{19.76\text{ GB}}$ (Offload 4GB) | **RUNNABLE ✅** |
| **RTX 4090** | **24 GB** | Qwen2.5-Coder 32B Q4 | $19.5\text{ GB} + 10.48\text{ GB} = \mathbf{29.98\text{ GB}}$ | $19.5\text{ GB} + 0.26\text{ GB} = \mathbf{19.76\text{ GB}}$ | **100% IN VRAM ✅** |
| **MacBook M2/M3 Pro**| **18 GB Unified**| Qwen2.5-Coder 14B Q8 | $14.5\text{ GB} + 7.86\text{ GB} = \mathbf{22.36\text{ GB}}$ | $14.5\text{ GB} + 0.20\text{ GB} = \mathbf{14.70\text{ GB}}$ | **ZERO SWAP LAG ✅** |

---

## 4. Latency & Attention Benefits

1. **Near-Zero Time-to-First-Token (TTFT):**
   - Prefilling $40,000$ tokens on an RTX 4070 takes **15–25 seconds** of compute lockup.
   - Prefilling $1,000$ tokens takes **0.15–0.30 seconds**, yielding instantaneous response streaming.
2. **Mitigating "Lost-In-The-Middle":**
   - Smaller local models ($7\text{B}–14\text{B}$) suffer severe attention dilution when flooded with entire codebases.
   - Zero-Scan provides laser-focused context (`BOOT.md` + `NEXT_TASK.md`), increasing task completion accuracy and preventing hallucinations.

---

## 5. Integration Guide for Local Runtimes

### A. Ollama + Zero-Scan
```bash
# 1. Pull lightweight coding model
ollama pull qwen2.5-coder:14b-instruct-q4_K_M

# 2. Bootstrap Zero-Scan in your local project
zeroscan-bootstrap --name "my-local-project" --mission "Local development"

# 3. Install auto-sync hooks
zeroscan install-hooks
```

### B. MCP Server with Claude Desktop / Cursor / LM Studio
Add Zero-Scan MCP Server to your configuration:
```json
{
  "mcpServers": {
    "zeroscan": {
      "command": "zeroscan-mcp",
      "env": {
        "ZEROSCAN_PROJECT_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

---

## 6. Summary

Zero-Scan fundamentally transforms consumer-grade hardware into viable AI coding workstations. By controlling context inflation at the protocol level, developers can run capable $14\text{B}–32\text{B}$ parameter models locally without expensive server clusters or cloud API bills.
