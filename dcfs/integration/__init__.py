"""Integration helpers for external digital ecosystem platforms."""

from dcfs.integration.company_profile import (
    company_to_dep_entry,
    load_company_profile,
    validate_company_profile,
)
from dcfs.integration.dep_bridge import DEPBridgeClient

__all__ = [
    "DEPBridgeClient",
    "company_to_dep_entry",
    "load_company_profile",
    "validate_company_profile",
]
