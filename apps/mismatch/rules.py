DEFAULT_RULES = {
    "missing_approval": {
        "description": "Cost estimate exists but cost approval is missing or not approved.",
        "severity": "high",
    },
    "unmapped_release_item": {
        "description": "Release item has no mapped ADO sprint snapshot.",
        "severity": "medium",
    },
    "stale_vendor_update": {
        "description": "Vendor action has not been updated within stale window.",
        "severity": "medium",
    },
}
