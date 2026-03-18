import numpy as np
import numpy as np
from netCDF4 import Dataset
import os,time,sys,argparse
from datetime import datetime
from array import array
import stringTools as strtool
import warnings
warnings.filterwarnings("ignore")


grid_info={
'ALATG':'Latitude:degrees north:f4',
'ALTIG':'Altitude above sea-level:m:f4',
'ATCAG':'Mean annual temperaure:oC:f4',
'IDTBLG':'Water table flag:0=No water table,1=Natural stationary water table,2=Natural mobile water table,' \
  '3=Artificial stationary water table,4=Artificial mobile water table:none:i1',
'OXYEG':'Atmospheric O2:ppm:f4',
'Z2GEG' :'Atmospheric N2:ppm:f4',
'CO2EIG':'Atmospheric CO2:ppm:f4',
'CH4EG' :'Atmospheric CH4:ppm:f4',
'Z2OEG' :'Atmospheric N2O:ppm:f4',
'ZNH3EG':'Atmospheric NH3:ppm:f4',
'IETYPG':'Koppen climate zone:none:i1',
'DTBLIG':'Depth of natural water table:m:f4',
'DTBLDIG':'Depth of artificial water table:m:f4',
'DTBLGG':'Slope of natural water table relative to landscape surface:none:f4',
'RCHQNG':'Boundary condition for North surface runoff:varying between 0 and 1:none:f4',
'RCHQEG':'Boundary condition for East surface runoff:varying between 0 and 1:none:f4',
'RCHQSG':'Boundary condition for S surface runoff:varying between 0 and 1:none:f4',
'RCHQWG':'Boundary condition for W surface runoff:varying between 0 and 1:none:f4',
'RCHGNUG':'Bound condition for N subsurf flow:none:f4',
'RCHGEUG':'Bound condition for E subsurf flow:none:f4',
'RCHGSUG':'Bound condition for S subsurf flow:none:f4',
'RCHGWUG':'Bound condition for W subsurf flow:none:f4',
'RCHGNTG':'North edge distance to water table:m:f4',
'RCHGETG':'East edge distance to water table:m:f4',
'RCHGSTG':'South edge distance to water table:m:f4',
'RCHGWTG':'West edge distance to water table:m:f4',
'RCHGDG':'Lower boundary conditions for water flow:varying between 0 and 1:none:f4',
'DHI':'Width of each W-E landscape column:m:f4',#(DHI(NX),NX=1,NHE)
'DVI':'Width of each N-S landscape row:m:f4' #(DVI(NY),NY=1,NVS)
}

# the model is organized by landscape, under which is the top unit, which may
# be made up of several columns

topo_unit_info={
'NH1':'Starting column from the west:none:i1:0d',
'NH2':'Ending column at the east:none:i1:0d',
'NV1':'Starting row from the north:none:i1:0d',
'NV2':'Ending row at the south:none:i1:0d',
'ASPX':'Aspect:degrees:f4:0d',
'SL0':'Slope:degrees:f4:0d',
'DPTHSX':'Initial snowpack depth:m:f4:0d',
'PSIFC':'Water potential at field capacity:MPa:f4:0d',
'PSIWP':'Water potential at wilting point:MPa:f4:0d',
'ALBS':'Wet soil albedo:none:f4:0d',
'PH0':'Litter pH:none:f4:0d',
'RSCf':'C in surface fine litter:gC m-2:f4:0d',
'RSNf':'N in surface fine litter:gN m-2:f4:0d',
'RSPf':'P in surface fine litter:gP m-2:f4:0d',
'RSCw':'C in surface woody litter:gC m-2:f4:0d',
'RSNw':'N in surface woody litter:gN m-2:f4:0d',
'RSPw':'P in surface woody litter:gP m-2:f4:0d',
'RSCm':'C in manure:gC m-2:f4:0d',
'RSNm':'N in manure:gN m-2:f4:0d',
'RSPm':'P in manure:gP m-2:f4:0d',
'IXTYP1':'plant surface fine litter type:1=maize,2=wheat,3=soybean,4=new straw,5=old straw,' \
    '6=compost,7=green manure,8=new deciduos forest,9=new coniferous forest,' \
    '10=old deciduous forest,11=old coniferous forest,12=default:none:i1:0d',
'IXTYP2':'manure surface litter type:1=ruminant,2=non ruminant,3=others:none:i1:0d',
'NUI':'Initial layer number of soil surface layer:usually is 1:none:i1:0d',
'NJ':'Layer number of maximum rooting layer:none:i1:0d',
'NL1':'Number of additional layers below NJ with data in file:none:i1:0d',
'NL2':'Number of additional layers below NJ without data in file:none:i1:0d',
'ISOILR':'Flag for soil profile type:0=natural,1=reconstructed:none:i1:0d',
'CDPTH':'Depth to bottom of soil layer:m:f4:1d',#1d array
'BKDSI':'Initial bulk density:0 for water:Mg m-3:f4:1d',#1d array
'FC':'Field capacity:m3 m-3:f4:1d',#1d array
'WP':'Wilting point:m3 m-3:f4:1d',#1d array
'SCNV':'Vertical hydraulic conductivity Ksat:mm h-1:f4:1d',#1d array
'SCNH':'Lateral hydraulic conductivity Ksat:mm h-1:f4:1d',#1d array
'CSAND':'Sand content:kg Mg-1:f4:1d',#1d array
'CSILT':'Silt content:kg Mg-1:f4:1d',#1d array
'FHOL':'Macropore fraction in the non-rock fraction of soil:0-1:none:f4:1d',#1d array
'ROCK':'Rock fraction of the whole soil:0-1:none:f4:1d',#1d array
'PH':'depth-resolved pH:none:f4:1d',#1d array
'CEC':'Cation exchange capacity:cmol kg soil-1:f4:1d',#1d array, cmol kg-1=meq/100g
'AEC':'Anion exchange capacity:cmol kg soil-1:f4:1d',#1d array
'CORGC':'Total soil organic carbon:kg C/Mg soil:f4:1d',#1d array
'CORGR':'POC (part of SOC):kg C/Mg soil:f4:1d',#1d array
'CORGN':'Total soil organic nitrogen:g N/Mg soil:f4:1d',#1d array
'CORGP':'Total soil organic phosphorus:g P/Mg soil:f4:1d',#1d array
'CNH4':'Total soil NH4 concentration:gN/Mg soil:f4:1d',#1d array
'CNO3':'Total soil NO3 concentration:gN/Mg soil:f4:1d',#1d array
'CPO4':'Total soil H2PO4 concentration:gP/Mg soil:f4:1d',#1d array
'CAL':'Soluble soil Al content:g Al/Mg soil:f4:1d',#1d array
'CFE':'Soluble soil Fe content:g Fe/Mg soil:f4:1d',#1d array
'CCA':'Soluble soil Ca content:g Ca/Mg soil:f4:1d',#1d array
'CMG':'Soluble soil MG content:g MG/Mg soil:f4:1d',#1d array
'CNA':'Soluble soil Na content:g Na/Mg soil:f4:1d',#1d array
'CKA':'Soluble soil K content:g K/Mg soil:f4:1d',#1d array
'CSO4':'Soluble soil SO4 content:g S/Mg soil:f4:1d',#1d array
'CCL':'Soluble soil Cl content:g Cl/Mg soil:f4:1d',#1d array
'CALPO':'Soil AlPO4 content:g P/Mg soil:f4:1d',#1d array
'CFEPO':'Soil FePO4 content:g P/Mg soil:f4:1d',#1d array
'CCAPD':'Soil CaHPO4 content:g P/Mg soil:f4:1d',#1d array
'CCAPH':'Soil apatite content:g P/Mg soil:f4:1d',#1d array
'CALOH':'Soil Al(OH)3 content:g Al/Mg soil:f4:1d',#1d array
'CFEOH':'Soil Fe(OH)3 content:g Fe/Mg soil:f4:1d',#1d array
'CCACO':'Soil CaCO3 content:g Ca/Mg soil:f4:1d',#1d array
'CCASO':'Soil CaSO4 content:g Ca/Mg soil:f4:1d',#1d array
'GKC4':'Ca-NH4 Gapon selectivity coefficient:none:f4:1d',#1d array
'GKCH':'Ca-H Gapon selectivity coefficient:none:f4:1d',#1d array
'GKCA':'Ca-Al Gapon selectivity coefficient:none:f4:1d',#1d array
'GKCM':'Ca-Mg Gapon selectivity coefficient:none:f4:1d',#1d array
'GKCN':'Ca-Na Gapon selectivity coefficient:none:f4:1d',#1d array
'GKCK':'Ca-K Gapon selectivity coefficient:none:f4:1d',#1d array
'THW':'Initial soil water content:m3/m3:f4:1d',#1d array
'THI':'Initial soil ice content:m3/m3:f4:1d',#1d array
'RSCfL':'Initial fine litter C:gC m-2:f4:1d',#1d array
'RSNfL':'Initial fine litter N:gN m-2:f4:1d',#1d array
'RSPfL':'Initial fine litter P:gP m-2:f4:1d',#1d array
'RSCwL':'Initial woody litter C:gC m-2:f4:1d',#1d array
'RSNwL':'Initial woody litter N:gN m-2:f4:1d',#1d array
'RSPwL':'Initial woody litter P:gP m-2:f4:1d',#1d array
'RSCmL':'Initial manure liter C:gC m-2:f4:1d',#1d array
'RSNmL':'Initial manure litter N:gN m-2:f4:1d',#1d array
'RSPmL':'Initial manure litter P:gP m-2:f4:1d'#1d array
}

def write_site_topo_data(config_dict):
  """
  write topographic data for a given site based on ascii input for ecosys
  """
  print('generate grid data for '+config_dict['case'])

  mdir=config_dict['mdir']
  case=config_dict['case']
  sife_filenm=mdir+config_dict['sitef']
  topofnm=mdir+config_dict['topf']
  ngrid=1
  ntopu=int(config_dict['ntopu'])
  ncol=int(config_dict['ncol'])
  nrow=int(config_dict['nrow'])

  DHI=np.zeros(ncol,dtype=np.float32)
  DVI=np.zeros(nrow,dtype=np.float32)
  with open(sife_filenm,"r") as sife_file:
    line=sife_file.readline()
    arr=strtool.strpack(line.strip().split(' '))
    ALATG=float(arr[0])
    ALTIG=float(arr[1])
    ATCAG=float(arr[2])
    IDTBLG=int(float(arr[3]))

    line=sife_file.readline()
    arr=strtool.strpack(line.strip().split(' '))
    OXYEG=float(arr[0])
    Z2GEG=float(arr[1])
    CO2EIG=float(arr[2])
    CH4EG=float(arr[3])
    Z2OEG=float(arr[4])
    ZNH3EG=float(arr[5])

    line=sife_file.readline()
    arr=strtool.strpack(line.strip().split(' '))
    IETYPG=int(arr[0])
    ISALTG=int(arr[1])
    DTBLIG=float(arr[4])
    DTBLDIG=float(arr[5])
    DTBLGG=float(arr[6])

    line=sife_file.readline()
    arr=strtool.strpack(line.strip().split(' '))
    RCHQNG=float(arr[0])
    RCHQEG=float(arr[1])
    RCHQSG=float(arr[2])
    RCHQWG=float(arr[3])
      
    RCHGNUG=float(arr[8])
    RCHGEUG=float(arr[9])
    RCHGSUG=float(arr[10])
    RCHGWUG=float(arr[11])
      
    RCHGNTG=float(arr[4])      
    RCHGETG=float(arr[5])
    RCHGSTG=float(arr[6])
    RCHGWTG=float(arr[7])
    RCHGDG=float(arr[12])

    line=sife_file.readline()
    arr=strtool.strpack(line.strip().split(' '))

    for j in range(ncol):
      DHI[j]=float(arr[j])

    line=sife_file.readline()
    arr=strtool.strpack(line.strip().split(' '))
    for j in range(nrow):
      DVI[j]=float(arr[j])

#write grid file

  current_dateTime = datetime.now()
  odir=config_dict['outdir']
  print('outputdir=%s'%odir)  
  os.makedirs(odir, exist_ok=True)  
  nc_f=config_dict['outdir']+case+'_grid_%4d%02d%02d.nc'%(current_dateTime.year,current_dateTime.month,current_dateTime.day)
  nc_fid = Dataset(nc_f, 'w')
    
  print("check file %s"%nc_f)
    
  nc_fid.description='Grid input data created on %4d/%02d/%02d/%02d:%02d:%02d'% \
      (current_dateTime.year,current_dateTime.month,current_dateTime.day, \
      current_dateTime.hour,current_dateTime.minute,current_dateTime.second)

  nlevs=20
  nc_fid.createDimension('ncol', ncol)
  nc_fid.createDimension('nrow', nrow)
  nc_fid.createDimension('ngrid', ngrid)
  nc_fid.createDimension('ntopou', ntopu)
  nc_fid.createDimension('nlevs', nlevs)

  for v in grid_info:
    ss=strtool.split_var(grid_info[v])
    if v=='DHI':
      long_name,units,dtype=ss
      w_nc_var = nc_fid.createVariable(v, dtype, ('ngrid','ncol'))
    elif v=='DVI':
      long_name,units,dtype=ss
      w_nc_var = nc_fid.createVariable(v, dtype, ('ngrid','nrow'))
    else:
      if len(ss)==4:
        long_name,flags,units,dtype=ss
      else:
        flags=''
        long_name,units,dtype=ss
      w_nc_var = nc_fid.createVariable(v, dtype, ('ngrid'))
      w_nc_var.long_name=long_name
      w_nc_var.units=units
      if flags:
        w_nc_var.flags=flags

  w_nc_var = nc_fid.createVariable('topo_grid', 'i4', ('ntopou'))
  w_nc_var.long_name='grid ID of the topo unit'
  w_nc_var.units='none'

  for v in topo_unit_info:
    ss=strtool.split_var(topo_unit_info[v])
    if len(ss)==5:
      long_name,flags,units,dtype,dstr=ss
    else:
      flags=''
      long_name,units,dtype,dstr=ss
    if dstr=='0d':
      w_nc_var = nc_fid.createVariable(v, dtype, ('ntopou'))
    else:
      w_nc_var = nc_fid.createVariable(v, dtype, ('ntopou','nlevs'))
      w_nc_var.FillValue=-999.9
    w_nc_var.long_name=long_name
    w_nc_var.units=units
    if flags:
      w_nc_var.flags=flags

  NHW = nc_fid.createVariable('NHW', 'i4', ())
  NHE = nc_fid.createVariable('NHE', 'i4', ())
  NVN = nc_fid.createVariable('NVN', 'i4', ())
  NVS = nc_fid.createVariable('NVS', 'i4', ())
  NHW[:] = int(config_dict['NHW'])
  NHE[:] = int(config_dict['NHE'])
  NVN[:] = int(config_dict['NVN'])
  NVS[:] = int(config_dict['NVS'])

  nc_fid.variables['ALATG'][:]=[ALATG]
  nc_fid.variables['ALTIG'][:]=[ALTIG]
  nc_fid.variables['ATCAG'][:]=[ATCAG]
  nc_fid.variables['IDTBLG'][:]=[IDTBLG]
  nc_fid.variables['OXYEG'][:]=[OXYEG]
  nc_fid.variables['Z2GEG'][:]=[Z2GEG]
  nc_fid.variables['CO2EIG'][:]=[CO2EIG]
  nc_fid.variables['CH4EG'][:]=[CH4EG]
  nc_fid.variables['Z2OEG'][:]=[Z2OEG]
  nc_fid.variables['ZNH3EG'][:]=[ZNH3EG]
  nc_fid.variables['IETYPG'][:]=[IETYPG]
  nc_fid.variables['DTBLIG'][:]=[DTBLIG]
  nc_fid.variables['DTBLDIG'][:]=[DTBLDIG]
  nc_fid.variables['DTBLGG'][:]=[DTBLGG]
  nc_fid.variables['RCHQNG'][:]=[RCHQNG]
  nc_fid.variables['RCHQEG'][:]=[RCHQEG]
  nc_fid.variables['RCHQSG'][:]=[RCHQSG]
  nc_fid.variables['RCHQWG'][:]=[RCHQWG]
  nc_fid.variables['RCHGNUG'][:]=[RCHGNUG]
  nc_fid.variables['RCHGEUG'][:]=[RCHGEUG]
  nc_fid.variables['RCHGSUG'][:]=[RCHGSUG]
  nc_fid.variables['RCHGWUG'][:]=[RCHGWUG]
  nc_fid.variables['RCHGWUG'][:]=[RCHGWUG]
  nc_fid.variables['RCHGNTG'][:]=[RCHGNTG]
  nc_fid.variables['RCHGETG'][:]=[RCHGETG]
  nc_fid.variables['RCHGSTG'][:]=[RCHGSTG]
  nc_fid.variables['RCHGWTG'][:]=[RCHGWTG]
  nc_fid.variables['RCHGDG'][:]=[RCHGDG]
  nc_fid.variables['DHI'][:]=[DHI]
  nc_fid.variables['DVI'][:]=[DVI]


  k=0
  mesoi=''
  with open(topofnm,"r") as topofile:

    while 1:
      line=topofile.readline()
      if not line:
        break
      arr=strtool.strpack(line.strip().split(' '))
      NH1=int(arr[0])
      NV1=int(arr[1])
      NH2=int(arr[2])
      NV2=int(arr[3])
      ASPX=float(arr[4])
      SL0=float(arr[5])
      DPTHSX=float(arr[7])
      print('NH1=%d,NH2=%d,NV1=%d,NV2=%d'%(NH1,NH2,NV1,NV2))
      mesoi=topofile.readline()
      nc_fid.variables['topo_grid'][k]=1
      nc_fid.variables['NH1'][k]=NH1
      nc_fid.variables['NV1'][k]=NV1
      nc_fid.variables['NH2'][k]=NH2
      nc_fid.variables['NV2'][k]=NV2
      nc_fid.variables['ASPX'][k]=ASPX
      nc_fid.variables['SL0'][k]=SL0
      nc_fid.variables['DPTHSX'][k]=DPTHSX

      soilFilenm=mdir+mesoi.strip()

      CDPTH=np.zeros(nlevs,dtype=np.float32)-999.
      BKDSI=np.zeros(nlevs,dtype=np.float32)-999.
      FC=np.zeros(nlevs,dtype=np.float32)-999.
      WP=np.zeros(nlevs,dtype=np.float32)-999.
      SCNV=np.zeros(nlevs,dtype=np.float32)-999.
      SCNH=np.zeros(nlevs,dtype=np.float32)-999.
      CSAND=np.zeros(nlevs,dtype=np.float32)-999.
      CSILT=np.zeros(nlevs,dtype=np.float32)-999.
      FHOL=np.zeros(nlevs,dtype=np.float32)-999.
      ROCK=np.zeros(nlevs,dtype=np.float32)-999.
      PH=np.zeros(nlevs,dtype=np.float32)-999.
      CEC=np.zeros(nlevs,dtype=np.float32)-999.
      AEC=np.zeros(nlevs,dtype=np.float32)-999.
      CORGC=np.zeros(nlevs,dtype=np.float32)-999.
      CORGR=np.zeros(nlevs,dtype=np.float32)-999.
      CORGN=np.zeros(nlevs,dtype=np.float32)-999.
      CORGP=np.zeros(nlevs,dtype=np.float32)-999.
      CNH4=np.zeros(nlevs,dtype=np.float32)-999.
      CNO3=np.zeros(nlevs,dtype=np.float32)-999.
      CPO4=np.zeros(nlevs,dtype=np.float32)-999.
      CAL=np.zeros(nlevs,dtype=np.float32)-999.
      CFE=np.zeros(nlevs,dtype=np.float32)-999.
      CCA=np.zeros(nlevs,dtype=np.float32)-999.
      CMG=np.zeros(nlevs,dtype=np.float32)-999.
      CNA=np.zeros(nlevs,dtype=np.float32)-999.
      CKA=np.zeros(nlevs,dtype=np.float32)-999.
      CSO4=np.zeros(nlevs,dtype=np.float32)-999.
      CCL=np.zeros(nlevs,dtype=np.float32)-999.

      CALPO=np.zeros(nlevs,dtype=np.float32)-999.
      CFEPO=np.zeros(nlevs,dtype=np.float32)-999.
      CCAPD=np.zeros(nlevs,dtype=np.float32)-999.
      CCAPH=np.zeros(nlevs,dtype=np.float32)-999.
      CALOH=np.zeros(nlevs,dtype=np.float32)-999.
      CFEOH=np.zeros(nlevs,dtype=np.float32)-999.
      CCACO=np.zeros(nlevs,dtype=np.float32)-999.
      CCASO=np.zeros(nlevs,dtype=np.float32)-999.

      GKC4=np.zeros(nlevs,dtype=np.float32)-999.
      GKCH=np.zeros(nlevs,dtype=np.float32)-999.
      GKCA=np.zeros(nlevs,dtype=np.float32)-999.
      GKCM=np.zeros(nlevs,dtype=np.float32)-999.
      GKCN=np.zeros(nlevs,dtype=np.float32)-999.
      GKCK=np.zeros(nlevs,dtype=np.float32)-999.

      THW=np.zeros(nlevs,dtype=np.float32)-999.
      THI=np.zeros(nlevs,dtype=np.float32)-999.

      RSCfL=np.zeros(nlevs,dtype=np.float32)-999.
      RSNfL=np.zeros(nlevs,dtype=np.float32)-999.
      RSPfL=np.zeros(nlevs,dtype=np.float32)-999.
      RSCwL=np.zeros(nlevs,dtype=np.float32)-999.
      RSNwL=np.zeros(nlevs,dtype=np.float32)-999.
      RSPwL=np.zeros(nlevs,dtype=np.float32)-999.
      RSCmL=np.zeros(nlevs,dtype=np.float32)-999.
      RSNmL=np.zeros(nlevs,dtype=np.float32)-999.
      RSPmL=np.zeros(nlevs,dtype=np.float32)-999.

      with open(soilFilenm,"r") as soilFile:
        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        PSIFC=float(arr[0])
        PSIWP=float(arr[1])
        ALBS=float(arr[2])
        PH0=float(arr[3])
        RSCf =float(arr[4])
        RSNf =float(arr[5])
        RSPf =float(arr[6])
        RSCw =float(arr[7])
        RSNw =float(arr[8])
        RSPw =float(arr[9])
        RSCm =float(arr[10])
        RSNm =float(arr[11])
        RSPm =float(arr[12])
        IXTYP1 =int(float(arr[13]))
        IXTYP2 =int(float(arr[14]))
        NUI = int(float(arr[15]))
        NJ  =int(float(arr[16]))
        NL1=int(float(arr[17]))
        NL2=int(float(arr[18]))
        ISOILR=int(float(arr[19]))

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CDPTH[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          BKDSI[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          FC[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          WP[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          SCNV[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          SCNH[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CSAND[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CSILT[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          FHOL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          ROCK[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          PH[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CEC[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          AEC[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CORGC[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CORGR[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CORGN[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CORGP[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CNH4[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CNO3[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CPO4[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CAL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CFE[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CCA[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CMG[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CNA[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CKA[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CSO4[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CCL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CALPO[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CFEPO[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CCAPD[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CCAPH[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CALOH[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CFEOH[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CCACO[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          CCASO[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          GKC4[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          GKCH[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          GKCA[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          GKCM[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          GKCN[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          GKCK[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          THW[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          THI[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSCfL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSNfL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSPfL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSCwL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSNwL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSPwL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSCmL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSNmL[j]=float(arr[j])

        line=soilFile.readline()
        arr=strtool.strpack(line.strip().split(','))
        for j in range(len(arr)):
          RSPmL[j]=float(arr[j])

        nc_fid.variables['PSIFC'][k]=PSIFC
        nc_fid.variables['PSIWP'][k]=PSIWP
        nc_fid.variables['ALBS'][k]=ALBS
        nc_fid.variables['PH0'][k]=PH0
        nc_fid.variables['RSCf'][k]=RSCf
        nc_fid.variables['RSNf'][k]=RSNf
        nc_fid.variables['RSPf'][k]=RSPf
        nc_fid.variables['RSCw'][k]=RSCw
        nc_fid.variables['RSNw'][k]=RSNw
        nc_fid.variables['RSPw'][k]=RSPw
        nc_fid.variables['RSCm'][k]=RSCm
        nc_fid.variables['RSNm'][k]=RSNm
        nc_fid.variables['RSPm'][k]=RSPm
        nc_fid.variables['IXTYP1'][k]=IXTYP1
        nc_fid.variables['IXTYP2'][k]=IXTYP2
        nc_fid.variables['NUI'][k]=NUI
        nc_fid.variables['NJ'][k]=NJ
        nc_fid.variables['NL1'][k]=NL1
        nc_fid.variables['NL2'][k]=NL2
        nc_fid.variables['ISOILR'][k]=ISOILR

        nc_fid.variables['CDPTH'][k,:]=CDPTH
        nc_fid.variables['BKDSI'][k,:]=BKDSI

        nc_fid.variables['FC'][k,:]=FC
        nc_fid.variables['WP'][k,:]=WP
        nc_fid.variables['SCNV'][k,:]=SCNV
        nc_fid.variables['SCNH'][k,:]=SCNH
        nc_fid.variables['CSAND'][k,:]=CSAND
        nc_fid.variables['CSILT'][k,:]=CSILT
        nc_fid.variables['FHOL'][k,:]=FHOL
        nc_fid.variables['ROCK'][k,:]=ROCK
        nc_fid.variables['PH'][k,:]=PH
        nc_fid.variables['CEC'][k,:]=PH
        nc_fid.variables['AEC'][k,:]=AEC

        nc_fid.variables['CORGC'][k,:]=CORGC
        nc_fid.variables['CORGR'][k,:]=CORGR
        nc_fid.variables['CORGN'][k,:]=CORGN
        nc_fid.variables['CORGP'][k,:]=CORGP
        nc_fid.variables['CNH4'][k,:]=CNH4
        nc_fid.variables['CNO3'][k,:]=CNO3
        nc_fid.variables['CPO4'][k,:]=CPO4

        nc_fid.variables['CAL'][k,:]=CAL
        nc_fid.variables['CFE'][k,:]=CFE
        nc_fid.variables['CCA'][k,:]=CCA
        nc_fid.variables['CMG'][k,:]=CMG
        nc_fid.variables['CNA'][k,:]=CNA
        nc_fid.variables['CKA'][k,:]=CKA
        nc_fid.variables['CSO4'][k,:]=CSO4
        nc_fid.variables['CCL'][k,:]=CCL
        nc_fid.variables['CALPO'][k,:]=CALPO
        nc_fid.variables['CFEPO'][k,:]=CFEPO
        nc_fid.variables['CCAPD'][k,:]=CCAPD
        nc_fid.variables['CCAPH'][k,:]=CCAPH
        nc_fid.variables['CALOH'][k,:]=CALOH
        nc_fid.variables['CFEOH'][k,:]=CFEOH
        nc_fid.variables['CCACO'][k,:]=CCACO
        nc_fid.variables['CCASO'][k,:]=CCASO

        nc_fid.variables['GKC4'][k,:]=GKC4
        nc_fid.variables['GKCH'][k,:]=GKCH
        nc_fid.variables['GKCA'][k,:]=GKCA
        nc_fid.variables['GKCM'][k,:]=GKCM
        nc_fid.variables['GKCN'][k,:]=GKCN
        nc_fid.variables['GKCK'][k,:]=GKCK

        nc_fid.variables['THW'][k,:]=THW
        nc_fid.variables['THI'][k,:]=THI

        nc_fid.variables['RSCfL'][k,:]=RSCfL
        nc_fid.variables['RSNfL'][k,:]=RSNfL
        nc_fid.variables['RSPfL'][k,:]=RSPfL
        nc_fid.variables['RSCwL'][k,:]=RSCwL
        nc_fid.variables['RSNwL'][k,:]=RSNwL
        nc_fid.variables['RSPwL'][k,:]=RSPwL
        nc_fid.variables['RSCmL'][k,:]=RSCmL
        nc_fid.variables['RSNmL'][k,:]=RSNmL
        nc_fid.variables['RSPmL'][k,:]=RSPmL
      k=k+1

  nc_fid.close()  # close the new file
