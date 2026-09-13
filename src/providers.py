"""
🔌 MULTI-PROVIDER LLM ADAPTER
Google Gemini, OpenAI & Offline Mock

Hỗ trợ:
- Text generation
- Native Tool Calling
- ReAct Research Agent
"""

import os
import sys
import json
from typing import Dict, Any, List

from dotenv import load_dotenv


# ==============================================================================
# ENVIRONMENT
# ==============================================================================

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()


# ==============================================================================
# BASE PROVIDER
# ==============================================================================

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider."""

    def generate(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        raise NotImplementedError


# ==============================================================================
# MOCK OFFLINE PROVIDER
# ==============================================================================

class MockOfflineProvider(BaseLLMProvider):
    """
    Offline Mock Provider.

    Hỗ trợ test:
    - Direct Answer
    - search_papers
    - create_research_plan
    - Multi-step ReAct
    - NOT_FOUND
    """

    def __init__(self):
        self.model_name = "Offline-Mock-Research-Agent-2026"

    # --------------------------------------------------------------------------
    # BASELINE CHATBOT
    # --------------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:

        prompt_lower = prompt.lower()

        if "research gap" in prompt_lower:
            return (
                "[Mock Chatbot Response]: "
                "Research gap là khoảng trống trong tri thức, phương pháp, "
                "dữ liệu hoặc bằng chứng nghiên cứu mà các công trình trước "
                "chưa giải quyết đầy đủ. Việc xác định gap giúp researcher "
                "xây dựng câu hỏi nghiên cứu và contribution có cơ sở."
            )

        return (
            "[Mock Chatbot Response]: "
            "Tôi có thể hỗ trợ giải thích các khái niệm nghiên cứu chung, "
            "nhưng Chatbot Baseline không có Tool để tìm paper hoặc "
            "truy cập dữ liệu bên ngoài."
        )

    # --------------------------------------------------------------------------
    # HELPER: ORIGINAL USER REQUEST
    # --------------------------------------------------------------------------

    @staticmethod
    def _extract_original_request(prompt: str) -> str:
        """
        Lấy riêng yêu cầu ban đầu của user.

        Mục đích:
        tránh keyword bên trong Observation làm Agent hiểu sai intent.

        Ví dụ:
        TC02 chỉ yêu cầu tìm paper, nhưng Observation chứa chữ
        'limitation' thì không được tự suy ra user muốn research plan.
        """

        prompt_lower = prompt.lower()

        marker_query = "yêu cầu ban đầu của người dùng:"
        marker_observation = "các action / observation đã thực hiện:"

        if marker_query in prompt_lower:
            original_request = prompt_lower.split(
                marker_query,
                1
            )[1]

            if marker_observation in original_request:
                original_request = original_request.split(
                    marker_observation,
                    1
                )[0]

            return original_request.strip()

        return prompt_lower.strip()

    # --------------------------------------------------------------------------
    # HELPER: CHECK PRIOR TOOL EXECUTION
    # --------------------------------------------------------------------------

    @staticmethod
    def _tool_already_executed(
        prompt: str,
        tool_name: str
    ) -> bool:

        return (
            f'"tool": "{tool_name}"' in prompt
            or f"'tool': '{tool_name}'" in prompt
        )

    # --------------------------------------------------------------------------
    # REACT AGENT MOCK
    # --------------------------------------------------------------------------

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:

        prompt_lower = prompt.lower()

        original_request = self._extract_original_request(
            prompt
        )

        search_done = self._tool_already_executed(
            prompt,
            "search_papers"
        )

        plan_done = self._tool_already_executed(
            prompt,
            "create_research_plan"
        )

        # ======================================================================
        # CASE 1 — NOT_FOUND
        # ======================================================================

        if '"status": "NOT_FOUND"' in prompt:

            return {
                "type": "text",
                "content": (
                    "[Mock Agent Final Answer]: "
                    "Không tìm thấy đủ paper hoặc evidence cho chủ đề "
                    "được yêu cầu. Vì vậy chưa thể xác định research gap "
                    "đáng tin cậy. Nên mở rộng hoặc điều chỉnh từ khóa "
                    "tìm kiếm trước."
                ),
                "thought": (
                    "Tool trả về NOT_FOUND nên không được tự bịa "
                    "paper hoặc research gap."
                )
            }

        # ======================================================================
        # CASE 2 — AFTER create_research_plan
        # ======================================================================

        if plan_done:

            # TC04:
            # search_papers -> create_research_plan -> final
            if search_done:

                return {
                    "type": "text",
                    "content": (
                        "[Mock Agent Final Answer]: "
                        "Đã phân tích literature và tạo research plan dựa "
                        "trên potential research gap cùng resource constraints. "
                        "Một hướng khả thi là đánh giá robustness của risky "
                        "driving prediction dưới điều kiện mưa, sương mù "
                        "và thiếu sáng, ưu tiên reproduce baseline hoặc "
                        "fine-tuning để phù hợp GPU RTX 3090 24GB."
                    ),
                    "thought": (
                        "Đã có kết quả từ search_papers và "
                        "create_research_plan nên đủ thông tin để trả lời."
                    )
                }

            # TC03:
            # create_research_plan -> final
            return {
                "type": "text",
                "content": (
                    "[Mock Agent Final Answer]: "
                    "Đã tạo research plan dựa trên research topic và "
                    "resource constraints. Research gap hiện chưa được "
                    "xác nhận từ literature review, vì vậy nên tìm và "
                    "phân tích paper trước khi chốt contribution."
                ),
                "thought": (
                    "Đã nhận kết quả từ create_research_plan. "
                    "Không có bước literature search trước đó nên không "
                    "khẳng định research gap đã được xác nhận."
                )
            }

        # ======================================================================
        # CASE 3 — AFTER search_papers
        # ======================================================================

        if search_done:

            # IMPORTANT:
            # chỉ dựa vào ORIGINAL USER REQUEST,
            # không dựa vào toàn bộ prompt/Observation.
            needs_research_plan = any(
                keyword in original_request
                for keyword in [
                    "research gap",
                    "đề xuất",
                    "phân tích limitation",
                    "research plan",
                    "kế hoạch nghiên cứu",
                    "khả thi",
                    "resource constraint",
                    "gpu",
                    "3090"
                ]
            )

            # ------------------------------------------------------------------
            # TC04 — MULTI-STEP
            # search_papers -> create_research_plan
            # ------------------------------------------------------------------

            if needs_research_plan:

                return {
                    "type": "tool_call",
                    "tool_name": "create_research_plan",
                    "arguments": {
                        "research_topic": "risky driving prediction",
                        "research_gap": (
                            "Limited robustness evaluation under adverse "
                            "weather and low-light driving conditions."
                        ),
                        "resource_constraint": "Single RTX 3090 24GB"
                    },
                    "thought": (
                        "Paper search đã hoàn tất và yêu cầu ban đầu "
                        "còn yêu cầu phân tích gap/feasibility. "
                        "Bước tiếp theo là tạo research plan."
                    )
                }

            # ------------------------------------------------------------------
            # TC02 — SINGLE TOOL
            # search_papers -> final
            # ------------------------------------------------------------------

            return {
                "type": "text",
                "content": (
                    "[Mock Agent Final Answer]: "
                    "Đã tìm thấy các paper liên quan đến risky driving "
                    "prediction. Các hướng chính gồm temporal modeling, "
                    "interaction-aware prediction, future trajectory modeling "
                    "và multimodal risk assessment."
                ),
                "thought": (
                    "Yêu cầu ban đầu chỉ yêu cầu tìm literature. "
                    "Kết quả search_papers đã đủ để trả lời."
                )
            }

        # ======================================================================
        # CASE 4 — DIRECT RESEARCH PLAN REQUEST
        # ======================================================================

        plan_keywords = [
            "tạo một research plan",
            "tạo research plan",
            "create research plan",
            "kế hoạch nghiên cứu"
        ]

        if any(
            keyword in original_request
            for keyword in plan_keywords
        ):

            resource_constraint = (
                "Single RTX 3090 24GB"
                if "3090" in original_request
                else "Limited compute resources"
            )

            return {
                "type": "tool_call",
                "tool_name": "create_research_plan",
                "arguments": {
                    "research_topic": "risky driving prediction",
                    "resource_constraint": resource_constraint
                },
                "thought": (
                    "Người dùng đã yêu cầu tạo research plan và "
                    "đã cung cấp research topic/resource constraints."
                )
            }

        # ======================================================================
        # CASE 5 — PAPER SEARCH REQUEST
        # ======================================================================

        search_keywords = [
            "tìm paper",
            "tìm các paper",
            "paper liên quan",
            "search paper",
            "literature",
            "nghiên cứu liên quan"
        ]

        if any(
            keyword in original_request
            for keyword in search_keywords
        ):

            if (
                "xyz-nonexistent-research-topic-99999"
                in original_request
            ):
                query = "XYZ-Nonexistent-Research-Topic-99999"

            else:
                query = "risky driving prediction"

            return {
                "type": "tool_call",
                "tool_name": "search_papers",
                "arguments": {
                    "query": query,
                    "max_results": 5
                },
                "thought": (
                    "Người dùng yêu cầu tìm literature nên cần gọi "
                    "search_papers trước."
                )
            }

        # ======================================================================
        # CASE 6 — DIRECT ANSWER
        # ======================================================================

        if "research gap" in original_request:

            return {
                "type": "text",
                "content": (
                    "[Mock Agent Response]: "
                    "Research gap là khoảng trống trong tri thức, phương pháp, "
                    "dữ liệu hoặc bằng chứng mà các nghiên cứu hiện tại "
                    "chưa giải quyết đầy đủ. Xác định gap giúp researcher "
                    "xây dựng câu hỏi nghiên cứu và contribution có cơ sở."
                ),
                "thought": (
                    "Đây là câu hỏi kiến thức nghiên cứu chung "
                    "nên không cần Tool."
                )
            }

        # ======================================================================
        # FALLBACK
        # ======================================================================

        return {
            "type": "text",
            "content": (
                "[Mock Agent Response]: "
                "Tôi là AI Research Assistant. Tôi có thể hỗ trợ "
                "literature search, research gap discovery và "
                "research planning."
            ),
            "thought": (
                "Không phát hiện yêu cầu cần sử dụng Tool."
            )
        }


# ==============================================================================
# GEMINI PROVIDER
# ==============================================================================

class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider với Native Tool Calling."""

    def __init__(
        self,
        api_key: str = None,
        model: str = None
    ):

        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )

        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "gemini-2.5-flash"
        )

    # --------------------------------------------------------------------------
    # TEXT GENERATION
    # --------------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:

        if (
            not self.api_key
            or self.api_key
            == "your_gemini_api_key_here"
        ):
            return (
                "[Gemini Error]: "
                "Chưa cấu hình GEMINI_API_KEY."
            )

        try:

            from google import genai

            client = genai.Client(
                api_key=self.api_key
            )

            contents = (
                f"{system_prompt}\n\n{prompt}"
                if system_prompt
                else prompt
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )

            return response.text or ""

        except Exception as e:

            return (
                f"[Gemini Exception]: {str(e)}"
            )

    # --------------------------------------------------------------------------
    # TOOL CALLING
    # --------------------------------------------------------------------------

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:

        if (
            not self.api_key
            or self.api_key
            == "your_gemini_api_key_here"
        ):

            print(
                "ℹ️ [Gemini Provider]: "
                "Không có GEMINI_API_KEY hợp lệ. "
                "Fallback sang Mock Offline."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )

        try:

            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=self.api_key
            )

            # ------------------------------------------------------------------
            # Tool Schema -> Gemini Functions
            # ------------------------------------------------------------------

            function_declarations = []

            for tool in tools_schema:

                if (
                    not tool.get("name")
                    or not tool.get("parameters")
                ):
                    continue

                function_declarations.append(
                    {
                        "name": tool["name"],
                        "description": tool.get(
                            "description",
                            ""
                        ),
                        "parameters": tool.get(
                            "parameters",
                            {}
                        )
                    }
                )

            config = types.GenerateContentConfig(
                system_instruction=(
                    system_prompt
                    if system_prompt
                    else None
                ),
                tools=[
                    {
                        "function_declarations":
                        function_declarations
                    }
                ]
                if function_declarations
                else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # ------------------------------------------------------------------
            # Tool Call
            # ------------------------------------------------------------------

            if response.function_calls:

                call = response.function_calls[0]

                args = (
                    dict(call.args)
                    if hasattr(call, "args")
                    and call.args
                    else {}
                )

                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": (
                        f"Gemini chọn Tool '{call.name}' "
                        f"với arguments "
                        f"{json.dumps(args, ensure_ascii=False)}"
                    )
                }

            # ------------------------------------------------------------------
            # Final Text
            # ------------------------------------------------------------------

            return {
                "type": "text",
                "content": response.text or "",
                "thought": (
                    "Gemini xác định không cần gọi thêm Tool."
                )
            }

        except Exception as e:

            print(
                "⚠️ [Gemini API Warning]: "
                f"{str(e)}"
            )

            print(
                "↪️ Fallback sang Mock Offline."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )


# ==============================================================================
# OPENAI PROVIDER
# ==============================================================================

class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider với Native Tool Calling."""

    def __init__(
        self,
        api_key: str = None,
        model: str = None
    ):

        self.api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
        )

        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "gpt-4o-mini"
        )

    # --------------------------------------------------------------------------
    # TEXT GENERATION
    # --------------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:

        if (
            not self.api_key
            or self.api_key
            == "your_openai_api_key_here"
        ):
            return (
                "[OpenAI Error]: "
                "Chưa cấu hình OPENAI_API_KEY."
            )

        try:

            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key
            )

            messages = []

            if system_prompt:
                messages.append(
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": prompt
                }
            )

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )

            return (
                response
                .choices[0]
                .message
                .content
                or ""
            )

        except Exception as e:

            return (
                f"[OpenAI Exception]: {str(e)}"
            )

    # --------------------------------------------------------------------------
    # TOOL CALLING
    # --------------------------------------------------------------------------

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:

        if (
            not self.api_key
            or self.api_key
            == "your_openai_api_key_here"
        ):

            print(
                "ℹ️ [OpenAI Provider]: "
                "Không có OPENAI_API_KEY hợp lệ. "
                "Fallback sang Mock Offline."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )

        try:

            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key
            )

            # ------------------------------------------------------------------
            # Tool Schema -> OpenAI Tools
            # ------------------------------------------------------------------

            tools = []

            for tool in tools_schema:

                if not tool.get("name"):
                    continue

                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool.get(
                                "description",
                                ""
                            ),
                            "parameters": tool.get(
                                "parameters",
                                {}
                            )
                        }
                    }
                )

            messages = []

            if system_prompt:
                messages.append(
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": prompt
                }
            )

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=(
                    tools
                    if tools
                    else None
                ),
                tool_choice=(
                    "auto"
                    if tools
                    else None
                )
            )

            msg = response.choices[0].message

            # ------------------------------------------------------------------
            # Tool Call
            # ------------------------------------------------------------------

            if msg.tool_calls:

                call = msg.tool_calls[0]

                args = (
                    json.loads(
                        call.function.arguments
                    )
                    if call.function.arguments
                    else {}
                )

                return {
                    "type": "tool_call",
                    "tool_name": (
                        call.function.name
                    ),
                    "arguments": args,
                    "thought": (
                        f"OpenAI chọn Tool "
                        f"'{call.function.name}' "
                        f"với arguments "
                        f"{json.dumps(args, ensure_ascii=False)}"
                    )
                }

            # ------------------------------------------------------------------
            # Final Text
            # ------------------------------------------------------------------

            return {
                "type": "text",
                "content": msg.content or "",
                "thought": (
                    "OpenAI xác định không cần gọi thêm Tool."
                )
            }

        except Exception as e:

            print(
                "⚠️ [OpenAI API Warning]: "
                f"{str(e)}"
            )

            print(
                "↪️ Fallback sang Mock Offline."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )


# ==============================================================================
# PROVIDER FACTORY
# ==============================================================================

def get_llm_provider() -> BaseLLMProvider:
    """
    Chọn provider theo biến môi trường:

    LLM_PROVIDER=gemini
    LLM_PROVIDER=openai
    LLM_PROVIDER=mock
    """

    provider_type = os.getenv(
        "LLM_PROVIDER",
        "gemini"
    ).strip().lower()

    # --------------------------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------------------------

    if provider_type == "gemini":

        key = os.getenv(
            "GEMINI_API_KEY"
        )

        if (
            key
            and key
            != "your_gemini_api_key_here"
        ):
            return GeminiProvider()

        print(
            "ℹ️ GEMINI_API_KEY chưa được cấu hình. "
            "Dùng MockOfflineProvider."
        )

        return MockOfflineProvider()

    # --------------------------------------------------------------------------
    # OPENAI
    # --------------------------------------------------------------------------

    if provider_type == "openai":

        key = os.getenv(
            "OPENAI_API_KEY"
        )

        if (
            key
            and key
            != "your_openai_api_key_here"
        ):
            return OpenAIProvider()

        print(
            "ℹ️ OPENAI_API_KEY chưa được cấu hình. "
            "Dùng MockOfflineProvider."
        )

        return MockOfflineProvider()

    # --------------------------------------------------------------------------
    # MOCK
    # --------------------------------------------------------------------------

    if provider_type == "mock":
        return MockOfflineProvider()

    # --------------------------------------------------------------------------
    # UNKNOWN PROVIDER
    # --------------------------------------------------------------------------

    print(
        f"⚠️ LLM_PROVIDER='{provider_type}' không hợp lệ. "
        "Dùng MockOfflineProvider."
    )

    return MockOfflineProvider()