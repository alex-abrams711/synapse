#!/bin/bash
# UserPromptSubmit Hook - Active Tasks Management Rules
# Reminds agent of mandatory workflow requirements on every user prompt

echo ""
echo "ALWAYS, BEFORE STARTING WORK, set the tasks you have been asked to work on as Dev Status: [In Progress]."
echo "ALWAYS, BEFORE STARTING WORK, set active_tasks in config.json when starting work on tasks."
echo "ALWAYS run ALL quality checks before marking any task as verified."
echo "ALWAYS mark QA Status: [Passed] only if checks pass, [Failed - reason] if they fail."
echo "ALWAYS ask user 'Would you like me to fix the failed tasks?' before fixing failures."
echo "ALWAYS clear active_tasks to [] when all tasks pass verification."
echo "NEVER mark QA Status as [Passed] without actually running the quality checks."
echo ""
echo "CRITICAL: User Verification Status (UV) fields are USER-ONLY."
echo "NEVER update or modify UV fields - only users can mark tasks as [Verified]."
echo "UV fields are for final user acceptance/sign-off only."
echo ""
echo "If you understand, respond with \"Synapse workflow loaded...\""
echo ""
