"""Independent diagnostic modules for the DALHA Myeongri core."""

from app.engine.diagnostics.structure import STRUCTURE_DIAGNOSTIC_VERSION, diagnose_structure
from app.engine.diagnostics.strength import STRENGTH_DIAGNOSTIC_VERSION, diagnose_strength

__all__ = [
    "STRUCTURE_DIAGNOSTIC_VERSION",
    "STRENGTH_DIAGNOSTIC_VERSION",
    "diagnose_structure",
    "diagnose_strength",
]
