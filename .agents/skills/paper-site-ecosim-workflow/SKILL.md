---
name: paper-site-ecosim-workflow
description: Extract study sites, observational variables, and cited data sources from ecosystem-modeling papers, PDFs, supplements, or article text, then plan or create EcoSIM simulation workflows and run folders for those sites. Use when Codex is asked to read a paper for EcoSIM feasibility, including requests phrased as "read paper for ecosim feasibility"; read a paper for sites/data availability; reproduce a published site simulation in EcoSIM; compare EcoSIM outputs to paper observations; or convert paper-derived AmeriFlux/FLUXNET/crop-site information into EcoSIM inputs and runnable cases.
---

# Paper Site EcoSIM Workflow

## Overview

Use this skill to turn a modeling paper into an actionable EcoSIM site-simulation plan. The workflow has two linked products:

- a site-by-site evidence table of observations and literature/data sources
- a procedure for preparing, running, and evaluating EcoSIM simulations for those sites

Do not edit source papers or model inputs unless the user explicitly asks for implementation.

## Trigger Phrases

Use this skill whenever the request asks to `read paper for ecosim feasibility`, `read the paper for ecosim feasibility`, assess whether a paper can be simulated in EcoSIM, or judge EcoSIM feasibility from a paper/PDF.

## Paper Reading Workflow

1. Identify the paper artifact: PDF, DOCX, HTML, plain text, supplement, or citation/DOI.
2. For local PDFs, extract text page by page with the bundled Python runtime. If `pdftotext` is unavailable, use `pypdf`. If text extraction is poor or tables are image-only, render pages or use OCR only for the needed pages.
3. Search the extracted text for:
   - `Experimental sites`, `site`, `AmeriFlux`, `FLUXNET`, `location`
   - `observed`, `measured`, `validation`, `calibration`, `data`
   - variables such as `biomass`, `LAI`, `GLAI`, `yield`, `NEE`, `ET`, `SWC`, `soil water`, `soil temperature`, `SOC`, `POC`, `MAOC`, `N2O`
   - `References`, `Supporting Information`, `Table`, `Figure`
4. Build a site inventory. Normalize site IDs exactly, for example `US-Ne1`, `US-Ne2`, `US-Ne3`, `US-Pon`.
5. For each site, distinguish:
   - variables directly measured and used for calibration or validation
   - variables available only as management/forcing inputs
   - variables compared informally but not formal validation targets
   - variables explicitly unavailable or only simulated
6. Trace every observational variable to its source:
   - direct dataset DOI or portal record, such as AmeriFlux BASE
   - method or site-description paper
   - prior model-input paper
   - current paper figure/table if no external data source is cited
7. Report a compact table with columns:
   - site
   - location or cropping/vegetation system
   - observational variables available
   - calibration/validation role when stated
   - cited source(s)
   - caveats

Avoid copying long passages from the paper. Summarize and cite.

## EcoSIM Simulation Workflow

After the paper-derived site table is complete, use this workflow to prepare EcoSIM simulations. Assume the EcoSIM executable is ready unless the user says otherwise.

1. Resolve each site.
   - For AmeriFlux/FLUXNET sites, use `ameriflux-site-info` for metadata.
   - Record latitude, longitude, elevation, site name, vegetation/crop identity, and years used in the paper.
   - If the site has a known Koppen label, convert it with `koppen-climate-codec`; otherwise derive it from coordinates.

2. Gather forcing and input data.
   - Use `unified-ameriflux-extractor` when a complete AmeriFlux input package is needed.
   - Use `ameriflux-era5-to-ecosim` for hourly climate forcing from AmeriFlux ERA5 CSVs.
   - Use `ameriflux-surgo-grid-extract` for soil/grid variables, with documented fallback if gSSURGO is incomplete.
   - Use `ameriflux-atmchem-info` when atmospheric deposition or precipitation chemistry is needed.
   - Use `ssp-ghg-atmgas-generator` for future or scenario greenhouse-gas forcing; historical-only GHG files are not sufficient for post-2023 SSP runs.

3. Build vegetation or crop management inputs.
   - Use `ecosim-vegetation-code` to map observed vegetation/crops to EcoSIM PFT codes and climate-code suffixes.
   - For natural ecosystems, use `ecosim-natural-plant-mgmt`.
   - For crop sites, construct year-specific planting, harvest, irrigation, fertilization, tillage, and rotation records from the paper, AmeriFlux metadata, supplements, or prior input-paper sources. Do not silently substitute natural-vegetation management for crops.
   - For repeated crop rotations, preserve the paper's calibration/validation years and document any assumed management before the observation period.

4. Prepare or verify plant traits.
   - Use existing crop trait files when they match the target crop and Koppen code.
   - Use `ecosim-plant-trait-sanity-check` on `plant_trait.*.desc` files before running.
   - For new species or unclear PFTs, use `ecosim-trait-deriver` or `plant-trait-target-deriver`, then rerun the sanity check.

5. Create the namelist and run folder.
   - Use `ameriflux-namelist-generator`.
   - For a runnable site case, read and follow `ameriflux-namelist-generator/references/runfolder_workflow.md`.
   - Default run folder layout:

```text
/Users/jinyuntang/work/github/ecosim_workspace/croots/examples/run_dir/<SITE_ID>/
  <SITE_ID>.namelist
  output/
```

6. Validate before running.
   - Confirm grid, climate, PFT management, PFT parameter, atmospheric chemistry, and GHG paths resolve from the run folder.
   - Confirm forcing years cover the simulation chronology.
   - Confirm `delta_time=3600.` for hourly forcing.
   - Confirm output variables include the paper's observational targets.
   - Confirm crop management units, dates, and event ordering are physically plausible.

7. Run EcoSIM when requested.
   - Keep each site/case run folder separate.
   - Save logs and note the executable path or symlink assumption.
   - Do not overwrite prior outputs unless the user asks.

8. Evaluate against observations.
   - Match paper aggregation: daily, seasonal, annual, by crop year, or by soil depth.
   - Check sign conventions, especially `NEE`.
   - Convert EcoSIM output units before comparing to observations.
   - Use the paper's metrics when possible, such as index of agreement `d`, `R2`, `RRMSE`, and `RMD`.
   - Keep calibration data separate from validation data when the paper makes that split.

## Output Contract

When the user asks for paper extraction only, report:

- study citation and DOI if available
- site table with variables and data sources
- unavailable variables or caveats
- exact source citations/DOIs for datasets and method papers

When the user asks for simulation procedures or run folders, also report:

- required EcoSIM input artifacts by site
- existing artifacts found and missing artifacts
- skill chain used to create missing artifacts
- run folder path and namelist path
- forcing year range, spinup assumptions, and output targets
- validation checks completed and unresolved assumptions

## Worked Example: Zhang et al. 2024 MEMS 2 Cropping Paper

For Zhang, King, Hamilton, and Cotrufo (2024), `Representing cropping systems with the MEMS 2 ecosystem model`, Agronomy Journal, DOI `10.1002/agj2.21611`, the paper-reading extraction should identify:

- `US-Ne1`: Mead, Nebraska, irrigated continuous maize. Observations: aboveground biomass, GLAI/LAI, grain yield, NEE, ET, SWC at 10/25/50/100 cm, ST at 4 cm, bulk SOC stock at 0-15 and 15-30 cm in 2001 and 2005. Sources: Suyker (2023a) AmeriFlux `10.17190/AMF/1246084`, Suyker & Verma (2009), Grant et al. (2007), Zhang, Suyker, and Paustian (2018).
- `US-Ne2`: Mead, Nebraska, irrigated maize-soybean rotation, later continuous maize. Same observation classes as `US-Ne1`. Sources: Suyker (2023b) AmeriFlux `10.17190/AMF/1246085`, Suyker & Verma (2009), Grant et al. (2007), Zhang, Suyker, and Paustian (2018).
- `US-Ne3`: Mead, Nebraska, rainfed maize-soybean rotation. Same observation classes as `US-Ne1`. Sources: Suyker (2023c) AmeriFlux `10.17190/AMF/1246086`, Suyker & Verma (2009), Grant et al. (2007), Zhang, Suyker, and Paustian (2018).
- `US-Pon`: Ponca City, Oklahoma, continuous winter wheat. Observations: aboveground biomass and GLAI from destructive measurements; 1997 was used for calibration and remaining data for validation. Sources: Verma (2016) AmeriFlux `10.17190/AMF/1246091`, Hanan et al. (2002), Zhang, Suyker, and Paustian (2018).

Important caveats for this paper:

- POC and MAOC were not measured at the study sites.
- Formal validation beyond biomass/GLAI was limited to the Mead sites.
- SOC was compared but not treated as formal validation because historical management was incomplete.

For EcoSIM simulation of these sites:

- Treat `US-Ne1`, `US-Ne2`, and `US-Ne3` as crop run folders with maize/soybean year-specific management.
- Treat `US-Pon` as winter wheat, and document management assumptions because the paper states detailed Ponca management was lacking.
- Use the AmeriFlux dataset DOIs and Zhang, Suyker, and Paustian (2018) to reconstruct site forcing, management, and calibration/validation windows.
- Include output variables needed to compare against biomass, GLAI/LAI, yield, NEE, ET, SWC by depth, ST, and SOC where available.
