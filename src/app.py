"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)

AI Research Assistant:
Literature Review & Research Gap Discovery

So sánh:
- Cấp 2: LLM Chatbot
- Cấp 3: ReAct Agent + MCP Server
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
)
from providers import get_llm_provider


load_dotenv()


# ==============================================================================
# CONFIG / FILE IO
# ==============================================================================

def load_test_cases():
    """Tải danh sách Test Cases."""

    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    config_path = os.path.join(
        base_dir,
        "config",
        "test_cases.json"
    )

    if not os.path.exists(config_path):

        example_path = os.path.join(
            base_dir,
            "config",
            "test_cases.example.json"
        )

        if os.path.exists(example_path):

            print(
                "⚠️ [CONFIG NOTICE]: "
                "Chưa thấy 'config/test_cases.json'. "
                "Đang dùng file example."
            )

            config_path = example_path

        else:
            config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Lưu Waterfall Trace vào docs/trace_waterfall.json."""

    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    docs_dir = os.path.join(
        base_dir,
        "docs"
    )

    os.makedirs(
        docs_dir,
        exist_ok=True
    )

    trace_path = os.path.join(
        docs_dir,
        "trace_waterfall.json"
    )

    with open(
        trace_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            trace_data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"📊 [OBSERVABILITY]: "
        f"Đã lưu {len(trace_data)} sự kiện "
        f"Waterfall Trace tại '{trace_path}'!"
    )


# ==============================================================================
# LEVEL 2 — BASELINE CHATBOT
# ==============================================================================

def run_baseline_chatbot(
    user_query: str,
    provider
):
    """
    LLM Chatbot không có quyền sử dụng Tool.
    """

    print(
        f"\n💬 [CHATBOT BASELINE] "
        f"Câu hỏi: {user_query}"
    )

    response = provider.generate(
        user_query,
        system_prompt=CHATBOT_BASELINE_PROMPT
    )

    print(
        f"🤖 Chatbot phản hồi:\n"
        f"{response}"
    )


# ==============================================================================
# HELPER — BUILD NEXT REACT PROMPT
# ==============================================================================

def build_react_context(
    original_query: str,
    observations: list
) -> str:
    """
    Tạo prompt cho vòng ReAct tiếp theo.

    Vì provider hiện tại nhận một prompt string thay vì
    conversation history đầy đủ, Observation được đưa trở lại
    prompt để LLM có thể tiếp tục suy luận.
    """

    if not observations:
        return original_query

    observation_text = json.dumps(
        observations,
        ensure_ascii=False,
        indent=2
    )

    return f"""
YÊU CẦU BAN ĐẦU CỦA NGƯỜI DÙNG:

{original_query}


CÁC ACTION / OBSERVATION ĐÃ THỰC HIỆN:

{observation_text}


Hãy tiếp tục giải quyết YÊU CẦU BAN ĐẦU dựa trên các Observation trên.

QUY TẮC:

1. Không gọi lại một Tool với cùng tham số nếu kết quả đã có.
2. Nếu đã đủ evidence để trả lời, hãy trả lời Final Answer.
3. Nếu vẫn cần một hành động khác để hoàn thành yêu cầu,
   hãy gọi Tool phù hợp tiếp theo.
4. Không được bịa paper, kết quả, citation hoặc research gap.
5. Nếu Observation trả về NOT_FOUND hoặc không đủ evidence,
   phải nói rõ điều đó.
"""


# ==============================================================================
# LEVEL 3 — REACT AGENT
# ==============================================================================

def run_react_agent(
    user_query: str,
    provider,
    mcp_server: MCPAcademicServer
) -> list:

    """
    ReAct Agent Loop:

    Thought
        ↓
    Action
        ↓
    MCP Tool
        ↓
    Observation
        ↓
    Thought
        ↓
    Next Action / Final Answer
    """

    print(
        f"\n🤖 [REACT AGENT] "
        f"Câu hỏi: {user_query}"
    )

    step = 0

    trace_logs = []

    observation_history = []

    executed_calls = set()

    tools_list = mcp_server.list_tools()

    working_prompt = user_query

    final_answer_generated = False

    # ==========================================================================
    # REACT LOOP
    # ==========================================================================

    while step < MAX_ITERATIONS:

        step += 1

        step_start_time = time.time()

        print(
            f"\n--- 🔄 ReAct Loop "
            f"(Step {step}/{MAX_ITERATIONS}) ---"
        )

        # ----------------------------------------------------------------------
        # THOUGHT
        # ----------------------------------------------------------------------

        llm_response = provider.generate_with_tools(
            working_prompt,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )

        llm_latency_ms = round(
            (time.time() - step_start_time) * 1000,
            2
        )

        thought = llm_response.get(
            "thought",
            "Đang suy luận..."
        )

        print(
            f"🧠 [Thought]: "
            f"{thought}"
        )

        response_type = llm_response.get(
            "type"
        )

        # ======================================================================
        # CASE 1 — FINAL ANSWER
        # ======================================================================

        if response_type == "text":

            final_content = llm_response.get(
                "content",
                ""
            )

            print(
                f"🏁 [Final Answer]: "
                f"{final_content}"
            )

            trace_logs.append(
                {
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": thought,
                    "output": final_content,
                    "latency_ms": llm_latency_ms
                }
            )

            final_answer_generated = True

            break

        # ======================================================================
        # CASE 2 — TOOL CALL
        # ======================================================================

        elif response_type == "tool_call":

            tool_name = llm_response.get(
                "tool_name"
            )

            arguments = llm_response.get(
                "arguments",
                {}
            )

            print(
                f"🛠️ [Action Proposed]: "
                f"{tool_name}({arguments})"
            )

            # ------------------------------------------------------------------
            # Validate Tool
            # ------------------------------------------------------------------

            if not tool_name:

                error_message = (
                    "LLM yêu cầu Tool Call nhưng "
                    "không cung cấp tool_name."
                )

                print(
                    f"❌ {error_message}"
                )

                trace_logs.append(
                    {
                        "step": step,
                        "query": user_query,
                        "action_type": "INVALID_TOOL_CALL",
                        "thought": thought,
                        "output": error_message,
                        "latency_ms": llm_latency_ms
                    }
                )

                break

            # ------------------------------------------------------------------
            # Prevent duplicate infinite loops
            # ------------------------------------------------------------------

            call_fingerprint = json.dumps(
                {
                    "tool": tool_name,
                    "arguments": arguments
                },
                ensure_ascii=False,
                sort_keys=True
            )

            if call_fingerprint in executed_calls:

                print(
                    "⚠️ [LOOP GUARD]: "
                    "Agent đang cố gọi lại đúng Tool "
                    "với cùng tham số."
                )

                observation_history.append(
                    {
                        "tool": tool_name,
                        "arguments": arguments,
                        "observation": {
                            "status": "DUPLICATE_CALL",
                            "message": (
                                "Tool này đã được gọi với "
                                "cùng tham số. Không gọi lại."
                            )
                        }
                    }
                )

                working_prompt = build_react_context(
                    user_query,
                    observation_history
                )

                continue

            executed_calls.add(
                call_fingerprint
            )

            # ------------------------------------------------------------------
            # ACTION → MCP SERVER
            # ------------------------------------------------------------------

            tool_start_time = time.time()

            mcp_result = mcp_server.call_tool(
                tool_name,
                arguments
            )

            tool_latency_ms = round(
                (time.time() - tool_start_time) * 1000,
                2
            )

            # ------------------------------------------------------------------
            # OBSERVATION
            # ------------------------------------------------------------------

            obs_data = mcp_result.get(
                "result",
                {}
            )

            print(
                "👁️ [Observation từ MCP Server]:"
            )

            print(
                json.dumps(
                    obs_data,
                    ensure_ascii=False,
                    indent=2
                )
            )

            # ------------------------------------------------------------------
            # Save Trace
            # ------------------------------------------------------------------

            trace_logs.append(
                {
                    "step": step,
                    "query": user_query,
                    "action_type": "TOOL_EXECUTION",
                    "thought": thought,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "observation": obs_data,
                    "llm_latency_ms": llm_latency_ms,
                    "tool_latency_ms": tool_latency_ms,
                    "latency_ms": round(
                        llm_latency_ms
                        + tool_latency_ms,
                        2
                    )
                }
            )

            # ------------------------------------------------------------------
            # Add Observation to Agent Context
            # ------------------------------------------------------------------

            observation_history.append(
                {
                    "step": step,
                    "tool": tool_name,
                    "arguments": arguments,
                    "observation": obs_data
                }
            )

            # ------------------------------------------------------------------
            # IMPORTANT:
            # KHÔNG break ở đây.
            #
            # Observation được đưa lại LLM để Agent có thể:
            #
            # search_papers
            #       ↓
            # observation
            #       ↓
            # create_research_plan
            #       ↓
            # observation
            #       ↓
            # final answer
            # ------------------------------------------------------------------

            working_prompt = build_react_context(
                user_query,
                observation_history
            )

            continue

        # ======================================================================
        # CASE 3 — UNKNOWN RESPONSE
        # ======================================================================

        else:

            error_message = (
                "Provider trả về response_type "
                f"không hợp lệ: {response_type}"
            )

            print(
                f"⚠️ {error_message}"
            )

            trace_logs.append(
                {
                    "step": step,
                    "query": user_query,
                    "action_type": "PROVIDER_ERROR",
                    "thought": thought,
                    "output": error_message,
                    "latency_ms": llm_latency_ms
                }
            )

            break

    # ==========================================================================
    # MAX ITERATIONS REACHED
    # ==========================================================================

    if not final_answer_generated:

        if step >= MAX_ITERATIONS:

            fallback_answer = (
                "Agent đã đạt giới hạn số vòng suy luận "
                "trước khi tạo được Final Answer."
            )

            print(
                f"\n⚠️ [MAX ITERATIONS]: "
                f"{fallback_answer}"
            )

            trace_logs.append(
                {
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "MAX_ITERATIONS_REACHED",
                    "output": fallback_answer
                }
            )

    return trace_logs


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":

    print(
        "=========================================================="
    )

    print(
        "🔬 AI RESEARCH ASSISTANT "
        "- DAY 03 REACT AGENT LAB"
    )

    print(
        "=========================================================="
    )

    provider = get_llm_provider()

    mcp_server = MCPAcademicServer()

    print(
        f"🔌 LLM Provider: "
        f"{provider.__class__.__name__}"
    )

    print(
        f"🌐 MCP Server: "
        f"{mcp_server.server_name}\n"
    )

    tests = load_test_cases()

    print(
        f"✅ Đã tải thành công "
        f"{len(tests)} Test Cases.\n"
    )

    # ==========================================================================
    # INTERACTIVE MODE
    # ==========================================================================

    if "--interactive" in sys.argv:

        print(
            "🎮 [INTERACTIVE MODE] "
            "AI Research Assistant"
        )

        print(
            "\n💡 Gợi ý:"
        )

        print(
            "   - Research gap là gì?"
        )

        print(
            "   - Hãy tìm paper về risky driving prediction."
        )

        print(
            "   - Hãy tạo research plan cho risky driving "
            "prediction với RTX 3090 24GB."
        )

        print(
            "   - Tìm paper về risky driving prediction, "
            "phân tích limitation và đề xuất gap khả thi."
        )

        print(
            "\n   Gõ 'exit' hoặc 'quit' để thoát.\n"
        )

        while True:

            try:

                user_input = input(
                    "👤 Researcher hỏi: "
                ).strip()

                if (
                    not user_input
                    or user_input.lower()
                    in ["exit", "quit"]
                ):

                    print(
                        "👋 Kết thúc phiên."
                    )

                    break

                logs = run_react_agent(
                    user_input,
                    provider,
                    mcp_server
                )

                save_waterfall_trace(
                    logs
                )

            except (
                KeyboardInterrupt,
                EOFError
            ):

                print(
                    "\n👋 Đã thoát phiên tương tác."
                )

                break

    # ==========================================================================
    # TEST SUITE
    # ==========================================================================

    elif "--all" in sys.argv:

        print(
            "🚀 [TEST SUITE MODE] "
            "Kiểm tra toàn bộ Test Cases:"
        )

        completed_count = 0

        todo_count = 0

        all_traces = []

        for tc in tests:

            print(
                "\n=================================================="
            )

            print(
                f"🧪 [{tc['id']}] "
                f"Loại test: {tc['type']} "
                f"(Độ phức tạp: {tc['complexity']})"
            )

            print(
                f"📌 Kỳ vọng: "
                f"{tc['expected_behavior']}"
            )

            question = tc.get(
                "question",
                ""
            ).strip()

            if question.startswith(
                "TODO"
            ):

                print(
                    "⏸️ [CHƯA KÍCH HOẠT - TODO]"
                )

                print(
                    f"   {question}"
                )

                todo_count += 1

            else:

                logs = run_react_agent(
                    question,
                    provider,
                    mcp_server
                )

                all_traces.extend(
                    logs
                )

                completed_count += 1

        print(
            "\n=================================================="
        )

        print(
            f"📊 [KẾT QUẢ TEST SUITE]: "
            f"Đã thực thi "
            f"{completed_count}/{len(tests)} Test Cases "
            f"| {todo_count} TODO"
        )

        if all_traces:

            save_waterfall_trace(
                all_traces
            )

        print(
            "💡 Interactive mode: "
            "python src/app.py --interactive"
        )

    # ==========================================================================
    # DEFAULT DEMO
    # ==========================================================================

    else:

        print(
            "ℹ️ HƯỚNG DẪN:"
        )

        print(
            "  1. Chat trực tiếp: "
            "python src/app.py --interactive"
        )

        print(
            "  2. Chạy toàn bộ Test Cases: "
            "python src/app.py --all\n"
        )

        sample_query = tests[1][
            "question"
        ]

        print(
            "--- 🏁 DEMO TC02: "
            "Paper Search ---"
        )

        logs = run_react_agent(
            sample_query,
            provider,
            mcp_server
        )

        save_waterfall_trace(
            logs
        )