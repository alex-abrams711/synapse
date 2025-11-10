# Legacy Workflows

This directory contains the original implementation of Synapse workflows prior to the Option 6 QA verification redesign.

## Status

**These workflows are stable and fully supported.**

No breaking changes have been made to these workflows. They continue to work exactly as before and will remain available for users who prefer the original approach.

## What's in Legacy

- **`resources/schemas/`** - Original config schema with `third_party_workflows.detected` (array)
- **`resources/workflows/feature-implementation/`** - Original feature implementation workflow with complex validation hooks
- **`resources/workflows/feature-planning/`** - Original feature planning workflow

## Why Legacy?

The new Option 6 implementation (in `/resources`) represents a significant architectural change:

1. **Simpler hooks**: ~400 lines vs 1000+ lines
2. **Schema-driven**: Flexible task format parsing
3. **User control**: Can stop with failures, decide when to fix
4. **Breaking config changes**: `third_party_workflow` (object) instead of array

Rather than migrate existing workflows in-place, we created a fresh implementation in parallel. This approach:
- ✅ Preserves existing functionality
- ✅ Avoids mid-stream breaking changes
- ✅ Allows users to opt-in when ready
- ✅ Provides a reference implementation

## Migrating to New Workflows

If you want to adopt the new Option 6 workflows in `/resources`:

1. **Complete any in-progress work** using legacy workflows
2. **Run updated sense command** (when available) to generate new config structure
3. **Update tasks.md** to use task code format if needed
4. **Switch workflow** in your project settings

See `/resources/workflows/feature-implementation-v2/README.md` for details on the new approach.

## Support

Legacy workflows will continue to be maintained and supported alongside the new implementation. Choose whichever approach works best for your project.
