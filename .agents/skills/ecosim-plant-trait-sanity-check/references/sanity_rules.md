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
- `IEBTYP` should use EcoSIM embryophyte type codes `0=bryophyte`, `1=pteridophyte`, `2=gymnosperm`, `3=monocot`, and `4=eudicot`. The checker accepts either a valid integer code or a recognized label in `.desc` output, errors on missing, unrecognized, non-integer, or out-of-range values, and warns when the value conflicts with the inferred PFT form from the block code/name.
- `ISNTYP` should use EcoSIM snow interception pattern codes `0=bryophyte`, `1=grass`, `2=shrub`, `3=deciduous tree`, and `4=conifer`. The checker errors on missing, non-integer, or out-of-range numeric codes, and warns when the code conflicts with the label text or the inferred PFT form from the block code/name.
- Fraction traits such as `RUBP`, `PEPC`, `CHL`, `FCO2`, `ALBR`, `ALBP`, `TAUR`, `TAUP`, `CFI`, `PORT`, `PhiMIN`, `PhiMAX`, and `PhiMean` should be within `[0, 1]`. In photosynthetic properties, `CHL` is the fraction of total leaf protein in chlorophyll-bound/light-harvesting proteins, including chlorophyll-protein complexes associated with PSI, PSII, and LHC.
- `CHL` values in `PHOTOSYNTHETIC PROPERTIES` should normally fall in a broad screening range of `0.08-0.30` on the total-leaf-protein basis. Values below this range likely under-allocate protein to light harvesting, especially for evergreen needleleaf PFTs.
- Do not use `SLA1` values for sanity-check decisions, including web-informed checks or derived leaf-area photosynthetic capacity calculations.
- `CLASS` must contain four numeric inclination fractions, each in `[0, 1]`, summing to one.
- Optical checks should flag `ALBR + TAUR > 1` and `ALBP + TAUP > 1`.
- `ANGSH` must be `0 degrees` for plant forms that lack petiole or sheath tissue. This includes conifer, lichen, and moss PFTs where a nonzero petiole/sheath angle would imply an organ that is not represented by the plant morphology.
- Growth yields `DMLF`, `DMSHE`, `DMSTK`, `DMRSV`, `DMHSK`, `DMEAR`, `DMGR`, and `DMRT` should be positive and normally not exceed about `1.2`.
- Phenological accumulation thresholds `VRNLI` and `VRNXI` should be nonnegative; zero can encode no accumulated leafout or leafoff requirement.
- Organ N and P mass ratios (`CNLF`, `CNSHE`, `CNSTK`, `CNRTLIG`, `CNRSV`, `CNHSK`, `CNEAR`, `CNGR`, `CNRT`, `CPLF`, `CPSHE`, `CPSTK`, `CPRTLIG`, `CPRSV`, `CPHSK`, `CPEAR`, `CPGR`, `CPRT`) must be positive; values above `0.2 g element gC-1` are suspicious enough to warn.
- `OSMO` should be negative in MPa. Very negative values below about `-5 MPa` deserve a warning.
- `WTSTDI` should be nonnegative.

## Active Structural Protein Pools

- Relate total protein C to both total N and total P in active structural biomass. For an organ with structural N and P concentrations `N/C` and `P/C`, calculate the N-supported protein fraction as `(protein C:N) * (N/C)`, the P-supported fraction as `(protein C:P) * (P/C)`, and the realized protein C fraction as the smaller of the two.
- For leaves, all structural biomass is active. Use `leaf protein C / leaf structural C = min(CNWL*CNLF, CPWL*CPLF)`.
- For non-tree roots, all structural biomass is active. Use `root protein C / root structural C = min(CNWR*CNRT, CPWR*CPRT)` across the entire structural root pool.
- For tree and other woody-PFT roots, apply the same root relationship only to active structural biomass. Exclude lignified heartwood, represented separately by `CNRTLIG` and `CPRTLIG`, from the root protein pool. A static trait file does not contain the dynamic active-to-heartwood C partition, so do not estimate whole-root protein C by mixing active-root and lignified-heartwood concentrations.
- Require the N/P-limited protein C fraction to be no greater than `1 gC protein gC structural biomass-1`. Warn when either single-nutrient-supported amount exceeds one even if the other nutrient keeps the realized pool below one.
- Interpret `CNWL`, `CPWL`, `CNWR`, and `CPWR` as protein-pool stoichiometry, not whole-organ elemental C:N or C:P ratios.

## Clean Photosynthetic Parameterization

Apply these as pathway-aware physiological warnings. Promote them to errors when `--strict-physiology` is requested. The ranges are deliberately broad screening bounds, not cultivar-specific calibration targets.

- Require a recognizable `ICTYP` pathway and all inputs needed for the corresponding kinetic, allocation, capacity-ratio, and optical checks. Missing values must not silently disable strict physiology.
- Treat `VCMX`, `VOMX`, `XKCO2`, and `XKO2` as a Rubisco kinetic quartet. Check `VCMX/VOMX` against `6-14` for C4 and `2-8` for C3, and check implied specificity `VCMX*XKO2/(VOMX*XKCO2)` against `70-140`. This prevents an unrealistic turnover ratio from being hidden by compensating Km values.
- Screen C4 `XKCO2` at `10-35 uM`, `XKO2` at `120-400 uM`, and effective `XKCO24` at `0.5-20 uM`. Screen C3 `XKCO2` at `8-30 uM` and `XKO2` at `180-650 uM`. EcoSIM uses these as aqueous 25 C reference constants.
- Define photosynthesis-related allocations (`RUBP`, `PEPC`, and `CHL`) relative to total leaf protein C, not leaf structural C or total leaf N. First derive `leaf_protein_C_per_leaf_C = min(CNWL*CNLF, CPWL*CPLF)` and `effective_CNWL = leaf_protein_C_per_leaf_C/CNLF`. Then estimate enzyme nitrogen allocation with `fN_enzyme = allocation * effective_CNWL / 3.3`, using `3.3 gC protein gN-1` when enzyme-specific composition is unavailable. Screen Rubisco at `5-16%` of total leaf N for C4 and `8-30%` for C3. Screen C4 PEPC at `1-6%`; field maize commonly allocates about `2.5-3.5%`.
- Require `RUBP + CHL + PEPC <= 0.65` for C4 and `RUBP + CHL <= 0.65` for C3 because these fractions draw from one total-leaf-protein pool.
- For C4, calculate protein-normalized `Vpmax:Vcmax = VCMX4*PEPC/(VCMX*RUBP)` and screen at `0.8-2.5`.
- Calculate protein-normalized `Jmax:Vcmax` using EcoSIM's chlorophyll-C conversion: `ETMX*CHL*fCHLMESO/(3.7*VCMX*RUBP)` for C4, screened at `4-8`; and `ETMX*CHL/(3.5*VCMX*RUBP)` for C3, screened at `1.2-3`.
- Screen `FCO2` at `0.25-0.50` for C4 and `0.55-0.85` for C3. Screen C4 `fCHLMESO` at `0.40-0.75`.
- Screen leaf PAR absorptance `1-ALBP-TAUP` at `0.80-0.95` and broad shortwave absorptance `1-ALBR-TAUR` at `0.30-0.85`.

Use web evidence to narrow these ranges for a species, cultivar, nitrogen treatment, growth stage, and measurement protocol. Useful foundations include the corrected Rubisco kinetic compilation (https://doi.org/10.1093/jxb/erab383), maize nitrogen allocation (https://doi.org/10.3389/fpls.2016.00699), maize seasonal capacity ratios (https://doi.org/10.1111/pce.13511), and maize mesophyll/bundle-sheath chlorophyll partitioning (https://doi.org/10.1104/pp.51.6.1133).

## Woody Versus Herbaceous Root Blocks

Woody short codes include common EcoSIM trees and shrubs such as `ndlf`, `ndld`, `bdlf`, `bdln`, `bdlw`, `bspr`, `dfir`, `jpin`, `lpin`, `tasp`, `woak`, `shru`, `bush`, and `busn`.

Woody blocks should include:

- `ROOTMAGE`
- `PhiMIN`
- `PhiMAX`
- `R95MAT`
- two `KLGMAX` rows when the format distinguishes maximum lignification rate from half-saturation parameter
- lignified root concentrations `CNRTLIG` and `CPRTLIG`

Herbaceous blocks should include `PhiMean` unless both `PhiMIN` and `PhiMAX`
are defined. When the root maturation pair `PhiMIN`/`PhiMAX` is present,
`PhiMean` is not required.
Exception: soybean (`soyb*`) is a eudicot crop that can express secondary root
growth, so `ROOTMAGE`, `PhiMIN`, `PhiMAX`, and `R95MAT` are allowed for soybean
without issuing the generic non-woody root-trait warning. Still check their
numeric bounds and `PhiMIN <= PhiMAX`.

## Interpretation

Treat `ERROR` findings as likely malformed or numerically invalid input. Treat `WARN` findings as requiring domain review. A warning can be ecologically defensible, but it should be traceable to a species-specific source, deliberate parameterization, or documented EcoSIM convention.
