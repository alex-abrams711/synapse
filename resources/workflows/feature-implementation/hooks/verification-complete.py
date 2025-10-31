#!/usr/bin/env python3
"""Verification completion hook - validates QA Status was updated

This hook runs after the verifier sub-agent completes. It:
1. Parses the verifier's response to determine PASS/FAIL verdict
2. Parses the tasks file to check QA Status field was updated
3. Validates the QA Status matches the verdict (both checkbox and value)
4. Blocks with explicit re-invocation instructions if verification failed
"""
import json
import sys

# Import shared task parsing utilities
import task_parser
from task_parser import Task

def determine_verification_result(agent_response: str) -> str:
    """Extract PASS/FAIL verdict from verifier's response

    Args:
        agent_response: The verifier agent's full response text

    Returns:
        "PASS", "FAIL", or None if unclear
    """
    agent_response_lower = agent_response.lower()

    # Check for explicit status declarations
    if "status: pass" in agent_response_lower:
        return "PASS"
    elif "status: fail" in agent_response_lower:
        return "FAIL"

    # Fallback: look for failure indicators
    has_failures = ("fail" in agent_response_lower and
                   ("critical" in agent_response_lower or
                    "error" in agent_response_lower or
                    "issue" in agent_response_lower))

    if has_failures:
        return "FAIL"

    return None

def validate_qa_status_for_pass(task: Task, agent_response: str) -> tuple:
    """Validate QA Status is correct for PASS verdict

    Args:
        task: The task that was verified
        agent_response: Full verifier response for context

    Returns:
        Tuple of (is_valid, error_message)
    """
    expected_statuses = ["Complete", "complete", "Passed", "passed", "Done", "done"]

    # Check both status value AND checkbox
    status_correct = task.qa_status in expected_statuses
    checkbox_checked = task.qa_status_checked

    if status_correct and checkbox_checked:
        print(f"✅ QA Status correctly updated to '{task.qa_status}' with checkbox checked", file=sys.stderr)
        return True, ""
    elif not status_correct and not checkbox_checked:
        error = f"""Verifier reported PASS but QA Status not properly updated.

Current QA Status: [{task.qa_status}] (checkbox: {'☑' if checkbox_checked else '☐'})
Expected: [Complete] with checkbox checked [x]
Task: {task.task_id} at line {task.line_number}

REQUIRED ACTION: Re-invoke the "verifier" sub-agent with these instructions:
- Review your verification and confirm it passed
- Update the task's QA Status field to [Complete] in the tasks file
- Check the checkbox on the QA Status line (change [ ] to [x])
- The QA Status field is at line {task.qa_status_line_number or 'near ' + str(task.line_number)}
- Both the status value AND checkbox must be updated"""
        return False, error
    elif not status_correct:
        error = f"""Verifier checked the QA Status checkbox but didn't update status value correctly.

Current QA Status: [{task.qa_status}] (checkbox: ☑)
Expected: [Complete] (checkbox: ☑)
Task: {task.task_id} at line {task.line_number}

REQUIRED ACTION: Re-invoke the "verifier" sub-agent with these instructions:
- Update the QA Status value to [Complete]
- The checkbox is already checked, just fix the status value
- Line {task.qa_status_line_number or task.line_number}"""
        return False, error
    else:  # status correct but checkbox not checked
        error = f"""Verifier updated QA Status value but forgot to check the checkbox.

Current QA Status: [{task.qa_status}] (checkbox: ☐)
Expected: [{task.qa_status}] (checkbox: ☑)
Task: {task.task_id} at line {task.line_number}

REQUIRED ACTION: Re-invoke the "verifier" sub-agent with these instructions:
- The status value is correct, but you must check the checkbox
- Change the [ ] to [x] on line {task.qa_status_line_number or task.line_number}
- This marks the QA step as visually complete"""
        return False, error

def validate_qa_status_for_fail(task: Task, agent_response: str) -> tuple:
    """Validate QA Status is correct for FAIL verdict

    Args:
        task: The task that was verified
        agent_response: Full verifier response for error details

    Returns:
        Tuple of (is_valid, error_message)
    """
    expected_statuses = ["Failed", "failed", "In Progress", "in progress", "Needs Work", "needs work"]

    # Check both status value AND checkbox
    status_correct = task.qa_status in expected_statuses
    checkbox_checked = task.qa_status_checked

    if status_correct and checkbox_checked:
        print(f"✅ QA Status correctly updated to '{task.qa_status}' with checkbox checked", file=sys.stderr)
        print("❌ Verification found issues - need implementer to fix", file=sys.stderr)

        # Extract failure context (first 1000 chars of response)
        response_excerpt = agent_response[:1000]
        if len(agent_response) > 1000:
            response_excerpt += "..."

        error = f"""Verification FAILED - issues found during QA.

QA Status: [{task.qa_status}] (checkbox: ☑)
Task: {task.task_id}

REQUIRED ACTION: Re-invoke the "implementer" sub-agent to fix these issues:
- Review the verification report below for specific failures
- Provide the implementer with detailed error information
- Do NOT make fixes yourself - the implementer must do this work
- After implementer completes, re-invoke the verifier to confirm fixes

VERIFICATION REPORT EXCERPT:
{response_excerpt}"""
        return False, error
    elif not status_correct and not checkbox_checked:
        error = f"""Verifier reported FAIL but QA Status not updated.

Current QA Status: [{task.qa_status}] (checkbox: ☐)
Expected: [Failed] with checkbox checked [x]
Task: {task.task_id} at line {task.line_number}

REQUIRED ACTION: Re-invoke the "verifier" sub-agent with these instructions:
- Review your verification and document all failures
- Update the task's QA Status field to [Failed] in the tasks file
- Check the checkbox on the QA Status line (change [ ] to [x])
- The QA Status field is at line {task.qa_status_line_number or 'near ' + str(task.line_number)}
- List all specific issues that need fixing in your report"""
        return False, error
    elif not status_correct:
        error = f"""Verifier checked the QA Status checkbox but didn't update status value correctly.

Current QA Status: [{task.qa_status}] (checkbox: ☑)
Expected: [Failed] (checkbox: ☑)
Task: {task.task_id}

REQUIRED ACTION: Re-invoke the "verifier" sub-agent with these instructions:
- Update the QA Status value to [Failed]
- The checkbox is already checked, just fix the status value
- Line {task.qa_status_line_number or task.line_number}
- Document all issues found during verification"""
        return False, error
    else:  # status correct but checkbox not checked
        error = f"""Verifier updated QA Status value but forgot to check the checkbox.

Current QA Status: [{task.qa_status}] (checkbox: ☐)
Expected: [{task.qa_status}] (checkbox: ☑)
Task: {task.task_id}

REQUIRED ACTION: Re-invoke the "verifier" sub-agent with these instructions:
- The status value is correct, but you must check the checkbox
- Change the [ ] to [x] on line {task.qa_status_line_number or task.line_number}
- This marks that QA verification was performed (even though it failed)"""
        return False, error

def main():
    print("🔍 Running verifier completion hook...", file=sys.stderr)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    # Only process Task tool calls
    if input_data.get("tool_name") != "Task":
        print("Not a Task tool call - skipping.", file=sys.stderr)
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})

    # Only process verifier subagent
    if tool_input.get("subagent_type") != "verifier":
        print("Not a verifier completion - skipping.", file=sys.stderr)
        sys.exit(0)

    print("🔍 Verifier completion detected - validating QA Status update...", file=sys.stderr)

    # Get the agent response
    tool_response = input_data.get("tool_response", {})
    agent_response = tool_response.get("content", "")

    # Convert to string if it's a list of content blocks
    if isinstance(agent_response, list):
        agent_response = " ".join([
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in agent_response
        ])

    # Determine verification result from response
    verification_result = determine_verification_result(agent_response)

    if not verification_result:
        print("⚠️ Could not determine verification result (no clear PASS/FAIL)", file=sys.stderr)
        output = {
            "decision": "block",
            "reason": """Verifier did not provide clear PASS/FAIL verdict.

REQUIRED ACTION: Re-invoke the "verifier" sub-agent with these instructions:
- Review the implementation thoroughly
- Provide a clear STATUS: PASS or STATUS: FAIL in your final report
- Update the task's QA Status field in the tasks file to match your verdict
- If FAIL, list all issues that need fixing"""
        }
        print(json.dumps(output))
        sys.exit(2)

    print(f"📋 Verification result: {verification_result}", file=sys.stderr)

    # Load config and find tasks file
    config = task_parser.load_synapse_config()
    if not config:
        # No task management system - just check response
        print("ℹ️ No task management system - relying on verifier response only", file=sys.stderr)

        if verification_result == "FAIL":
            output = {
                "decision": "block",
                "reason": """Verification FAILED.

REQUIRED ACTION: Re-invoke the "implementer" sub-agent to fix the issues:
- Review the verification report above
- Provide specific error details to the implementer
- Do NOT make fixes yourself - the implementer must do this work
- After implementer completes, re-invoke verifier to confirm fixes"""
            }
            print(json.dumps(output))
            sys.exit(2)
        else:
            print("✅ Verification PASSED", file=sys.stderr)
            sys.exit(0)

    # Find active tasks file
    tasks_file_path = task_parser.find_active_tasks_file(config)
    if not tasks_file_path:
        print("ℹ️ No active tasks file - relying on verifier response only", file=sys.stderr)
        # Use same fallback logic as above
        if verification_result == "FAIL":
            output = {
                "decision": "block",
                "reason": """Verification FAILED.

REQUIRED ACTION: Re-invoke the "implementer" sub-agent to fix the issues:
- Review the verification report above
- Provide specific error details to the implementer
- Do NOT make fixes yourself - the implementer must do this work
- After implementer completes, re-invoke verifier to confirm fixes"""
            }
            print(json.dumps(output))
            sys.exit(2)
        else:
            print("✅ Verification PASSED", file=sys.stderr)
            sys.exit(0)

    # Parse tasks from file with schema-aware normalization
    parsed_tasks = task_parser.parse_tasks_with_structure(tasks_file_path, config)
    if not parsed_tasks:
        print("⚠️ No tasks found in file", file=sys.stderr)
        # Use same fallback
        if verification_result == "FAIL":
            output = {
                "decision": "block",
                "reason": """Verification FAILED.

REQUIRED ACTION: Re-invoke the "implementer" sub-agent to fix the issues:
- Review the verification report above
- Provide specific error details to the implementer
- Do NOT make fixes yourself - the implementer must do this work
- After implementer completes, re-invoke verifier to confirm fixes"""
            }
            print(json.dumps(output))
            sys.exit(2)
        else:
            print("✅ Verification PASSED", file=sys.stderr)
            sys.exit(0)

    # Find which task was being verified
    prompt = tool_input.get("prompt", "")
    target_task = task_parser.find_matching_task(prompt, parsed_tasks)

    if not target_task:
        print("⚠️ Could not identify which task was verified", file=sys.stderr)
        # Use same fallback
        if verification_result == "FAIL":
            output = {
                "decision": "block",
                "reason": """Verification FAILED.

REQUIRED ACTION: Re-invoke the "implementer" sub-agent to fix the issues:
- Review the verification report above
- Provide specific error details to the implementer
- Do NOT make fixes yourself - the implementer must do this work
- After implementer completes, re-invoke verifier to confirm fixes"""
            }
            print(json.dumps(output))
            sys.exit(2)
        else:
            print("✅ Verification PASSED", file=sys.stderr)
            sys.exit(0)

    print(f"📝 Checking QA Status for task: {target_task.task_id}", file=sys.stderr)
    print(f"   Current QA Status: {target_task.qa_status}", file=sys.stderr)

    # Validate QA Status was updated correctly
    if verification_result == "PASS":
        is_valid, error_message = validate_qa_status_for_pass(target_task, agent_response)
        if is_valid:
            print("🎉 Verification complete - implementation approved!", file=sys.stderr)
            sys.exit(0)
        else:
            output = {"decision": "block", "reason": error_message}
            print(json.dumps(output))
            sys.exit(2)

    else:  # verification_result == "FAIL"
        is_valid, error_message = validate_qa_status_for_fail(target_task, agent_response)
        # Note: is_valid will be False in both cases (updated or not updated)
        # because we need to block and have implementer fix the issues
        output = {"decision": "block", "reason": error_message}
        print(json.dumps(output))
        sys.exit(2)

if __name__ == "__main__":
    main()
