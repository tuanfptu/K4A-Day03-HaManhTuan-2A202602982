# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3

## BƯỚC 3 — SUBMISSION ARTIFACT

> **Họ và Tên Học viên:** Hà Mạnh Tuân
> **Mã Sinh Viên / Mã Học viên:** 2A202602982
> **Chủ đề Lựa chọn:** AI Research Assistant – Literature Review & Research Gap Discovery

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX

| Tiêu chí Đánh giá           | Mức độ (1–5) | Giải trình chi tiết lý do chọn điểm                                                                                                                                                                                                          |
| :-------------------------- | :----------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Multi-step Reasoning** |    **5/5**   | Agent phải thực hiện chuỗi nhiều bước gồm tìm literature, đọc Observation, phân tích limitation, xác định potential research gap, đánh giá feasibility và tạo research plan.                                                                 |
| **2. Tool Interaction**     |    **5/5**   | Hệ thống sử dụng MCP Server để gọi hai Tool là `search_papers` và `create_research_plan`. LLM quyết định khi nào cần Tool và truyền arguments tương ứng.                                                                                     |
| **3. Dynamic Decision**     |    **5/5**   | Hành động tiếp theo phụ thuộc vào kết quả Observation. Ví dụ, sau `search_papers`, Agent phân tích limitation rồi mới quyết định có cần gọi `create_research_plan` hay không. Khi nhận `NOT_FOUND`, Agent dừng và không tự tạo research gap. |
| **4. Long Horizon Goal**    |    **4/5**   | Với yêu cầu phức tạp, Agent phải duy trì mục tiêu ban đầu xuyên suốt nhiều vòng ReAct, từ literature retrieval đến research plan. Tuy nhiên số bước của bài Lab vẫn tương đối ngắn.                                                          |
| **TỔNG ĐIỂM AGENTIC FIT**   |   **19/20**  | **Bài toán rất phù hợp để triển khai Agentic System.**                                                                                                                                                                                       |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG

> ⚠️ **YÊU CẦU NGHIỆM THU:** Hệ thống được chạy với LLM API thật thông qua `GeminiProvider`.
> MCP Server sử dụng hai Tool: `search_papers` và `create_research_plan`.
> Tool `search_papers` trong phạm vi Lab sử dụng mock research database để mô phỏng nguồn dữ liệu nghiên cứu; Gemini thật chịu trách nhiệm suy luận và Native Function Calling.

### 2.1. Luồng ReAct tiêu biểu — TC04 Multi-step Reasoning

**User Query:**

> Hãy tìm các paper về risky driving prediction, phân tích limitation của chúng và đề xuất một research gap khả thi với GPU RTX 3090 24GB.

Luồng thực thi:

```text
User Query
    ↓
Gemini Decision
    ↓
search_papers
    ↓
Observation: 5 papers
    ↓
Phân tích limitation / potential research gap
    ↓
create_research_plan
    ↓
Observation: Research Plan
    ↓
Final Answer
```

Đoạn trích Waterfall Trace tiêu biểu:

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_papers",
    "arguments": {
      "query": "risky driving prediction"
    },
    "observation": {
      "status": "SUCCESS",
      "query": "risky driving prediction",
      "papers_found": 5
    }
  },
  {
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "create_research_plan",
    "arguments": {
      "research_topic": "risky driving prediction",
      "resource_constraint": "Single RTX 3090 24GB",
      "research_gap": "Các phương pháp hiện tại chưa đánh giá đầy đủ tính robust dưới điều kiện thời tiết bất lợi và còn tồn tại hạn chế về tài nguyên tính toán."
    },
    "observation": {
      "status": "SUCCESS",
      "message": "Đã tạo research plan thành công."
    }
  },
  {
    "step": 3,
    "action_type": "FINAL_ANSWER",
    "output": "Agent tổng hợp literature evidence, limitation, potential research gap và research plan phù hợp với Single RTX 3090 24GB."
  }
]
```

### 2.2. Kết quả 5 Test Cases

| Test Case | Mục tiêu                       | Flow thực tế                                                                      | Kết quả |
| :-------- | :----------------------------- | :-------------------------------------------------------------------------------- | :-----: |
| **TC01**  | Direct Query                   | `Final Answer`                                                                    |  ✅ PASS |
| **TC02**  | Single Tool Query              | `search_papers → Observation → Final Answer`                                      |  ✅ PASS |
| **TC03**  | Research Plan Creation         | `create_research_plan → Observation → Final Answer`                               |  ✅ PASS |
| **TC04**  | Multi-step Reasoning           | `search_papers → Observation → create_research_plan → Observation → Final Answer` |  ✅ PASS |
| **TC05**  | Edge Case / Anti-Hallucination | `search_papers → NOT_FOUND → Final Answer`                                        |  ✅ PASS |

### 2.3. Edge Case — TC05

Với chủ đề không tồn tại:

```text
XYZ-Nonexistent-Research-Topic-99999
```

Tool trả về:

```json
{
  "status": "NOT_FOUND",
  "query": "XYZ-Nonexistent-Research-Topic-99999",
  "message": "Không tìm thấy paper phù hợp với chủ đề 'XYZ-Nonexistent-Research-Topic-99999'. Không đủ evidence để xác định research gap."
}
```

Agent sau đó tuân thủ quy tắc **Anti-Hallucination**:

* Không tự bịa paper.
* Không tạo citation giả.
* Không tự suy diễn research gap khi không có evidence.
* Không gọi `create_research_plan` khi literature retrieval thất bại.
* Trả lời rõ rằng cần điều chỉnh hoặc mở rộng từ khóa tìm kiếm.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

* [x] Đã cấu hình API Key thật trong `.env`.
* [x] Đã chạy Agent bằng **GeminiProvider**.
* [x] Đã sử dụng Native Function Calling với MCP Tools.
* [x] Đã thực thi đầy đủ **5/5 Test Cases**.
* [x] Không còn Test Case ở trạng thái TODO.
* [x] Đã sinh `docs/trace_waterfall.json`.
* [x] Đã backup trace nghiệm thu thành `docs/trace_waterfall_gemini_final.json`.
* [x] TC04 thực hiện thành công Multi-step ReAct.
* [x] TC05 xử lý thành công trường hợp `NOT_FOUND` và Anti-Hallucination.

**Tổng số Test Cases đã chạy thành công:** **5 / 5**

**Số lượt gọi Tool qua MCP Server chính xác:** **5 lượt**

Chi tiết:

```text
TC01: 0 Tool Call
TC02: 1 Tool Call  — search_papers
TC03: 1 Tool Call  — create_research_plan
TC04: 2 Tool Calls — search_papers → create_research_plan
TC05: 1 Tool Call  — search_papers

TOTAL: 5 Tool Calls
```

**Số Waterfall Trace Events:** **10 events**

**LLM Provider:** `GeminiProvider`

**MCP Server:** `research-assistant-mcp-server`

**Tools:**

```text
search_papers
create_research_plan
```

**Kết quả đẩy Repo nộp bài:**

* [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

## 4. NHẬN XÉT SAU BÀI LAB

Qua bài Lab, em hiểu rõ sự khác biệt giữa một LLM Chatbot thông thường và một ReAct Agent có khả năng sử dụng Tool.

Chatbot chỉ có thể tạo phản hồi trực tiếp dựa trên context và kiến thức của mô hình, trong khi Agent có thể chủ động quyết định khi nào cần gọi Tool, nhận Observation từ môi trường và tiếp tục đưa ra quyết định ở bước tiếp theo.

Trong TC04, Agent đã thực hiện được một chuỗi ReAct nhiều bước:

```text
Thought / Decision
    ↓
search_papers
    ↓
Observation
    ↓
Decision
    ↓
create_research_plan
    ↓
Observation
    ↓
Final Answer
```

Bài Lab cũng cho thấy vai trò quan trọng của **MCP Server** trong việc chuẩn hóa giao tiếp giữa Agent và các Tool, cũng như vai trò của **Waterfall Trace** trong việc quan sát, debug và đánh giá quá trình Agent thực thi.

Ngoài ra, TC05 cho thấy Agent cần có cơ chế xử lý failure và Anti-Hallucination thay vì cố gắng tạo ra câu trả lời khi Tool không cung cấp đủ evidence.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Commit và Push toàn bộ mã nguồn, Test Cases, Waterfall Trace và báo cáo  lên GitHub Repository cá nhân, sau đó sao chép đường link Repository và nộp trên LMS VLearn.
