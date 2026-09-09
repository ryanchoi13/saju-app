"""Keep an unrelated completed operation when another direction is disputed."""


def operation_block_reason(operation, synthesis):
    name = operation.get("operation")
    if operation.get("assessment_status") not in {None, "completed"} or operation.get("unresolved_requirements"):
        return "operation_judgment_unconfirmed"
    if any(c.get("operation") == name for c in synthesis.get("caution_operations", [])):
        return "operation_is_cautioned"
    for conflict in synthesis.get("diagnostic_conflicts", []):
        if conflict.get("resolution") not in {"preserve_as_unresolved", "preserve_partial_result"}:
            continue
        affected = conflict.get("operations")
        if affected:
            if name in affected:
                return "operation_has_unresolved_conflict"
            continue
        # A genuinely unscoped conflict still blocks; never invent its scope.
        return "unscoped_unresolved_conflict"
    return None


def usable_operations(synthesis):
    return [o for o in synthesis.get("favorable_operations", []) if not operation_block_reason(o, synthesis)]
