from __future__ import annotations

from datetime import datetime
from threading import Lock
from uuid import UUID

from buddy.contracts.buddy_contracts import AccessCheck, CommunityReport


class InMemoryStore:
    """Process-local storage for the hack build.

    TODO(supabase): replace this with Supabase tables for checks, evidence,
    call sessions, and community reports while preserving the contract models.
    """

    def __init__(self) -> None:
        self._checks: dict[UUID, AccessCheck] = {}
        self._community_reports: dict[UUID, CommunityReport] = {}
        self._lock = Lock()

    def save_check(self, check: AccessCheck) -> AccessCheck:
        check.updated_at = datetime.utcnow()
        with self._lock:
            self._checks[check.id] = check
        return check

    def get_check(self, check_id: UUID) -> AccessCheck | None:
        with self._lock:
            return self._checks.get(check_id)

    def list_checks(self) -> list[AccessCheck]:
        with self._lock:
            return sorted(self._checks.values(), key=lambda check: check.created_at, reverse=True)

    def save_community_report(self, report: CommunityReport) -> CommunityReport:
        with self._lock:
            self._community_reports[report.id] = report
        return report

    def get_community_report(self, report_id: UUID) -> CommunityReport | None:
        with self._lock:
            return self._community_reports.get(report_id)

    def list_community_reports(self) -> list[CommunityReport]:
        with self._lock:
            return sorted(
                self._community_reports.values(),
                key=lambda report: report.created_at,
                reverse=True,
            )


store = InMemoryStore()

