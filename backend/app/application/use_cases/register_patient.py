"""Caso de uso: registrar um paciente no dossiê."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.entities import Allergy, Criticality, Patient
from app.domain.ports import PatientRepository


@dataclass(frozen=True)
class AllergyInput:
    substance: str
    criticality: Criticality = Criticality.LOW


@dataclass(frozen=True)
class RegisterPatient:
    patients: PatientRepository

    def execute(
        self,
        *,
        given_name: str,
        family_name: str,
        birth_date: date,
        mrn: str,
        allergies: tuple[AllergyInput, ...] = (),
    ) -> Patient:
        patient = Patient(
            given_name=given_name,
            family_name=family_name,
            birth_date=birth_date,
            mrn=mrn,
        )
        for item in allergies:
            patient.add_allergy(Allergy(substance=item.substance, criticality=item.criticality))
        self.patients.add(patient)
        return patient
