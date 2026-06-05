"""Caso de uso: ingerir um laudo (saída de OCR) num caso cirúrgico."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import DiagnosticReport, ReportStatus
from app.domain.errors import EntityNotFound
from app.domain.ports import DiagnosticReportRepository, SurgicalCaseRepository


@dataclass(frozen=True)
class IngestDiagnosticReport:
    cases: SurgicalCaseRepository
    reports: DiagnosticReportRepository

    def execute(
        self,
        *,
        surgical_case_id: UUID,
        extracted: dict,
        status: ReportStatus = ReportStatus.PARTIAL,
        presented_form_url: str | None = None,
    ) -> DiagnosticReport:
        if self.cases.get(surgical_case_id) is None:
            raise EntityNotFound(f"caso cirúrgico {surgical_case_id} não encontrado")
        report = DiagnosticReport(
            surgical_case_id=surgical_case_id,
            status=status,
            extracted=extracted,
            presented_form_url=presented_form_url,
        )
        self.reports.add(report)
        return report
