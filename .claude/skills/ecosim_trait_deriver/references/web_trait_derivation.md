# Web Trait Derivation

Use this reference when the task is to derive EcoSIM parameters for a named plant from web and online literature evidence.

## Decision sequence

1. Resolve the accepted scientific name.
2. Decide whether the plant maps best to the tree anchor `ndlf43` or the grass anchor `gr3s43`.
3. Extract the anchor traits from the template `.desc`.
4. Search for plant-specific evidence in both species-profile sources and online literature.
5. Update the anchor values only where evidence supports a change.

## Recommended source stack

### Identity and growth form

- Kew POWO
- USDA PLANTS or USDA Forest Service

Use these to determine:

- accepted scientific name
- family
- life form
- perennial vs annual
- woody vs herbaceous
- broad climate or habitat context

### Trees and forestry species

- USDA Forest Service Silvics pages
- USDA Fire Effects Information System
- peer-reviewed forestry ecology papers
- online theses, dissertations, technical reports, and forestry books when they contain primary measurements

Useful for:

- height and growth form
- drought tolerance
- shade tolerance
- regeneration strategy
- root habit
- phenology
- habitat and climate range

### Grasses and crops

- FAO ECOCROP
- USDA crop resources
- peer-reviewed crop physiology papers
- online agronomy theses, extension technical bulletins, and cultivar reports when they contain measured traits

Useful for:

- life span
- habit
- photoperiod
- growing cycle
- climate requirements
- crop physiology and nutrient traits

## Online literature search workflow

For any quantitative trait that is likely to be measured in the literature, do not rely only on species summaries.

Search iteratively:

1. accepted scientific name + exact trait term
2. accepted scientific name + synonyms or older taxonomy + exact trait term
3. accepted scientific name + organ or process terms such as `photosynthesis`, `leaf nitrogen`, `specific leaf area`, `seed mass`, `root depth`, `hydraulic`, `water potential`
4. genus name + exact trait term if species-level search fails
5. functional-type synthesis only if species and genus searches fail

Good literature targets include:

- journal articles
- supplemental tables and appendices
- books and species monographs
- theses and dissertations
- technical reports with primary measurements
- trait datasets with traceable citations

When a value comes from a secondary source, prefer tracing it back to the primary citation if possible.

## Trait mapping heuristics

### Safe direct mappings

These can often be mapped directly from source descriptions:

- `ISTYP`
- `IDTYP`
- `IWTYP`
- `IPTYP`
- `MY`
- `ZTYPI`
- `WDLF`
- `GRMX`
- `GRDM`
- `WTSTDI`

### Usually inference-heavy

These should be changed only with stronger support:

- `VCMX`
- `VOMX`
- `ETMX`
- `RUBP`
- `UPMXZH`
- `UPMXZO`
- `UPMXPO`
- `RCS`
- `RSMX`

Traits in this group should usually trigger a literature search before you decide to keep the anchor.

### Often template-retained

Unless high-quality quantitative data are found, these often remain close to the anchor:

- `OPTICAL PROPERTIES`
- many `ROOT UPTAKE PARAMETERS`
- many `ORGAN GROWTH YIELDS`

Even for these, still check online literature if the user is asking for a species-specific derivation rather than a fast approximation.

## Output expectations

For each changed trait, record:

- trait code
- derived value
- rationale
- evidence source
- provenance label

Also record:

- whether the support came from species page, database, or online literature
- whether the value is species-level, genus-level, or functional-type-level

For unchanged traits, prefer:

- keep the anchor value
- mark it `template-retained`

## Examples

### Limber Pine

- likely anchor: `ndlf43`
- evidence to look for:
  - evergreen conifer
  - long-lived, slow-growing tree
  - drought and cold tolerance
  - deep roots / woody roots
  - ectomycorrhizal association

### Maize

- likely anchor: `gr3s43`
- evidence to look for:
  - annual C4 grass
  - crop cycle and photoperiod response
  - high nutrient demand
  - shallow to intermediate fibrous root system
  - crop physiology measurements from agronomy literature
