import numpy as np
from netCDF4 import Dataset
import os,time,sys,argparse
from datetime import datetime
from array import array
import stringTools as strtool
import warnings
warnings.filterwarnings("ignore")


#writing pft management data, annual time series


def write_pft_mgmt(config_dict):
    """
    write pft management file based on input configuration
    """
    print('generate pft data for '+config_dict['case'])
    mdir=config_dict['mdir']
    case=config_dict['case']
    pfts=[]  
    if ':' in config_dict['pftf']:    
        pfts=strtool.split_var(config_dict['pftf'])
      
    ntopu=int(config_dict['ntopu'])
    yearstr=""
    if 'year' in config_dict:
        yearstr=config_dict['year']
#  ncol=int(config_dict['ncol'])
#  nrow=int(config_dict['nrow'])

    current_dateTime = datetime.now()
    nc_f=config_dict['outdir']+case+'_pft_%4d%02d%02d.nc'%(current_dateTime.year,current_dateTime.month,current_dateTime.day)

    print("check file %s"%nc_f)

    nc_fid = Dataset(nc_f, 'w')

    nc_fid.description='PFT input data created on %4d/%02d/%02d/%02d:%02d:%02d'% \
        (current_dateTime.year,current_dateTime.month,current_dateTime.day, \
        current_dateTime.hour,current_dateTime.minute,current_dateTime.second)+ \
        '\n use READ(tline,*)DY,PPI(NZ,NY,NX),SDPTHI(NZ,NY,NX) to read planting information from pft_pltinfo;' +\
        ' use READ(tline,*)DY,ICUT,JCUT,HCUT,PCUT,ECUT11,ECUT12,ECUT13,ECUT14,ECUT21,ECUT22,ECUT23,ECUT24 to '+\
        'read management information from pft_mgmt'

    nc_fid.createDimension('ntopou', ntopu)  #number of topographic unit
    nc_fid.createDimension('nchar1', 10)
    nc_fid.createDimension('nchar2', 10)
    nc_fid.createDimension('ncharmgnt',128)
    nc_fid.createDimension('maxpfts', 5)
    nc_fid.createDimension('maxpmgt',24) #management is done at most once every two weeks
    nc_fid.createDimension('year', None)
#  nc_fid.createDimension('ncol', ncol)
#  nc_fid.createDimension('nrow', nrow)

    w_nc_var = nc_fid.createVariable('NH1', 'i4', ('ntopou'))
    w_nc_var.long_name='Starting column from the west for a topo unit'
    w_nc_var.units='None'

    w_nc_var = nc_fid.createVariable('NV1', 'i4', ('ntopou'))
    w_nc_var.long_name='Ending column at the east for a topo unit'
    w_nc_var.units='None'

    w_nc_var = nc_fid.createVariable('NH2', 'i4', ('ntopou'))
    w_nc_var.long_name='Starting row from the north  for a topo unit'
    w_nc_var.units='None'

    w_nc_var = nc_fid.createVariable('NV2', 'i4', ('ntopou'))
    w_nc_var.long_name='Ending row at the south  for a topo unit'
    w_nc_var.units='None'

    w_nc_var = nc_fid.createVariable('NZ', 'i4', ('ntopou'))
    w_nc_var.long_name='Number of pfts on a topo unit'
    w_nc_var.units='None'

    w_nc_var = nc_fid.createVariable('nmgnts', 'i2', ('year','ntopou','maxpfts'))
    w_nc_var.long_name='Number of managements for a given pft in in given topo unit in a year'
#w_nc_var = nc_fid.createVariable('pft_mgmt', 'S1', ('ntopu','nchars'))
#w_nc_var = nc_fid.createVariable('pft_mgmt', 'S1', ('ntopu','nchars'))
    w_nc_var = nc_fid.createVariable('pft_type', 'S1', ('year','ntopou','maxpfts','nchar1'))

    w_nc_var = nc_fid.createVariable('pft_pltinfo', 'S1', ('year','ntopou','maxpfts','ncharmgnt'))
    w_nc_var.long_name='string containing planting information'


    w_nc_var = nc_fid.createVariable('pft_mgmt', 'S1', ('year','ntopou','maxpfts','maxpmgt','ncharmgnt'))
    w_nc_var.long_name='string containing plant management information'

    pflag = nc_fid.createVariable('pft_dflag', 'i4', ())

    years=[]
    pft_dflag=-1  #no pft data
    if len(pfts)==2 and not yearstr:
    #only two input data and if no year information is given  
        pft_dflag=0  #constant pft managment data 
    elif len(pfts)>2 or yearstr:
        pft_dflag=1  #transient pft managment data, including multiple
      
    if pft_dflag==1:
        if ':' in yearstr:
            years=strtool.split_var(config_dict['year'])
        elif '-' in yearstr:
            year1=int(yearstr[0:4])
            year2=int(yearstr[5:])+1
            years=[]
        #in this case, plant mgmt file is always given as s1xxxxs2
        #where xxxx means year
            pfts1=config_dict['pftf']
            for year in range(year1,year2):
                years.append(str(year))
                pft=pfts1.replace('xxxx', str(year))
                pfts.append(pft)
            
        w_nc_var = nc_fid.createVariable('year', 'i4', ('year'))

    pflag[:]=pft_dflag
    pflag.setncattr('long_name','Flag for plant management data')
    pflag.setncattr('flags','-1 no pft data, 0 only plantation information, 1 transient pft data')

    k1=0
    for pf in pfts:
        pftnm=mdir+pf        
        if pft_dflag==1:
            nc_fid.variables['year'][k1]=int(years[k1])            
        readpftinfo(mdir,k1,pftnm,nc_fid)
        k1=k1+1
    nc_fid.close()  # close the new file


def readmgmnt(k1,k,nz,mgfnm,nc_fid):
    """
    read management information from file mgf, and write to nc_fid
    """
    with open(mgfnm,"r") as mgf:
        print(mgfnm)
        line1=mgf.readline()
        sarr1=strtool.string2arr(line1.strip())
        len1=len(sarr1)
        #planting information
        nc_fid.variables['pft_pltinfo'][k1,k,nz,:]=' '*128
        nc_fid.variables['pft_pltinfo'][k1,k,nz,0:len1]=sarr1
        k2=0
        #within year management
        while 1:
            line1=mgf.readline()
            if not line1:
                break
            sarr1=strtool.string2arr(line1.strip())
            len1=len(sarr1)
            nc_fid.variables['pft_mgmt'][k1,k,nz,k2,:]=' '*128
            nc_fid.variables['pft_mgmt'][k1,k,nz,k2,0:len1]=sarr1
            k2=k2+1
#            print(line1)
        nc_fid.variables['nmgnts'][k1,k,nz]=k2

def readpftinfo(mdir,k1,pftnm,nc_fid):        
    """
    read in plant pft file names, and save it to nc_fid
    """
    print('reading file %s'%pftnm)
    k=0    
    with open(pftnm,"r") as pftf:
        while 1:
            line=pftf.readline()
            if not line:
                break
            arr=strtool.strpack(line.strip().split(' '))
            NH1=int(arr[0])
            NV1=int(arr[1])
            NH2=int(arr[2])
            NV2=int(arr[3])
            NZ=int(arr[4])

            nc_fid.variables['NH1'][k]=NH1
            nc_fid.variables['NV1'][k]=NV1
            nc_fid.variables['NH2'][k]=NH2
            nc_fid.variables['NV2'][k]=NV2
            nc_fid.variables['NZ'][k]=NZ
            line=pftf.readline()
            arr=strtool.strpack(line.strip().split(' '))
            for nz in range(NZ):
                sarr=strtool.string2arr(arr[nz*2])
                len1=len(sarr)
                nc_fid.variables['pft_type'][k1,k,nz,0:len1]=sarr
                #pft managemnt file
                if arr[nz*2+1] != 'NO':
#                    print('%s %s\n'%(arr[nz*2],arr[nz*2+1]))
                    mgfnm=mdir+arr[nz*2+1]
                    #
                    readmgmnt(k1,k,nz,mgfnm,nc_fid)
                        
            k=k+1