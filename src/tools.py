"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Tool Schemas + Execution Layer cho AI Research Assistant.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. TOOL SCHEMAS — TASK 1.2
# ==============================================================================

TOOLS_SCHEMA = [
    {
        "name": "search_papers",
        "description": (
            "Tìm kiếm các research paper liên quan đến một chủ đề nghiên cứu. "
            "Kết quả bao gồm title, year, method và limitation để hỗ trợ "
            "literature review và research gap discovery."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Chủ đề hoặc từ khóa nghiên cứu cần tìm, "
                        "ví dụ: 'risky driving prediction'."
                    )
                },
                "max_results": {
                    "type": "integer",
                    "description": "Số lượng paper tối đa cần trả về.",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },

    {
        "name": "create_research_plan",
        "description": (
            "Tạo research plan khả thi dựa trên research topic, "
            "research gap và giới hạn tài nguyên của người dùng."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "research_topic": {
                    "type": "string",
                    "description": "Chủ đề nghiên cứu chính."
                },
                "resource_constraint": {
                    "type": "string",
                    "description": (
                        "Giới hạn tài nguyên, ví dụ: "
                        "'Single RTX 3090 24GB'."
                    )
                },
                "research_gap": {
                    "type": "string",
                    "description": (
                        "Research gap đã xác định sau literature review. "
                        "Có thể bỏ trống nếu người dùng chưa xác định gap."
                    )
                }
            },
            "required": [
                "research_topic",
                "resource_constraint"
            ]
        }
    }
]

# ==============================================================================
# 2. MOCK RESEARCH DATABASE
# ==============================================================================

MOCK_DATABASE = {
    "risky driving prediction": [
        {
            "paper_id": "P001",
            "title": "Risk-aware Driving Behavior Prediction with Temporal Modeling",
            "year": 2024,
            "method": "Transformer-based temporal modeling",
            "limitation": (
                "Evaluation is mainly conducted under normal weather "
                "and daytime driving conditions."
            )
        },
        {
            "paper_id": "P002",
            "title": "Interaction-aware Risk Prediction for Autonomous Driving",
            "year": 2025,
            "method": "Graph-based interaction modeling",
            "limitation": (
                "High computational cost and limited evaluation "
                "on resource-constrained hardware."
            )
        },
        {
            "paper_id": "P003",
            "title": "Future-aware Risky Agent Detection in Driving Scenes",
            "year": 2025,
            "method": "Future trajectory prediction + risk scoring",
            "limitation": (
                "Limited robustness analysis under rain, fog "
                "and low-light conditions."
            )
        },
        {
            "paper_id": "P004",
            "title": "Multimodal Driving Risk Assessment from Video",
            "year": 2024,
            "method": "Vision-language multimodal model",
            "limitation": (
                "Requires significant GPU resources and "
                "large-scale multimodal training data."
            )
        },
        {
            "paper_id": "P005",
            "title": "Real-time Traffic Risk Prediction from Dashcam Video",
            "year": 2023,
            "method": "CNN + temporal attention",
            "limitation": (
                "Real-time performance is evaluated on a limited "
                "number of traffic scenarios."
            )
        }
    ]
}


# ==============================================================================
# 3. TOOL EXECUTION FUNCTIONS
# ==============================================================================

def execute_search_papers(query: str, max_results: int = 5) -> str:
    """
    Tìm paper trong mock research database.
    """

    normalized_query = query.strip().lower()

    # Simple keyword matching cho Lab
    matched_papers = []

    for topic, papers in MOCK_DATABASE.items():
        if (
            normalized_query in topic
            or topic in normalized_query
            or (
                "risky" in normalized_query
                and "driving" in normalized_query
            )
        ):
            matched_papers.extend(papers)

    if not matched_papers:
        return json.dumps(
            {
                "status": "NOT_FOUND",
                "query": query,
                "message": (
                    f"Không tìm thấy paper phù hợp với chủ đề '{query}'. "
                    "Không đủ evidence để xác định research gap."
                )
            },
            ensure_ascii=False
        )

    results = matched_papers[:max_results]

    return json.dumps(
        {
            "status": "SUCCESS",
            "query": query,
            "papers_found": len(results),
            "papers": results
        },
        ensure_ascii=False
    )


def execute_create_research_plan(
    research_topic: str,
    resource_constraint: str,
    research_gap: str = ""
) -> str:
    """
    Tạo research plan dựa trên topic, gap và resource constraints.
    """

    if not research_gap:
        research_gap = (
            "Gap chưa được xác định rõ. "
            "Nên thực hiện literature review trước khi chốt contribution."
        )

    plan = {
        "research_topic": research_topic,
        "research_gap": research_gap,
        "resource_constraint": resource_constraint,
        "recommended_direction": (
            "Thiết kế một baseline có thể reproduce được trước, "
            "sau đó đánh giá limitation trên một benchmark phù hợp "
            "và phát triển cải tiến tập trung vào research gap đã chọn."
        ),
        "steps": [
            "1. Xác định baseline và benchmark phù hợp.",
            "2. Reproduce hoặc chạy checkpoint của baseline.",
            "3. Phân tích failure cases và limitation.",
            "4. Thiết kế một cải tiến tập trung vào research gap.",
            "5. Thực hiện ablation và benchmark.",
            "6. Đánh giá accuracy, robustness và computational cost."
        ],
        "feasibility": (
            f"Kế hoạch được thiết kế với giới hạn tài nguyên: "
            f"{resource_constraint}."
        )
    }

    return json.dumps(
        {
            "status": "SUCCESS",
            "plan": plan,
            "message": "Đã tạo research plan thành công."
        },
        ensure_ascii=False
    )


# ==============================================================================
# 4. TOOL ROUTER
# ==============================================================================

TOOL_ROUTER = {
    "search_papers": execute_search_papers,
    "create_research_plan": execute_create_research_plan
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Trung chuyển yêu cầu Tool từ MCP Server sang Execution Layer.
    """

    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)

        except Exception as e:
            return json.dumps(
                {
                    "status": "EXECUTION_ERROR",
                    "error": str(e)
                },
                ensure_ascii=False
            )

    return json.dumps(
        {
            "status": "UNKNOWN_TOOL",
            "error": f"Tool '{tool_name}' không tồn tại!"
        },
        ensure_ascii=False
    )