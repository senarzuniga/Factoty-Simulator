import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

DEFAULT_PROFILE_PATH = Path(__file__).resolve().parents[2] / "config" / "company_profile.json"
MIN_MATURITY_LEVEL = 1
MAX_MATURITY_LEVEL = 5

REQUIRED_COMPANY_FIELDS = {
    "id": str,
    "name": str,
    "country": str,
    "sector": str,
    "machines": int,
    "employees": int,
    "maturity_level": int,
    "annual_revenue_m": (int, float),
    "installed_base_age_avg_years": (int, float),
    "active_contracts": int,
    "logo_color": str,
}


class CompanyProfileError(ValueError):
    """Raised when the company profile is invalid for DEP compatibility."""


def load_company_profile(path: Optional[str] = None) -> Dict[str, Any]:
    profile_path = Path(path) if path else DEFAULT_PROFILE_PATH
    with profile_path.open("r", encoding="utf-8") as fp:
        profile = json.load(fp)
    return validate_company_profile(profile)


def validate_company_profile(profile: Mapping[str, Any]) -> Dict[str, Any]:
    missing_fields = [field for field in REQUIRED_COMPANY_FIELDS if field not in profile]
    if missing_fields:
        raise CompanyProfileError(f"Missing required company fields: {', '.join(missing_fields)}")

    validated = dict(profile)
    for field, expected_type in REQUIRED_COMPANY_FIELDS.items():
        value = validated[field]
        if not isinstance(value, expected_type):
            if isinstance(expected_type, tuple):
                expected = " or ".join(t.__name__ for t in expected_type)
            else:
                expected = expected_type.__name__
            raise CompanyProfileError(
                f"Field '{field}' must be of type {expected}, got {type(value).__name__}"
            )

    if not MIN_MATURITY_LEVEL <= validated["maturity_level"] <= MAX_MATURITY_LEVEL:
        raise CompanyProfileError(
            f"Field 'maturity_level' must be between {MIN_MATURITY_LEVEL} and {MAX_MATURITY_LEVEL}"
        )
    if validated["machines"] <= 0:
        raise CompanyProfileError("Field 'machines' must be greater than zero")
    if validated["employees"] <= 0:
        raise CompanyProfileError("Field 'employees' must be greater than zero")
    if validated["active_contracts"] < 0:
        raise CompanyProfileError("Field 'active_contracts' must be zero or greater")

    return validated


def company_to_dep_entry(profile: Mapping[str, Any]) -> Dict[str, Any]:
    validated = validate_company_profile(profile)
    return {key: validated[key] for key in REQUIRED_COMPANY_FIELDS}
