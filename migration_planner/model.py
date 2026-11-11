"""Plain data classes shared across the package."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

DISPOSITIONS = ("rehost", "replatform", "refactor", "repurchase", "retire", "retain")
# Dispositions that move or replace a workload in the migration programme.
MIGRATING = ("rehost", "replatform", "refactor", "repurchase")

INVENTORY_FIELDS = (
    "app_id",
    "name",
    "owner",
    "business_criticality",
    "users",
    "technology",
    "os_or_platform",
    "end_of_support_date",
    "vendor_supported_in_cloud",
    "data_sensitivity",
    "dependencies",
    "current_annual_cost",
    "change_frequency",
    "licence_model",
    "notes",
)
# Optional extra column: an Azure annual run cost estimate taken from a proper assessment.
OPTIONAL_FIELDS = ("azure_annual_cost_estimate",)

VENDOR_VALUES = ("yes", "no", "unknown")
SENSITIVITY_VALUES = ("low", "medium", "high", "restricted")
CHANGE_VALUES = ("none", "low", "medium", "high")


@dataclass
class App:
    app_id: str
    name: str
    owner: str
    business_criticality: int
    users: int | None
    technology: str
    os_or_platform: str
    end_of_support_date: date | None
    vendor_supported_in_cloud: str
    data_sensitivity: str
    dependencies: tuple[str, ...]
    current_annual_cost: float | None
    change_frequency: str
    licence_model: str
    notes: str
    azure_annual_cost_estimate: float | None = None
    line: int = 0


@dataclass
class Assessed:
    """An application plus the decision the rules reached."""

    app: App
    tech_class: str
    eos_status: str
    dependents_count: int
    disposition: str
    in_scope: bool
    scores: dict
    runner_up: str
    margin: int
    confidence: str
    needs_review: bool
    reasons: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    overridden: bool = False
