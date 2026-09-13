"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng MCP Server cung cấp công cụ cho AI Research Assistant.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call


if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MCPAcademicServer:
    """
    Giả lập MCP Server tuân thủ chuẩn Model Context Protocol.

    Giữ tên class MCPAcademicServer để tương thích với src/app.py.
    """

    def __init__(self, server_name: str = "research-assistant-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách Tools công bố qua MCP."""
        return TOOLS_SCHEMA

    def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        [TASK 2.1]
        Thực thi Tool thông qua Tool Router và đóng gói
        phản hồi theo cấu trúc JSON-RPC 2.0.
        """

        try:
            # 1. Gọi Execution Layer
            result_json = dispatch_tool_call(
                tool_name,
                arguments
            )

            # 2. Chuyển JSON string -> Python dict
            content = json.loads(result_json)

            # 3. Đóng gói phản hồi MCP / JSON-RPC
            return {
                "jsonrpc": "2.0",
                "server": self.server_name,
                "tool": tool_name,
                "result": content
            }

        except json.JSONDecodeError as e:
            return {
                "jsonrpc": "2.0",
                "server": self.server_name,
                "tool": tool_name,
                "result": {
                    "status": "MCP_ERROR",
                    "error": f"Không thể parse Tool response: {str(e)}"
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "server": self.server_name,
                "tool": tool_name,
                "result": {
                    "status": "MCP_ERROR",
                    "error": str(e)
                }
            }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER — AI RESEARCH ASSISTANT")
    print("==========================================================")

    server = MCPAcademicServer()
    tools = server.list_tools()

    print(
        f"✅ Khởi tạo thành công MCP Server: "
        f"{server.server_name} (Version: {server.version})"
    )

    print(f"📦 Số lượng Tools công bố: {len(tools)}")

    print("\n📋 Tools:")
    for tool in tools:
        print(f"   - {tool.get('name')}")

    # ==============================================================
    # TEST TOOL SCHEMA
    # ==============================================================

    search_tool = next(
        (
            tool
            for tool in tools
            if tool.get("name") == "search_papers"
        ),
        None
    )

    plan_tool = next(
        (
            tool
            for tool in tools
            if tool.get("name") == "create_research_plan"
        ),
        None
    )

    if search_tool and plan_tool:
        print(
            "✅ [TASK 1.2]: "
            "Tool schemas 'search_papers' và "
            "'create_research_plan' đã được khai báo."
        )
    else:
        print(
            "❌ [TASK 1.2]: "
            "Thiếu Tool Schema cho Research Assistant."
        )

    # ==============================================================
    # TEST TASK 2.1 — MCP CALL
    # ==============================================================

    test_result = server.call_tool(
        "search_papers",
        {
            "query": "risky driving prediction",
            "max_results": 3
        }
    )

    if not test_result:
        print(
            "❌ [TASK 2.1]: "
            "Hàm call_tool() trả về kết quả rỗng."
        )

    else:
        print(
            "\n✅ [TASK 2.1]: "
            "Test dispatch Tool 'search_papers' thành công."
        )

        print(
            "📨 Phản hồi JSON-RPC:"
        )

        print(
            json.dumps(
                test_result,
                ensure_ascii=False,
                indent=2
            )
        )

    # ==============================================================
    # TEST EDGE CASE
    # ==============================================================

    edge_result = server.call_tool(
        "search_papers",
        {
            "query": "XYZ-Nonexistent-Research-Topic-99999"
        }
    )

    print(
        "\n🧪 Test NOT_FOUND:"
    )

    print(
        json.dumps(
            edge_result,
            ensure_ascii=False,
            indent=2
        )
    )