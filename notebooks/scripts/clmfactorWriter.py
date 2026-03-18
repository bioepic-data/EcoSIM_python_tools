from netCDF4 import Dataset
import os,time,sys,argparse
from datetime import datetime
from array import array
import warnings
warnings.filterwarnings("ignore")

case_sample_dict={
'dir':'sample',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/sample/',
'flist':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/sample/clmfacor_list'
}

case_lake_dict={
'dir':'lake',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/lake/',
'flist':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/lake/clmfacor_list'
}

case_dry_dict={
'dir':'dryland_maize',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/dryland_maize/',
'flist':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/dryland_maize/clmfacor_list'
}

case=case_dry_dict
mdir=case['mdir']
flist=case['flist']


current_dateTime = datetime.now()
nc_f=case['mdir']+case['dir']+'_clmfactor_%4d%02d%02d.nc'%(current_dateTime.year,current_dateTime.month,current_dateTime.day)
nc_fid = Dataset(nc_f, 'w')


nc_fid.createDimension('year', None)

w_nc_var = nc_fid.createVariable('DRAD', 'f4', ('year'))
w_nc_var.long_name='annual change in radiation'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DTMPX', 'f4', ('year'))
w_nc_var.long_name='annual change in maximum air temperature'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DTMPN', 'f4', ('year'))
w_nc_var.long_name='annual change in minimum air temperature'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DHUM', 'f4', ('year'))
w_nc_var.long_name='annual change in air humidity'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DPREC', 'f4', ('year'))
w_nc_var.long_name='annual change in precipitation'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DIRRI', 'f4', ('year'))
w_nc_var.long_name='annual change in irrigation'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DCO2E', 'f4', ('year'))
w_nc_var.long_name='annual change in atmospheric CO2'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DCH4E', 'f4', ('year'))
w_nc_var.long_name='annual change in atmospheric CH4'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DWIND', 'f4', ('year'))
w_nc_var.long_name='annual change in atmospheric wind'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DCN4R', 'f4', ('year'))
w_nc_var.long_name='annual change in atmospheric NH4 concentration'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('DCNOR', 'f4', ('year'))
w_nc_var.long_name='annual change in atmospheric NO3 concentration'
w_nc_var.units='None'

w_nc_var = nc_fid.createVariable('ICLM', 'f4', ('year'))
w_nc_var.long_name='annual change climate change factor type'
w_nc_var.units='None'
w_nc_var.flags='1:by step, 2:by year'

w_nc_var = nc_fid.createVariable('year', 'i4', ('year'))
w_nc_var.long_name='annual change climate change factor type'
w_nc_var.units='None'
w_nc_var.flags='1:by step, 2:by year'

def read_clmf(optfile):
    """
    read the climate change factors
    and the climate change category
    """
    with open(optfile,"r") as ifile:
        #skip the first six lines
        for j in range(6):
            line=ifile.readline().strip()
        clmf=ifile.readline().strip()
        #skip the next three lines
        for j in range(3):
            line=ifile.readline().strip()
        line=ifile.readline().strip()
        sarr=line.split(',')
        return clmf,sarr[-1]


with open(flist,"r") as ifile:
    line=ifile.readline().strip()
    k=0
    while line:
        opfile=mdir+line
        clmf,clmt=read_clmf(opfile)
        if case['dir']=='sample':            
            sarr=(line[-4:]+','+clmt+','+clmf).split(',')
        else:
            sarr=('20'+line[2:4]+','+clmt+','+clmf).split(',')
        nc_fid.variables['year'][k]=int(sarr[0])
        nc_fid.variables['ICLM'][k]=int(sarr[1])
        nc_fid.variables['DRAD'][k]=float(sarr[2])
        nc_fid.variables['DTMPX'][k]=float(sarr[3])
        nc_fid.variables['DTMPN'][k]=float(sarr[4])
        nc_fid.variables['DHUM'][k]=float(sarr[5])
        nc_fid.variables['DPREC'][k]=float(sarr[6])
        nc_fid.variables['DIRRI'][k]=float(sarr[7])
        nc_fid.variables['DWIND'][k]=float(sarr[8])
        nc_fid.variables['DCO2E'][k]=float(sarr[9])
        nc_fid.variables['DCN4R'][k]=float(sarr[10])
        nc_fid.variables['DCNOR'][k]=float(sarr[11])
        line=ifile.readline().strip()
        k=k+1


nc_fid.close()  # close the new file
