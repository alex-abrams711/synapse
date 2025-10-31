
#!/bin/bash
# UserPromptSubmit Hook - Process Guardrails
# Reminds Claude of mandatory workflow requirements on every user prompt

echo ""
echo "ALWAYS use implementer sub-agent for implementation tasks."
echo "ALWAYS use verifier sub-agent for verification tasks."
echo "ALWAYS follow implementation with verification."
echo "ALWAYS stop and wait for user input before continuing to new task."
echo ""
echo "If you understand, please respond with \"Synapse feature workflow loaded...\""
echo ""
