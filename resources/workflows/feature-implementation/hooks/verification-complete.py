#!/usr/bin/env python3
import json
import sys

def main():
    print("🔍 Running task verifier completion hook...", file=sys.stderr)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    # Parse PostToolUse data
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Task tool calls
    if tool_name != "Task":
        print("Not a Task tool call - skipping.", file=sys.stderr)
        sys.exit(0)

    # Extract subagent_type from tool_input
    subagent_type = tool_input.get("subagent_type", "")

    # Only process verifier subagent
    if subagent_type != "verifier":
        print("Not a verifier completion - skipping.", file=sys.stderr)
        sys.exit(0)

    print("🔍 verifier completion detected - checking results...", file=sys.stderr)

    # Get the agent response from tool_response
    tool_response = input_data.get("tool_response", {})
    agent_response = tool_response.get("content", "")

    # Convert to string if it's a list of content blocks
    if isinstance(agent_response, list):
        agent_response = " ".join([
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in agent_response
        ])

    agent_response_lower = agent_response.lower()

    # Check verification result
    if "status: fail" in agent_response_lower:
        print("❌ Task verification FAILED", file=sys.stderr)
        output = {
            "decision": "block",
            "reason": "Task verification FAILED. Review the verification report and address all issues before proceeding. Re-run implementer to fix issues, then verifier again."
        }
        print(json.dumps(output))
        sys.exit(2)

    elif "status: pass" in agent_response_lower:
        # Allow successful verification to complete
        print("✅ Task verification PASSED - Implementation approved!", file=sys.stderr)
        print("🎉 Workflow complete - all quality gates passed", file=sys.stderr)
        sys.exit(0)

    else:
        # If no clear status, look for other indicators
        has_failures = ("fail" in agent_response_lower and
                       ("critical" in agent_response_lower or
                        "error" in agent_response_lower or
                        "issue" in agent_response_lower))

        if has_failures:
            print("❌ Task verification found issues", file=sys.stderr)
            output = {
                "decision": "block",
                "reason": "Task verification found issues. Review the verification report, present to user, and ask for next steps."
            }
            print(json.dumps(output))
            sys.exit(2)

if __name__ == "__main__":
    main()