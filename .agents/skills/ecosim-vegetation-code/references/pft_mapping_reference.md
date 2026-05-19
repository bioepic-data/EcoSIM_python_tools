# EcoSIM PFT Mapping Reference

Use `templates/ecosim_pftpar_20260303.nc.cdl` as authoritative. In that file, `pfts` contains valid six-character EcoSIM vegetation codes. Each code is `pfts_short` plus a two-digit `koppen_clim_no`.

## PFT Short Codes

| pfts_short | pfts_long |
| --- | --- |
| alfa | alfalfa crop |
| barl | barley crop |
| bdlf | broadleaf tree (deciduous or evergreen) |
| bdln | broadleaf tree with N2 fixation |
| bdlw | broadleaf tree adapted to wetland |
| brom | brome grass |
| bspr | black spruce tree (needle leaf) |
| fmos | feather moss (with jack pine) |
| ndlf | needleleaf tree (evergreen) |
| ndld | needleleaf tree (deciduous) |
| gr3s | C3 grass perennial |
| gr4s | C4 grass perennial |
| gr3a | C3 grass annual |
| clva | clover annual crop |
| clvs | clover perennial crop |
| bush | bush tree |
| dfir | douglas fir tree |
| busn | bush tree with N2 fixation |
| lpin | loblolly pine tree |
| maiz | maize crop |
| oats | oats crop |
| rice | rice crop |
| shru | shrub tree |
| soyb | soybean crop |
| swhe | spring wheat crop |
| lich | lichen |
| jpin | jackpine tree |
| moss | moss (sphagnum) |
| mosf | moss (feathermoss) |
| smos | moss (sphagnum near sedge) |
| sedg | sedge grass |
| tasp | aspen tree |
| woak | oak tree (upland) |
| dgra | deer grass |
| woat | wild oats |

## Koppen Numerical Codes

| koppen_clim_no | koppen_clim_short | koppen_clim_long |
| --- | --- | --- |
| 11 | Af | Tropical rainforest climate |
| 12 | Am | Tropical monsoon climate |
| 13 | As | Tropical summer-dry climate |
| 14 | Aw | Tropical winter-dry climate |
| 21 | BWk | Cold desert climate |
| 22 | BWh | Hot desert climate |
| 26 | BSk | Cold semi-arid climate |
| 27 | BSh | Hot semi-arid climate |
| 31 | Cfa | Humid subtropical climate |
| 32 | Cfb | Temperate oceanic climate |
| 33 | Cfc | Subpolar oceanic climate |
| 34 | Csa | Hot-summer Mediterranean climate |
| 35 | Csb | Warm-summer Mediterranean climate |
| 36 | Csc | Cold-summer Mediterranean climate |
| 37 | Cwa | Monsoon-influenced humid subtropical climate |
| 38 | Cwb | Subtropical highland climate |
| 39 | Cwc | Cold subtropical highland climate |
| 41 | Dfa | Hot-summer humid continental climate |
| 42 | Dfb | Warm-summer humid continental climate |
| 43 | Dfc | Subarctic climate |
| 44 | Dfd | Extremely cold subarctic climate |
| 45 | Dsa | Mediterranean-influenced hot-summer humid continental climate |
| 46 | Dsb | Mediterranean-influenced warm-summer humid continental climate |
| 47 | Dsc | Mediterranean-influenced subarctic climate |
| 48 | Dsd | Mediterranean-influenced extremely cold subarctic climate |
| 49 | Dwa | Monsoon-influenced hot-summer humid continental climate |
| 50 | Dwb | Monsoon-influenced warm-summer humid continental climate |
| 51 | Dwc | Monsoon-influenced subarctic climate |
| 52 | Dwd | Monsoon-influenced extremely cold subarctic climate |
| 61 | ET | Tundra climate |
| 62 | EF | Ice cap climate |

## Output Pattern

Prefer this table when answering mapping requests:

| Site vegetation | pfts_short | pfts_long | Koppen | EcoSIM code | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |

Use `Status=exact` only when the code is present in `pfts`. Use `Status=missing` when the short-code plus Koppen combination is not present; list available alternatives for that short code.
