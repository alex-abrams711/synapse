#!/bin/bash
# UserPromptSubmit Hook - Active Tasks Management Rules
# Reminds agent of mandatory workflow requirements on every user prompt

echo ""
echo "ALWAYS, BEFORE STARTING WORK, set the tasks you have been asked to work on as Dev Status: [In Progress]."
echo "ALWAYS, BEFORE STARTING WORK, set active_tasks in config.json when starting work on tasks."
echo "ALWAYS run ALL quality checks before marking any task as verified."
echo "ALWAYS mark QA Status: [Passed] only if checks pass, [Failed - reason] if they fail."
echo "ALWAYS ask user 'Would you like me to fix the failed tasks?' before fixing failures."
echo "NEVER mark QA Status as [Passed] without actually running the quality checks."
echo "NEVER update User Verification (UV) fields unless instructed by the user."
echo ""
echo "If you understand, respond with \"Synapse workflow loaded...\""
echo ""
