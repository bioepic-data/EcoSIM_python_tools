import numpy as np
from netCDF4 import Dataset
import os,time,sys,argparse
from datetime import datetime
from array import array
import warnings
import stringTools as strtool
import os
warnings.filterwarnings("ignore")



def write_plant_traits(pft_path,gfname,outdir):
    """
    write plant trait files
    """
    pft_names=os.listdir(pft_path)
    
    JLI=4
#pft files are named as pft+koppen_climate_zone
#Bdlf:broadleaf tree (deciduous or evergreen, depending on climate zone)
    pft_name={'alfa':'alfalfa','barl':'barley',
      'bdlf':'broadleaf tree (deciduous or evergreen)',
      'bdln': 'broadleaf tree with N2 fixation',
      'bdlw': 'broadleaf tree adapted to wetland',
      'brom': 'brome',
      'bspr': 'black spruce (needle leaf)',
      'fmos': 'feather moss (with jack pine)',
      'ndlf': 'needleleaf tree (evergreen)',
      'ndld': 'needleleaf tree (deciduous)',
      'gr3s': 'C3 grass perennial',
      'gr4s': 'C4 grass perennial',
      'gr3a': 'C3 grass annual',
      'clva': 'clover annual',
      'clvs': 'clover perennial',
      'bush': 'bush',
      'dfir': 'douglas fir',
      'busn': 'bush with N2 fixation',
      'lpin': 'loblolly pine',
      'maiz': 'maize',
      'oats': 'oats',
      'shru': 'shrub',
      'soyb': 'soybean',
      'swhe': 'spring wheat',
      'lich': 'lichen',
      'jpin': 'jackpine',
      'moss': 'moss (sphagnum)',
      'mosf': 'moss (feathermoss)',      
      'smos': 'moss (sphagnum near sedge)',
      'sedg': 'sedge',
      'tasp': 'aspen',
      'woak': 'oak (upland)'}

    koppenDict_no = {
      "Af":"11",
      "Am":"12",
      "As":"13",
      "Aw":"14",
      "BWk":"21",
      "BWh":"22",
      "BSk":"26",
      "BSh":"27",
      "Cfa":"31",
      "Cfb":"32",
      "Cfc":"33",
      "Csa":"34",
      "Csb":"35",
      "Csc":"36",
      "Cwa":"37",
      "Cwb":"38",
      "Cwc":"39",
      "Dfa":"41",
      "Dfb":"42",
      "Dfc":"43",
      "Dfd":"44",
      "Dsa":"45",
      "Dsb":"46",
      "Dsc":"47",
      "Dsd":"48",
      "Dwa":"49",
      "Dwb":"50",
      "Dwc":"51",
      "Dwd":"52",
      "ET":"61",
      "EF":"62"
    }

    koppenDict_clim = {
      "Af":  "Tropical rainforest climate",
      "Am":  "Tropical monsoon climate",
      "As":  "Tropical summer-dry climate",
      "Aw":  "Tropical winter-dry climate",
      "BWk": "Cold desert climate",
      "BWh": "Hot desert climate",
      "BSk": "Cold semi-arid climate",
      "BSh": "Hot semi-arid climate",
      "Cfa": "Humid subtropical climate",
      "Cfb": "Temperate oceanic climate",
      "Cfc": "Subpolar oceanic climate",
      "Csa": "Hot-summer Mediterranean climate",
      "Csb": "Warm-summer Mediterranean climate",
      "Csc": "Cold-summer Mediterranean climate",
      "Cwa": "Monsoon-influenced humid subtropical climate",
      "Cwb": "Subtropical highland climate",
      "Cwc": "Cold subtropical highland climate",
      "Dfa": "Hot-summer humid continental climate",
      "Dfb": "Warm-summer humid continental climate",
      "Dfc": "Subarctic climate",
      "Dfd": "Extremely cold subarctic climate",
      "Dsa": "Mediterranean-influenced hot-summer humid continental climate",
      "Dsb": "Mediterranean-influenced warm-summer humid continental climate",
      "Dsc": "Mediterranean-influenced subarctic climate",
      "Dsd": "Mediterranean-influenced extremely cold subarctic climate",
      "Dwa": "Monsoon-influenced hot-summer humid continental climate",
      "Dwb": "Monsoon-influenced warm-summer humid continental climate",
      "Dwc": "Monsoon-influenced subarctic climate",
      "Dwd": "Monsoon-influenced extremely cold subarctic climate",
      "ET": "Tundra climate",
      "EF": "Ice cap climate"
    }

    npfts=len(pft_names)

#pft_names=['alfa43','barl43','bdlf11','bdlf31','bdlf32','bdlf43',
#'bdlf61','bdlf62','bdln32','bdln43','bdlw62','brom43',
#'bspr43','bspr62','bush11','bush26','bush31','bush32','bush43',
#'busn26','busn31','busn32','busn43','clva35',
#'clvs35','dfir32','fmos43','gr3a35','gr3s26','gr3s32','gr3s33',
#'gr3s35','gr3s61','gr3s62','gr4s26','jpin43','lich32','lich33',
#'lich61','lich62','maiz31','lpin31',
#'maiz33','mosf43','moss43','moss32','moss33','moss61','moss62',
#'ndlf31','ndlf32','ndlf33','ndlf35','ndlf43','ndlf61','ndlf62','oats43',
#'sedg61','sedg62','shru35','smos61','soyb31','soyb33','swhe33','swhe43',
#'tasp43','woak31']

    ICTYP=np.zeros(npfts,dtype=np.int8)
    IGTYP=np.zeros(npfts,dtype=np.int8)
    ISTYP=np.zeros(npfts,dtype=np.int8)
    IDTYP=np.zeros(npfts,dtype=np.int8)
    INTYP=np.zeros(npfts,dtype=np.int8)
    IWTYP=np.zeros(npfts,dtype=np.int8)
    IPTYP=np.zeros(npfts,dtype=np.int8)
    IBTYP=np.zeros(npfts,dtype=np.int8)
    IRTYP=np.zeros(npfts,dtype=np.int8)
    MY=np.zeros(npfts,dtype=np.int8)
    ZTYPI=np.zeros(npfts,dtype=np.float32)

    VCMX=np.zeros(npfts,dtype=np.float32)
    VOMX=np.zeros(npfts,dtype=np.float32)
    VCMX4=np.zeros(npfts,dtype=np.float32)
    XKCO2=np.zeros(npfts,dtype=np.float32)
    XKO2=np.zeros(npfts,dtype=np.float32)
    XKCO24=np.zeros(npfts,dtype=np.float32)
    RUBP=np.zeros(npfts,dtype=np.float32)
    PEPC=np.zeros(npfts,dtype=np.float32)
    ETMX=np.zeros(npfts,dtype=np.float32)
    CHL=np.zeros(npfts,dtype=np.float32)
    CHL4=np.zeros(npfts,dtype=np.float32)
    FCO2=np.zeros(npfts,dtype=np.float32)

    ALBR=np.zeros(npfts,dtype=np.float32)
    ALBP=np.zeros(npfts,dtype=np.float32)
    TAUR=np.zeros(npfts,dtype=np.float32)
    TAUP=np.zeros(npfts,dtype=np.float32)

    XRNI=np.zeros(npfts,dtype=np.float32)
    XRLA=np.zeros(npfts,dtype=np.float32)
    CTC=np.zeros(npfts,dtype=np.float32)
    VRNLI=np.zeros(npfts,dtype=np.float32)
    VRNXI=np.zeros(npfts,dtype=np.float32)
    WDLF=np.zeros(npfts,dtype=np.float32)
    PB=np.zeros(npfts,dtype=np.float32)

    GROUPX=np.zeros(npfts,dtype=np.float32)
    XTLI=np.zeros(npfts,dtype=np.float32)
    XDL=np.zeros(npfts,dtype=np.float32)
    XPPD=np.zeros(npfts,dtype=np.float32)

    SLA1=np.zeros(npfts,dtype=np.float32)
    SSL1=np.zeros(npfts,dtype=np.float32)
    SNL1=np.zeros(npfts,dtype=np.float32)

    CLASS=np.zeros((npfts,JLI),dtype=np.float32)
    CFI=np.zeros(npfts,dtype=np.float32)
    ANGBR=np.zeros(npfts,dtype=np.float32)
    ANGSH=np.zeros(npfts,dtype=np.float32)

    STMX=np.zeros(npfts,dtype=np.float32)
    SDMX=np.zeros(npfts,dtype=np.float32)
    GRMX=np.zeros(npfts,dtype=np.float32)
    GRDM=np.zeros(npfts,dtype=np.float32)
    GFILL=np.zeros(npfts,dtype=np.float32)
    WTSTDI=np.zeros(npfts,dtype=np.float32)

    RRAD1M=np.zeros(npfts,dtype=np.float32)
    RRAD2M=np.zeros(npfts,dtype=np.float32)
    PORT=np.zeros(npfts,dtype=np.float32)
    PR=np.zeros(npfts,dtype=np.float32)
    RSRR=np.zeros(npfts,dtype=np.float32)
    RSRA=np.zeros(npfts,dtype=np.float32)
    PTSHT=np.zeros(npfts,dtype=np.float32)
    RTFQ=np.zeros(npfts,dtype=np.float32)

    UPMXZH=np.zeros(npfts,dtype=np.float32)
    UPKMZH=np.zeros(npfts,dtype=np.float32)
    UPMNZH=np.zeros(npfts,dtype=np.float32)

    UPMXZO=np.zeros(npfts,dtype=np.float32)
    UPKMZO=np.zeros(npfts,dtype=np.float32)
    UPMNZO=np.zeros(npfts,dtype=np.float32)

    UPMXPO=np.zeros(npfts,dtype=np.float32)
    UPKMPO=np.zeros(npfts,dtype=np.float32)
    UPMNPO=np.zeros(npfts,dtype=np.float32)

    OSMO=np.zeros(npfts,dtype=np.float32)
    RCS=np.zeros(npfts,dtype=np.float32)
    RSMX=np.zeros(npfts,dtype=np.float32)

    DMLF=np.zeros(npfts,dtype=np.float32)
    DMSHE=np.zeros(npfts,dtype=np.float32)
    DMSTK=np.zeros(npfts,dtype=np.float32)
    DMRSV=np.zeros(npfts,dtype=np.float32)
    DMHSK=np.zeros(npfts,dtype=np.float32)
    DMEAR=np.zeros(npfts,dtype=np.float32)
    DMGR=np.zeros(npfts,dtype=np.float32)
    DMRT=np.zeros(npfts,dtype=np.float32)
    DMND=np.zeros(npfts,dtype=np.float32)

    CNLF=np.zeros(npfts,dtype=np.float32)
    CNSHE=np.zeros(npfts,dtype=np.float32)
    CNSTK=np.zeros(npfts,dtype=np.float32)
    CNRSV=np.zeros(npfts,dtype=np.float32)
    CNHSK=np.zeros(npfts,dtype=np.float32)
    CNEAR=np.zeros(npfts,dtype=np.float32)
    CNGR=np.zeros(npfts,dtype=np.float32)
    CNRT=np.zeros(npfts,dtype=np.float32)
    CNND=np.zeros(npfts,dtype=np.float32)

    CPLF=np.zeros(npfts,dtype=np.float32)
    CPSHE=np.zeros(npfts,dtype=np.float32)
    CPSTK=np.zeros(npfts,dtype=np.float32)
    CPRSV=np.zeros(npfts,dtype=np.float32)
    CPHSK=np.zeros(npfts,dtype=np.float32)
    CPEAR=np.zeros(npfts,dtype=np.float32)
    CPGR=np.zeros(npfts,dtype=np.float32)
    CPRT=np.zeros(npfts,dtype=np.float32)
    CPND=np.zeros(npfts,dtype=np.float32)

    varname_dict={
    'ICTYP':'photosynthesis type:C3 or C4:none:i1',
    'IGTYP':'root profile:0=shallow (eg bryophytes),1=intermediate(eg herbs),2=deep (eg trees):none:i1',
    'ISTYP':'growth habit:0=annual,1=perennial:none:i1',
    'IDTYP':'growth habit:0=determinate,1=indetermimate:none:i1',
    'INTYP':'N2 fixation:1,2,3=rapid to slow root symbiosis (e.g.legumes),4,5,6=rapid to slow canopy symbiosis (e.g. cyanobacteria):none:i1',
    'IWTYP':'phenology type:0=evergreen,1=cold deciduous,2=drought deciduous,3=1+2:none:i1',
    'IPTYP':'photoperiod type:0=day neutral,1=short day,2=long day:none:i1',
    'IBTYP':'turnover of aboveground biomass:0,1=rapid(fully deciduous),2=very slow(needle evergreen),3=(broadleaf evergreen),4=slow(semi-deciduous),5=(semi-evergreen):none:i1',
    'IRTYP':'storage organ:0=above ground,1=below ground:none:i1',
    'MY':'mycorrhizal:1=no,2=yes:none:i1',
    'ZTYPI':'thermal adaptation zone:1=arctic,boreal,2=cool temperate:none:f4',
    'VCMX':'specific C3 rubisco carboxylase:umol C g-1 s-1:f4',
    'VOMX':'specific rubisco oxygenase activity:umol O g-1 s-1:f4',
    'VCMX4':'specific PEP carboxylase activity:umol g-1 s-1:f4',
    'XKCO2':'Km for VCMX:uM:f4',
    'XKO2':'Km for VOMX:uM:f4',
    'XKCO24':'Km for VCMX4:uM:f4',
    'RUBP':'fraction of leaf protein in rubisco:none:f4',
    'PEPC':'fraction of leaf protein in PEP carboxylase:none:f4',
    'ETMX':'specific chlorophyll activity:umol e- g-1 s-1:f4',
    'CHL':'fraction of leaf protein in mesophyll(C3) chlorophyll:none:f4',
    'CHL4':'fraction of leaf protein in bundle sheath(C4) chlorophyll:none:f4',
    'FCO2':'intercellular:atmospheric CO2 concentration ratio:none:f4',
    'ALBR':'leaf SW albedo:none:f4',
    'ALBP':'leaf PAR albedo:none:f4',
    'TAUR':'leaf SW transmission:none:f4',
    'TAUP':'leaf PAR transmission:none:f4',
    'XRNI':'rate of node initiation at 25oC:h-1:f4',
    'XRLA':'rate of leaf appearance at 25oC:h-1:f4',
    'CTC':'chilling temperature for CO2 fixation, seed loss:oC:f4',
    'VRNLI':'hour requirement for spring leafout:h:f4',
    'VRNXI':'hour requirement for autumn leafoff:h:f4',
    'WDLF':'leaf length vs width ratio:none:f4',
    'PB':'nonstructural C concentration needed for branching:gC gC-1:f4',
    'GROUPX':'initial plant maturity group, aka minimum number of vegetative nodes initiated before floral:none:f4',
    'XTLI':'node number in seed at planting:none:f4',
    'XDL':'critical daylength for phenological progress:h:f4',
    'XPPD':'photoperiod sensitivity, i.e. difference between current and critical daylengths used to calculate  phenological progress:node h-1:f4',
    'SLA1':'growth in leaf area vs mass:m2 gC-1:f4',
    'SSL1':'growth in petiole length vs mass:m gC-1:f4',
    'SNL1':'growth in internode stalk length vs mass:m gC-1:f4',
    'CLASS':'fraction of leaf area in 0-22.5,45,67.5,90o inclination classes:none:f4',
    'CFI':'initial clumping factor:none:f4',
    'ANGBR':'stem angle from horizontal:degree:f4',
    'ANGSH':'petiole angle from horizontal:degree:f4',
    'STMX':'maximum potential seed mumber from pre-anthesis stalk growth:none:f4',
    'SDMX':'maximum seed number per STMX:none:f4',
    'GRMX':'maximum seed size per SDMX:gC:f4',
    'GRDM':'seed size at planting:gC:f4',
    'GFILL':'grain filling rate at 25 oC:gC seed-1 h-1:f4',
    'WTSTDI':'mass of dead standing biomass at planting:gC m-2:f4',
    'RRAD1M':'radius of primary roots:m:f4',
    'RRAD2M':'radius of secondary roots:m:f4',
    'PORT':'root porosity:m3 m-3:f4',
    'PR':'nonstructural C concentration needed for root branching:gC gC-1:f4',
    'RSRR':'radial root resistivity:m2 MPa-1 h-1:f4',
    'RSRA':'axial root resistivity:m2 MPa-1 h-1:f4',
    'PTSHT':'rate constant for equilibrating shoot-root nonstructural C concentration:h-1:f4',
    'RTFQ':'root branching frequency:m-1:f4',
    'UPMXZH':'NH4 max uptake:g m-2 h-1:f4',
    'UPKMZH':'NH4 uptake Km:uM:f4',#check unit, likely is g/m3
    'UPMNZH':'NH4 uptake minimum conconcentration:uM:f4',#check unit, likely is g/m3
    'UPMXZO':'NO3 max uptake:g m-2 h-1:f4',
    'UPKMZO':'NO3 uptake Km:uM:f4',#check unit, likely is g/m3
    'UPMNZO':'NO3 uptake minimum conconcentration:uM:f4',#check unit, likely is g/m3
    'UPMXPO':'H2PO4 max uptake:gP m-2 h-1:f4',
    'UPKMPO':'H2PO4 uptake Km:uM:f4',#check unit, likely is g/m3
    'UPMNPO':'H2PO4 uptake minimum conconcentration:uM:f4',#check unit, likely is g/m3
    'OSMO':'leaf osmotic potential at zero leaf water potential:MPa:f4',
    'RCS':'shape parameter for stomatal resistance vs leaf turgor potential:none:f4',
    'RSMX':'cuticular resistance:s m-1:f4',
    'DMLF':'leaf dry matter C production vs nonstructural C consumption:gC gC-1:f4',
    'DMSHE':'petiole dry matter C production vs nonstructural C consumption:gC gC-1:f4',
    'DMSTK':'stalk dry matter C production vs nonstructural C consumption:gC gC-1:f4',
    'DMRSV':'stalk reserve C production vs nonstructural C consumption:gC gC-1):f4',
    'DMHSK':'husk dry matter C production vs nonstructural Cconsumption:gC gC-1:f4',
    'DMEAR':'ear dry matter C production vs nonstructural Cconsumption:gC gC-1:f4',
    'DMGR':'grain C production vs nonstructural C consumption:gC gC-1:f4',
    'DMRT':'root dry matter C production vs nonstructural C consumption:gC gC-1:f4',
    'DMND':'nodule bacteria in root nodule,canopy dry matter C production vs nonstructural C consumption:gC gC-1:f4',
    'CNLF':'NC ratio in plant leaves:gN gC-1:f4',
    'CNSHE':'NC ratio in plant petiole:gN gC-1:f4',
    'CNSTK':'NC ratio in plant stalk:gN gC-1:f4',
    'CNRSV':'NC ratio in plant stalk reserve:gN gC-1:f4',
    'CNHSK':'NC ratio in plant husk:gN gC-1:f4',
    'CNEAR':'NC ratio in plant ear:gN gC-1:f4',
    'CNGR':'NC ratio in plant grain:gN gC-1:f4',
    'CNRT':'NC ratio in plant root:gN gC-1:f4',
    'CNND':'NC ratio in plant nodule:gN gC-1:f4',
    'CPLF':'PC ratio in plant leaves:gP gC-1:f4',
    'CPSHE':'PC ratio in plant petiole:gP gC-1:f4',
    'CPSTK':'PC ratio in plant stalk:gP gC-1:f4',
    'CPRSV':'PC ratio in plant stalk reserve:gP gC-1:f4',
    'CPHSK':'PC ratio in plant husk:gP gC-1:f4',
    'CPEAR':'PC ratio in plant ear:gP gC-1:f4',
    'CPGR':'PC ratio in plant grain:gP gC-1:f4',
    'CPRT':'PC ratio in plant root:gP gC-1:f4',
    'CPND':'PC ratio in plant nodule:gP gC-1:f4'
    }
    print('npfts=%d'%npfts)

    for j in range(npfts):
        pfile=pft_path+pft_names[j]
        print('read file %s'%pfile)
        with open(pfile,"r") as pftfile:
            line=pftfile.readline()

#
#  PLANT FUNCTIONAL TYPE
#  ICTYP=photosynthesis type:3=C3,4=C4
#  IGTYP=root profile:0=shallow (eg bryophytes),1=intermediate(eg herbs),2=deep (eg trees)
#  ISTYP=growth habit:0=annual,1=perennial
#  IDTYP=growth habit:0=determinate,1=indetermimate
#  INTYP=N2 fixation:1,2,3=rapid to slow root symbiosis (e.g.legumes),4,5,6=rapid to slow canopy symbiosis (e.g. cyanobacteria)
#  IWTYP=phenology type:0=evergreen,1=cold deciduous,2=drought deciduous,3=1+2
#  IPTYP=photoperiod type:0=day neutral,1=short day,2=long day
#  IBTYP=turnover:if IGTYP=0 or 1:all above-ground:0,1=rapid(deciduous),2=very slow(evergreen),3=slow(semi-deciduous)
#                :if IGTYP=2:trees:1=rapid(deciduous),2=very slow(coniferous),3=slow(semi-deciduous)
#  IRTYP=storage organ:0=above ground,1=below ground
#  MY=mycorrhizal:1=no,2=yes
#  ZTYPI=thermal adaptation zone:1=arctic,boreal,2=cool temperate,3=warm temperate,4=subtropical,5=tropical
#
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            print(x[0])
            ICTYP[j]=int(x[0])
            IGTYP[j]=int(x[1])
            ISTYP[j]=int(x[2])
            IDTYP[j]=int(x[3])
            INTYP[j]=int(x[4])
            IWTYP[j]=int(x[5])
            IPTYP[j]=int(x[6])
            IBTYP[j]=int(x[7])
            IRTYP[j]=int(x[8])
            MY[j]   =int(x[9])
            ZTYPI[j]=float(x[10])

#   PHOTOSYNTHETIC PROPERTIES

#   VCMX,VOMX=specific rubisco carboxylase,oxygenase activity (umol C,O g-1 s-1)
#   VCMX4=specific PEP carboxylase activity (umol g-1 s-1)
#   XKCO2,XKO2,XKCO24=Km for VCMX,VOMX,VCMX4 (uM)
#   RUBP,PEPC=fraction of leaf protein in rubisco, PEP carboxylase
#   ETMX=specific chlorophyll activity (umol e- g-1 s-1)
#   CHL=fraction of leaf protein in mesophyll(C3), bundle sheath(C4) chlorophyll
#   CHL4=fraction of leaf protein in mesophyll chlorophyll(C4)
#   FCO2=intercellular:atmospheric CO2 concentration ratio

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            VCMX[j]=float(x[0])
            VOMX[j]=float(x[1])
            VCMX4[j]=float(x[2])
            XKCO2[j]=float(x[3])
            XKO2[j]=float(x[4])
            XKCO24[j]=float(x[5])
            RUBP[j]=float(x[6])
            PEPC[j]=float(x[7])
            ETMX[j]=float(x[8])
            CHL[j]=float(x[9])
            CHL4[j]=float(x[10])
            FCO2[j]=float(x[11])


#   OPTICAL PROPERTIES

#   ALBR,ALBP,TAUR,TAUP=leaf SW,PAR albedo, SW transmission, PAR transmission

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            ALBR[j]=float(x[0])
            ALBP[j]=float(x[1])
            TAUR[j]=float(x[2])
            TAUP[j]=float(x[3])

#   PHENOLOGICAL PROPERTIES

#   XRNI,XRLA=rate of node initiation,leaf appearance at 25oC (h-1)
#   CTC=chilling temperature for CO2 fixation, seed loss (oC)
#   VRNLI,VRNXI=hour requirement for spring leafout,autumn leafoff
#   WDLF=leaf length:width ratio
#   PB=nonstructural C concentration needed for branching
#   GROUPX,XTLI=node number required for floral initiation,at planting
#   XDL=critical photoperiod (h):<0=maximum daylength from site file
#   XPPD=photoperiod sensitivity (node h-1)


            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            XRNI[j]=float(x[0])
            XRLA[j]=float(x[1])
            CTC[j]=float(x[2])
            VRNLI[j]=float(x[3])
            VRNXI[j]=float(x[4])
            WDLF[j]=float(x[5])
            PB[j]=float(x[6])

#   MORPHOLOGICAL PROPERTIES

#   SLA1,SSL1,SNL1=growth in leaf area,petiole length,internode length vs mass
#   CLASS=fraction of leaf area in 0-22.5,45,67.5,90o inclination classes
#   CFI=initial clumping factor
#   ANGBR,ANGSH=stem,petiole angle from horizontal
#   STMX=maximum potential seed mumber from pre-anthesis stalk growth
#   SDMX=maximum seed number per STMX
#   GRMX=maximum seed size per SDMX (g)
#   GRDM=seed size at planting (g)
#   GFILL=grain filling rate at 25 oC (g seed-1 h-1)
#   WTSTDI=mass of dead standing biomass at planting

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            GROUPX[j]=float(x[0])
            XTLI[j]=float(x[1])
            XDL[j]=float(x[2])
            XPPD[j]=float(x[3])

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            SLA1[j]=float(x[0])
            SSL1[j]=float(x[1])
            SNL1[j]=float(x[2])

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            for N in range(JLI):
                  CLASS[j,N]=float(x[N])
            CFI[j]=float(x[JLI])
            ANGBR[j]=float(x[JLI+1])
            ANGSH[j]=float(x[JLI+2])

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            STMX[j]=float(x[0])
            SDMX[j]=float(x[1])
            GRMX[j]=float(x[2])
            GRDM[j]=float(x[3])
            GFILL[j]=float(x[4])
            WTSTDI[j]=float(x[5])

#   ROOT CHARACTERISTICS

#   RRAD1M,RRAD2M=radius of primary,secondary roots
#   PORT=root porosity
#   PR=nonstructural C concentration needed for root branching
#   RSRR,RSRA=radial,axial root resistivity (m2 MPa-1 h-1)
#   PTSHT=rate constant for equilibrating shoot-root nonstructural C concn
#   RTFQ=root branching frequency (m-1)


            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            RRAD1M[j]=float(x[0])
            RRAD2M[j]=float(x[1])
            PORT[j]=float(x[2])
            PR[j]=float(x[3])
            RSRR[j]=float(x[4])
            RSRA[j]=float(x[5])
            PTSHT[j]=float(x[6])
            RTFQ[j]=float(x[7])

#   ROOT UPTAKE PARAMETERS

#   UPMXZH,UPKMZH,UPMNZH=NH4 max uptake (g m-2 h-1),Km (uM), min concn (uM)
#   UPMXZO,UPKMZO,UPMNZO=NO3 max uptake (g m-2 h-1),Km (uM), min concn (uM)
#   UPMXPO,UPKMPO,UPMNPO=H2PO4 max uptake (g m-2 h-1),Km (uM), min concn (uM)

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            UPMXZH[j]=float(x[0])
            UPKMZH[j]=float(x[1])
            UPMNZH[j]=float(x[2])

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            UPMXZO[j]=float(x[0])
            UPKMZO[j]=float(x[1])
            UPMNZO[j]=float(x[2])

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            UPMXPO[j]=float(x[0])
            UPKMPO[j]=float(x[1])
            UPMNPO[j]=float(x[2])

#   WATER RELATIONS

#   OSMO=leaf osmotic potential at zero leaf water potential (MPa)
#   RCS=shape parameter for stomatal resistance vs leaf turgor potential
#   RSMX=cuticular resistance (s m-1)

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            OSMO[j]=float(x[0])
            RCS[j]=float(x[1])
            RSMX[j]=float(x[2])


#   ORGAN GROWTH YIELDS
#   DM*=DM-C production vs nonstructural C consumption (g g-1)
#     *LF=leaf,*SHE=petiole,*STK=stalk,*RSV=stalk reserve,*HSK=husk
#     *EAR=ear,*GR=grain,*RT=root,*ND=bacteria in root nodule,canopy

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()

            DMLF[j]=float(x[0])
            DMSHE[j]=float(x[1])
            DMSTK[j]=float(x[2])
            DMRSV[j]=float(x[3])
            DMHSK[j]=float(x[4])
            DMEAR[j]=float(x[5])
            DMGR[j]=float(x[6])
            DMRT[j]=float(x[7])
            DMND[j]=float(x[8])

#   ORGAN N AND P CONCENTRATIONS
#   CN*,CP*=N:C,P:C ratios in plant organs

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            CNLF[j]=float(x[0])
            CNSHE[j]=float(x[1])
            CNSTK[j]=float(x[2])
            CNRSV[j]=float(x[3])
            CNHSK[j]=float(x[4])
            CNEAR[j]=float(x[5])
            CNGR[j]=float(x[6])
            CNRT[j]=float(x[7])
            CNND[j]=float(x[8])

            line=pftfile.readline()
            if ',' in line:
                x=line.split(',')
            else:
                x=line.split()
            CPLF[j]=float(x[0])
            CPSHE[j]=float(x[1])
            CPSTK[j]=float(x[2])
            CPRSV[j]=float(x[3])
            CPHSK[j]=float(x[4])
            CPEAR[j]=float(x[5])
            CPGR[j]=float(x[6])
            CPRT[j]=float(x[7])
            CPND[j]=float(x[8])

#write pft file
    current_dateTime = datetime.now()
    nc_f='%s%s_pftpar_%4d%02d%02d.nc'%(outdir,gfname,current_dateTime.year,current_dateTime.month,current_dateTime.day)
    nc_fid = Dataset(nc_f, 'w')

    nc_fid.description='plant trait parameterization for ecosim created on %4d/%02d/%02d/%02d:%02d:%02d'% \
      (current_dateTime.year,current_dateTime.month,current_dateTime.day, \
      current_dateTime.hour,current_dateTime.minute,current_dateTime.second)
    nkopclims=len(koppenDict_no)
    nc_fid.createDimension('npfts', None)
    nc_fid.createDimension('JLI', JLI)
    nc_fid.createDimension('nchars1',10)
    nc_fid.createDimension('nchars2',4)
    nc_fid.createDimension('nkopenclms',nkopclims)
    nchars3=40
    nc_fid.createDimension('nchars3',nchars3)
    nchars4=2
    nc_fid.createDimension('nchars4',nchars4)
    nchars5=3
    nc_fid.createDimension('nchars5',nchars5)
    nchars6=64
    nc_fid.createDimension('nchars6',nchars6)

    nc_fid.createDimension('npft',len(pft_name))
    for v in varname_dict:
        ss=strtool.split_var(varname_dict[v])
        if len(ss)==4:
            long_name,flags,units,dtype=ss
        else:
            flags=''
            long_name,units,dtype=ss
        if v != 'CLASS':
            w_nc_var = nc_fid.createVariable(v, dtype, ('npfts'))
        else:
            w_nc_var = nc_fid.createVariable(v, dtype, ('npfts','JLI'))
        w_nc_var.long_name=long_name
        w_nc_var.units=units
        if flags:
            w_nc_var.flags=flags
    w_nc_var = nc_fid.createVariable('pfts', 'S1', ('npfts','nchars1'))

    for ll in range(npfts):
        print('pft[%d]=%10s'%(ll,pft_names[ll]))
        w_nc_var[ll,:]=strtool.string2arr(pft_names[ll],10)


    w_nc_var = nc_fid.createVariable('pfts_short', 'S1', ('npft','nchars2'))
    w_nc_var1 = nc_fid.createVariable('pfts_long', 'S1', ('npft','nchars3'))

    ll=0
    for v in pft_name:
        w_nc_var[ll,:]=strtool.string2arr(v)
        w_nc_var1[ll,:]=strtool.string2arr(pft_name[v],nchars3)
        ll=ll+1
    w_nc_var = nc_fid.createVariable('koppen_clim_no', 'S1', ('nkopenclms','nchars4'))
    w_nc_var1 = nc_fid.createVariable('koppen_clim_short', 'S1', ('nkopenclms','nchars5'))
    w_nc_var2 = nc_fid.createVariable('koppen_clim_long', 'S1', ('nkopenclms','nchars6'))

    ll=0
    for v in koppenDict_no:
        w_nc_var1[ll,:]=strtool.string2arr(v,nchars5)
        w_nc_var[ll,:]=strtool.string2arr(koppenDict_no[v],nchars4)
        w_nc_var2[ll,:]=strtool.string2arr(koppenDict_clim[v],nchars6)
        ll=ll+1

    nc_fid.variables['ICTYP'][:]=ICTYP
    nc_fid.variables['IGTYP'][:]=IGTYP
    nc_fid.variables['ISTYP'][:]=ISTYP
    nc_fid.variables['IDTYP'][:]=IDTYP
    nc_fid.variables['INTYP'][:]=INTYP
    nc_fid.variables['IWTYP'][:]=IWTYP
    nc_fid.variables['IPTYP'][:]=IPTYP
    nc_fid.variables['IBTYP'][:]=IBTYP
    nc_fid.variables['IRTYP'][:]=IRTYP
    nc_fid.variables['MY'][:]=MY
    nc_fid.variables['ZTYPI'][:]=ZTYPI

    nc_fid.variables['VCMX'][:]=VCMX
    nc_fid.variables['VOMX'][:]=VOMX
    nc_fid.variables['VCMX4'][:]=VCMX4
    nc_fid.variables['XKCO2'][:]=XKCO2
    nc_fid.variables['XKO2'][:]=XKO2
    nc_fid.variables['XKCO24'][:]=XKCO24
    nc_fid.variables['RUBP'][:]=RUBP
    nc_fid.variables['PEPC'][:]=PEPC
    nc_fid.variables['ETMX'][:]=ETMX
    nc_fid.variables['CHL'][:]=CHL
    nc_fid.variables['CHL4'][:]=CHL4
    nc_fid.variables['FCO2'][:]=FCO2

    nc_fid.variables['ALBR'][:]=ALBR
    nc_fid.variables['ALBP'][:]=ALBP
    nc_fid.variables['TAUR'][:]=TAUR
    nc_fid.variables['TAUP'][:]=TAUP

    nc_fid.variables['XRNI'][:]=XRNI
    nc_fid.variables['XRLA'][:]=XRLA
    nc_fid.variables['CTC'][:]=CTC
    nc_fid.variables['VRNLI'][:]=VRNLI
    nc_fid.variables['VRNXI'][:]=VRNXI
    nc_fid.variables['WDLF'][:]=WDLF
    nc_fid.variables['PB'][:]=PB

    nc_fid.variables['GROUPX'][:]=GROUPX
    nc_fid.variables['XTLI'][:]=XTLI
    nc_fid.variables['XDL'][:]=XDL
    nc_fid.variables['XPPD'][:]=XPPD

    nc_fid.variables['SLA1'][:]=SLA1
    nc_fid.variables['SSL1'][:]=SSL1
    nc_fid.variables['SNL1'][:]=SNL1

    nc_fid.variables['CLASS'][:]=CLASS
    nc_fid.variables['CFI'][:]=CFI
    nc_fid.variables['ANGBR'][:]=ANGBR
    nc_fid.variables['ANGSH'][:]=ANGSH

    nc_fid.variables['STMX'][:]=STMX
    nc_fid.variables['SDMX'][:]=SDMX
    nc_fid.variables['GRMX'][:]=GRMX
    nc_fid.variables['GRDM'][:]=GRDM
    nc_fid.variables['GFILL'][:]=GFILL
    nc_fid.variables['WTSTDI'][:]=WTSTDI

    nc_fid.variables['RRAD1M'][:]=RRAD1M
    nc_fid.variables['RRAD2M'][:]=RRAD2M
    nc_fid.variables['PORT'][:]=PORT
    nc_fid.variables['PR'][:]=PR
    nc_fid.variables['RSRR'][:]=RSRR
    nc_fid.variables['RSRA'][:]=RSRA
    nc_fid.variables['PTSHT'][:]=PTSHT
    nc_fid.variables['RTFQ'][:]=RTFQ

    nc_fid.variables['UPMXZH'][:]=UPMXZH
    nc_fid.variables['UPKMZH'][:]=UPKMZH
    nc_fid.variables['UPMNZH'][:]=UPMNZH

    nc_fid.variables['UPMXZO'][:]=UPMXZO
    nc_fid.variables['UPKMZO'][:]=UPKMZO
    nc_fid.variables['UPMNZO'][:]=UPMNZO

    nc_fid.variables['UPMXPO'][:]=UPMXPO
    nc_fid.variables['UPKMPO'][:]=UPKMPO
    nc_fid.variables['UPMNPO'][:]=UPMNPO

    nc_fid.variables['OSMO'][:]=OSMO
    nc_fid.variables['RCS'][:]=RCS
    nc_fid.variables['RSMX'][:]=RSMX

    nc_fid.variables['DMLF'][:]=DMLF
    nc_fid.variables['DMSHE'][:]=DMSHE
    nc_fid.variables['DMSTK'][:]=DMSTK
    nc_fid.variables['DMRSV'][:]=DMRSV
    nc_fid.variables['DMHSK'][:]=DMHSK
    nc_fid.variables['DMEAR'][:]=DMEAR
    nc_fid.variables['DMGR'][:]=DMGR
    nc_fid.variables['DMRT'][:]=DMRT
    nc_fid.variables['DMND'][:]=DMND

    nc_fid.variables['CNLF'][:]=CNLF
    nc_fid.variables['CNSHE'][:]=CNSHE
    nc_fid.variables['CNSTK'][:]=CNSTK
    nc_fid.variables['CNRSV'][:]=CNRSV
    nc_fid.variables['CNHSK'][:]=CNHSK
    nc_fid.variables['CNEAR'][:]=CNEAR
    nc_fid.variables['CNGR'][:]=CNGR
    nc_fid.variables['CNRT'][:]=CNRT
    nc_fid.variables['CNND'][:]=CNND

    nc_fid.variables['CPLF'][:]=CPLF
    nc_fid.variables['CPSHE'][:]=CPSHE
    nc_fid.variables['CPSTK'][:]=CPSTK
    nc_fid.variables['CPRSV'][:]=CPRSV
    nc_fid.variables['CPHSK'][:]=CPHSK
    nc_fid.variables['CPEAR'][:]=CPEAR
    nc_fid.variables['CPGR'][:]=CPGR
    nc_fid.variables['CPRT'][:]=CPRT
    nc_fid.variables['CPND'][:]=CPND

    nc_fid.close()  # close the new file

#pft_path='/Users/jinyuntang/work/github/ecosys_benchmark/spruce_PQ_3PFT_s1/pfts/'
#pft_path='/Users/jinyuntang/work/github/ecosys_benchmark/Blodget/pfts/'
#pft_path='/Users/jinyuntang/work/github/ecosys_benchmark/sorghum/plt_sorg/pfts/'
#pft_path='/Users/jinyuntang/work/github/ecosys_benchmark/plmrEcosys/pfts/'
#pft_names=os.listdir(pft_path)

#write_plant_traits(pft_names,pft_path,'blodgett')
