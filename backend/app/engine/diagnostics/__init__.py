"""Independent diagnostic modules for the DALHA Myeongri core."""

from app.engine.diagnostics.structure import STRUCTURE_DIAGNOSTIC_VERSION, diagnose_structure
from app.engine.diagnostics.strength import STRENGTH_DIAGNOSTIC_VERSION, diagnose_strength
from app.engine.diagnostics.climate import CLIMATE_DIAGNOSTIC_VERSION, diagnose_climate
from app.engine.diagnostics.pathology import PATHOLOGY_DIAGNOSTIC_VERSION, diagnose_pathology
from app.engine.diagnostics.mediation import MEDIATION_DIAGNOSTIC_VERSION, diagnose_mediation

__all__ = [
    "STRUCTURE_DIAGNOSTIC_VERSION",
    "STRENGTH_DIAGNOSTIC_VERSION",
    "CLIMATE_DIAGNOSTIC_VERSION",
    "diagnose_climate",
    "PATHOLOGY_DIAGNOSTIC_VERSION",
    "diagnose_pathology",
    "MEDIATION_DIAGNOSTIC_VERSION",
    "diagnose_mediation",
    "diagnose_structure",
    "diagnose_strength",
]
