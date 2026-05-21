# EcoSIM Plant Trait Sanity Rules

These checks are intentionally conservative. They catch values that are likely to break EcoSIM preprocessing, violate obvious unit/range expectations, or reveal a malformed block. They do not prove that a parameter is ecologically optimal for a given species.

Use web-informed evidence after these deterministic checks when judging whether a plausible numeric value is ecologically reasonable for the plant represented by the block.

## Block Scope

- One `PLANT traits for FUNCTIONAL TYPE` block is one plant record.
- The default scope is the first grid: `NY=1, NX=1`.
- Check all plant records at that grid, usually distinguished by `NZ` and PFT code.
- Do not infer that repeated blocks for other `NX` or `NY` values have been validated unless explicitly checked.

## Structural Checks

Required sections:

- `PLANT CLASS INFORMATION`
- `PHOTOSYNTHETIC PROPERTIES`
- `OPTICAL PROPERTIES`
- `PHENOLOGICAL PROPERTIES`
- `MORPHOLOGICAL PROPERTIES`
- `ROOT CHARACTERISTICS`
- `ROOT UPTAKE PARAMETERS`
- `WATER RELATIONS`
- `ORGAN GROWTH YIELDS`
- `ORGAN N AND P CONCENTRATIONS`

The parser should keep duplicate variable names in file order. `KLGMAX` is the common duplicate in woody root traits.

## High-Value Range Rules

- In `PLANT CLASS INFORMATION`, any block with `ISTYP` set to annual should have `IWTYP` set to evergreen. This is an EcoSIM convention: all annual plants are considered evergreen for the phenology-type field.
- Fraction traits such as `RUBP`, `CHL`, `FCO2`, `ALBR`, `ALBP`, `TAUR`, `TAUP`, `CFI`, `PORT`, `PhiMIN`, `PhiMAX`, and `PhiMean` should be within `[0, 1]`. In photosynthetic properties, `CHL` is the fraction of total leaf protein in chlorophyll-bound/light-harvesting proteins, including chlorophyll-protein complexes associated with PSI, PSII, and LHC.
- `CHL` values in `PHOTOSYNTHETIC PROPERTIES` should normally fall in a broad screening range of `0.08-0.30` on the total-leaf-protein basis. Values below this range likely under-allocate protein to light harvesting, especially for evergreen needleleaf PFTs.
- Do not use `SLA1` values for sanity-check decisions, including web-informed checks or derived leaf-area photosynthetic capacity calculations.
- `CLASS` must contain four numeric inclination fractions, each in `[0, 1]`, summing to one.
- Optical checks should flag `ALBR + TAUR > 1` and `ALBP + TAUP > 1`.
- Growth yields `DMLF`, `DMSHE`, `DMSTK`, `DMRSV`, `DMHSK`, `DMEAR`, `DMGR`, and `DMRT` should be positive and normally not exceed about `1.2`.
- Phenological accumulation thresholds `VRNLI` and `VRNXI` should be nonnegative; zero can encode no accumulated leafout or leafoff requirement.
- Organ N and P mass ratios (`CNLF`, `CNSHE`, `CNSTK`, `CNRTLIG`, `CNRSV`, `CNHSK`, `CNEAR`, `CNGR`, `CNRT`, `CPLF`, `CPSHE`, `CPSTK`, `CPRTLIG`, `CPRSV`, `CPHSK`, `CPEAR`, `CPGR`, `CPRT`) must be positive; values above `0.2 g element gC-1` are suspicious enough to warn.
- `OSMO` should be negative in MPa. Very negative values below about `-5 MPa` deserve a warning.
- `WTSTDI` should be nonnegative.

## Woody Versus Herbaceous Root Blocks

Woody short codes include common EcoSIM trees and shrubs such as `ndlf`, `ndld`, `bdlf`, `bdln`, `bdlw`, `bspr`, `dfir`, `jpin`, `lpin`, `tasp`, `woak`, `shru`, `bush`, and `busn`.

Woody blocks should include:

- `ROOTMAGE`
- `PhiMIN`
- `PhiMAX`
- `R95MAT`
- two `KLGMAX` rows when the format distinguishes maximum lignification rate from half-saturation parameter
- lignified root concentrations `CNRTLIG` and `CPRTLIG`

Herbaceous blocks should include `PhiMean` and normally should not include woody-only root maturation traits.

## Interpretation

Treat `ERROR` findings as likely malformed or numerically invalid input. Treat `WARN` findings as requiring domain review. A warning can be ecologically defensible, but it should be traceable to a species-specific source, deliberate parameterization, or documented EcoSIM convention.
