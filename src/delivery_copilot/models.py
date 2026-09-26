"""Data model for engagements, risks, tasks, and time entries."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

VALID_ENGAGEMENT_STATUSES = ("active", "at-risk", "closed")
VALID_RISK_SEVERITIES = ("low", "medium", "high")
VALID_RISK_STATUSES = ("open", "mitigated")
VALID_TASK_STATUSES = ("todo", "in_progress", "done")


@dataclass
class Risk:
    id: str
    description: str
    severity: str
    owner: str
    opened_date: str
    status: str = "open"
    mitigation: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Risk":
        return Risk(**d)


@dataclass
class Task:
    id: str
    title: str
    assignee: str
    due_date: str
    status: str = "todo"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Task":
        return Task(**d)


@dataclass
class TimeEntry:
    date: str
    consultant: str
    hours: float
    note: str = ""
    task_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "TimeEntry":
        return TimeEntry(**d)


@dataclass
class Engagement:
    id: str
    client_name: str
    name: str
    start_date: str
    lead: str
    end_date: Optional[str] = None
    status: str = "active"
    risks: list[Risk] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    time_entries: list[TimeEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: dict) -> "Engagement":
        d = dict(d)
        d["risks"] = [Risk.from_dict(r) for r in d.get("risks", [])]
        d["tasks"] = [Task.from_dict(t) for t in d.get("tasks", [])]
        d["time_entries"] = [TimeEntry.from_dict(t) for t in d.get("time_entries", [])]
        return Engagement(**d)

    def open_risks(self) -> list[Risk]:
        return [r for r in self.risks if r.status == "open"]

    def total_hours(self) -> float:
        return sum(t.hours for t in self.time_entries)
