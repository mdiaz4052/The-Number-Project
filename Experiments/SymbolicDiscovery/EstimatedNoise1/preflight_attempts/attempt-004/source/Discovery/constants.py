"""A small, sourced physical-constant catalogue for Milestone 1.

Values are SI values from the 2022 CODATA adjustment unless noted otherwise.
Planck units are derived using measured ``G``; searches involving them therefore
serve as controls and must not be presented as independent determinations of G.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from Discovery.dimensions import (
    ACTION,
    ENERGY,
    GRAVITATIONAL_CONSTANT,
    LENGTH,
    MASS,
    TEMPERATURE,
    TIME,
    VELOCITY,
    Dimension,
)


NIST_CODATA_2022 = "https://physics.nist.gov/cuu/Constants/Table/allascii.txt"
BIPM_SI_DEFINITIONS = "https://www.bipm.org/en/measurement-units/si-defining-constants"


@dataclass(frozen=True, slots=True)
class PhysicalConstant:
    """A positive scalar constant expressed in coherent SI units."""

    key: str
    symbol: str
    value_si: float
    dimension: Dimension
    si_unit: str
    description: str
    source_url: str
    standard_uncertainty_si: float | None = None
    exact: bool = False
    provenance: str = "experimentally adjusted"

    def __post_init__(self) -> None:
        if not math.isfinite(self.value_si) or self.value_si <= 0:
            raise ValueError(f"{self.key} must have a finite positive SI value")
        if self.standard_uncertainty_si is not None:
            if not math.isfinite(self.standard_uncertainty_si):
                raise ValueError(f"{self.key} has a non-finite uncertainty")
            if self.standard_uncertainty_si < 0:
                raise ValueError(f"{self.key} has a negative uncertainty")
        if self.exact and self.standard_uncertainty_si not in (None, 0.0):
            raise ValueError(f"{self.key} cannot be exact and uncertain")

    @property
    def relative_uncertainty(self) -> float | None:
        if self.exact:
            return 0.0
        if self.standard_uncertainty_si is None:
            return None
        return self.standard_uncertainty_si / self.value_si


SPEED_OF_LIGHT = PhysicalConstant(
    key="c",
    symbol="c",
    value_si=299_792_458.0,
    dimension=VELOCITY,
    si_unit="m s^-1",
    description="speed of light in vacuum",
    source_url=BIPM_SI_DEFINITIONS,
    exact=True,
    provenance="exact SI defining constant",
)

# h is exact in the SI; hbar = h/(2*pi), with mathematical pi exact.
REDUCED_PLANCK_CONSTANT = PhysicalConstant(
    key="hbar",
    symbol="hbar",
    value_si=6.626_070_15e-34 / (2.0 * math.pi),
    dimension=ACTION,
    si_unit="J s",
    description="reduced Planck constant",
    source_url=BIPM_SI_DEFINITIONS,
    exact=True,
    provenance="derived from exact SI defining constant h",
)

BOLTZMANN_CONSTANT = PhysicalConstant(
    key="k_B",
    symbol="k_B",
    value_si=1.380_649e-23,
    dimension=ENERGY / TEMPERATURE,
    si_unit="J K^-1",
    description="Boltzmann constant",
    source_url=BIPM_SI_DEFINITIONS,
    exact=True,
    provenance="exact SI defining constant",
)

ELECTRON_MASS = PhysicalConstant(
    key="m_e",
    symbol="m_e",
    value_si=9.109_383_713_9e-31,
    standard_uncertainty_si=0.000_000_002_8e-31,
    dimension=MASS,
    si_unit="kg",
    description="electron mass",
    source_url=NIST_CODATA_2022,
)

PROTON_MASS = PhysicalConstant(
    key="m_p",
    symbol="m_p",
    value_si=1.672_621_925_95e-27,
    standard_uncertainty_si=0.000_000_000_52e-27,
    dimension=MASS,
    si_unit="kg",
    description="proton mass",
    source_url=NIST_CODATA_2022,
)

ATOMIC_MASS_CONSTANT = PhysicalConstant(
    key="m_u",
    symbol="m_u",
    value_si=1.660_539_068_92e-27,
    standard_uncertainty_si=0.000_000_000_52e-27,
    dimension=MASS,
    si_unit="kg",
    description="unified atomic mass constant",
    source_url=NIST_CODATA_2022,
)

PLANCK_LENGTH = PhysicalConstant(
    key="l_P",
    symbol="l_P",
    value_si=1.616_255e-35,
    standard_uncertainty_si=0.000_018e-35,
    dimension=LENGTH,
    si_unit="m",
    description="Planck length",
    source_url=NIST_CODATA_2022,
    provenance="derived quantity whose definition contains G",
)

PLANCK_MASS = PhysicalConstant(
    key="m_P",
    symbol="m_P",
    value_si=2.176_434e-8,
    standard_uncertainty_si=0.000_024e-8,
    dimension=MASS,
    si_unit="kg",
    description="Planck mass",
    source_url=NIST_CODATA_2022,
    provenance="derived quantity whose definition contains G",
)

PLANCK_TIME = PhysicalConstant(
    key="t_P",
    symbol="t_P",
    value_si=5.391_247e-44,
    standard_uncertainty_si=0.000_060e-44,
    dimension=TIME,
    si_unit="s",
    description="Planck time",
    source_url=NIST_CODATA_2022,
    provenance="derived quantity whose definition contains G",
)

PLANCK_TEMPERATURE = PhysicalConstant(
    key="T_P",
    symbol="T_P",
    value_si=1.416_784e32,
    standard_uncertainty_si=0.000_016e32,
    dimension=TEMPERATURE,
    si_unit="K",
    description="Planck temperature",
    source_url=NIST_CODATA_2022,
    provenance="derived quantity whose definition contains G",
)

GRAVITATIONAL_CONSTANT_G = PhysicalConstant(
    key="G",
    symbol="G",
    value_si=6.674_30e-11,
    standard_uncertainty_si=0.000_15e-11,
    dimension=GRAVITATIONAL_CONSTANT,
    si_unit="m^3 kg^-1 s^-2",
    description="Newtonian constant of gravitation",
    source_url=NIST_CODATA_2022,
    provenance="measured target; excluded from search generators",
)


DEFAULT_SEARCH_CONSTANTS = (
    SPEED_OF_LIGHT,
    REDUCED_PLANCK_CONSTANT,
    BOLTZMANN_CONSTANT,
    ELECTRON_MASS,
    PROTON_MASS,
    ATOMIC_MASS_CONSTANT,
    PLANCK_LENGTH,
    PLANCK_MASS,
    PLANCK_TIME,
    PLANCK_TEMPERATURE,
)

