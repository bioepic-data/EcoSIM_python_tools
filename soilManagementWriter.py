import numpy as np
import numpy as np
from netCDF4 import Dataset
import os,time,sys,argparse
from datetime import datetime
from array import array
import stringTools as strtool
import warnings
warnings.filterwarnings("ignore")


config_lake_dict={
'case':'lake',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/lake/',
'outdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/lake/',    
'ntopu':'2'
}


config_sample_dict={
'case':'sample',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/sample/',
'outdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/sample/',    
'ntopu':'1'
}

config_dry_dict={
'case':'dryland',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/dryland_maize/',
'outdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/dryland_maize/',    
'ntopu':'1'
}

config_morrow2_dict={
'case':'Morrow2',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/Morrow_figure3/17-2/',
'mefile':'mexxxxm',
'years':'1898-2021',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Morrow2/',    
'NH1':[1],
'NV1':[1],
'NH2':[1],
'NV2':[1],
'ntopu':'1'    
}

config_morrow4_dict={
'case':'Morrow4',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/Morrow_figure3/17-4/',
'mefile':'mexxxxm',
'years':'1898-2021',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Morrow4/',    
'NH1':[1],
'NV1':[1],
'NH2':[1],
'NV2':[1],
'ntopu':'1'    
}

config_sorghum_dict={
'case':'Sorghum',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/sorghum/plt_sorg/',
'mefile':'mexxxxm',
'years':'2002-2007',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Sorghum/',    
'NH1':[1],
'NV1':[1],
'NH2':[1],
'NV2':[1],
'ntopu':'1'    
}

config_dict=config_sorghum_dict


def read_fert_file(ifile,mfname,nc_fid):
    """
    read fertilization file
    """
    with open(ifile,"r") as infile:
        line=infile.readline().strip()
        for k1 in range(12):
            nc_fid.variables[mfname][k1,:]=' '*24
        k1=0
        while line:
            sarr1=strtool.string2arr(line)
            len1=len(sarr1)
            nc_fid.variables[mfname][k1,:]=' '*128
            nc_fid.variables[mfname][k1,0:len1]=sarr1
            line=infile.readline().strip()
            k1=k1+1

def count_lines_iterative(filepath):
    """Counts the number of lines in a file by iterating through it."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            line_count = 0
            for line in file:
                line_count += 1
            return line_count
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return -1 # Or raise an exception
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1
        
def read_irrig_file(ifile,mfname,nc_fid):
    """
    read irrigation file
    """
    print('file=%s,mfname=%s\n'%(ifile,mfname))
    with open(ifile,"r") as infile:
        line=infile.readline().strip()
        for k1 in range(24):
            nc_fid.variables[mfname][k1,:]=' '*128
        k1=0
        while line:
            sarr1=strtool.string2arr(line)
            len1=len(sarr1)
            nc_fid.variables[mfname][k1,0:len1]=sarr1
            line=infile.readline().strip()
            k1=k1+1
    
def read_till_file(ifile,mfname,nc_fid,nrecors):        
    """
    read tillage file
    """
    with open(ifile,"r") as infile:
        line=infile.readline().strip()
        for k1 in range(nrecors):
            nc_fid.variables[mfname][k1,:]=' '*24
        k1=0
        while line:
            sarr1=strtool.string2arr(line)
            len1=len(sarr1)
            nc_fid.variables[mfname][k1,0:len1]=sarr1
            line=infile.readline().strip()
            k1=k1+1
            

def write_soil_mgmt(config_dict):
    print('generate soil managment data for '+config_dict['case'])

    mdir=config_dict['mdir']
    case=config_dict['case']

    ntopu=int(config_dict['ntopu'])

    current_dateTime = datetime.now()
    nc_f=config_dict['outdir']+case+'_soilmgmt_%4d%02d%02d.nc'%(current_dateTime.year,current_dateTime.month,current_dateTime.day)

    print("check file %s"%nc_f)

    nc_fid = Dataset(nc_f, 'w')

    nc_fid.description='soil managment data created on %4d/%02d/%02d/%02d:%02d:%02d'% \
    (current_dateTime.year,current_dateTime.month,current_dateTime.day, \
    current_dateTime.hour,current_dateTime.minute,current_dateTime.second)


    nc_fid.createDimension('ntopou', ntopu)
    nc_fid.createDimension('nchar1', 10)
    nc_fid.createDimension('nchart', 24)    
    nc_fid.createDimension('nfert', 12)
    nc_fid.createDimension('nfire', 12)    
    nc_fid.createDimension('nirri', 24)    
    nc_fid.createDimension('nchari', 128)
    nc_fid.createDimension('ncharf', 128)
    nc_fid.createDimension('year', None)

    w_nc_var = nc_fid.createVariable('year', 'i4', ('year'))
    w_nc_var.long_name='year AD'

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

    w_nc_var = nc_fid.createVariable('fertf', 'S1', ('year','ntopou','nchar1'))
    w_nc_var.long_name='Fertilization info for a topo unit'

    w_nc_var = nc_fid.createVariable('tillf', 'S1', ('year','ntopou','nchar1'))
    w_nc_var.long_name='Tillage info for a topo unit'

    w_nc_var = nc_fid.createVariable('irrigf', 'S1', ('year','ntopou','nchar1'))
    w_nc_var.long_name='Irrigation info for a topo unit'

    if case=='dryland':
        w_nc_var=nc_fid.createVariable('me01t', 'S1', ('ntill','nchart'))
        w_nc_var.long_name='Tillage file'

        nc_fid.variables['NH1'][:]=1
        nc_fid.variables['NV1'][:]=1
        nc_fid.variables['NH2'][:]=1
        nc_fid.variables['NV2'][:]=1

        mfname='me01t'
        ifile=mdir+mfname
        read_till_file(ifile,mfname,nc_fid)

        w_nc_var=nc_fid.createVariable('me01f', 'S1', ('nfert','ncharf'))
        w_nc_var.long_name='fertilization file'
        mfname='me01f'
        ifile=mdir+mfname
        read_fert_file(ifile,mfname,nc_fid)

        w_nc_var=nc_fid.createVariable('me03f', 'S1', ('nfert','ncharf'))
        w_nc_var.long_name='fertilization file'
        mfname='me03f'
        ifile=mdir+mfname
        read_fert_file(ifile,mfname,nc_fid)

        w_nc_var=nc_fid.createVariable('me05f', 'S1', ('nfert','ncharf'))
        w_nc_var.long_name='fertilization file'
        mfname='me05f'
        ifile=mdir+mfname
        read_fert_file(ifile,mfname,nc_fid)

        nc_fid.variables['year'][:]=range(2001,2007)
        for jj in range(2007-2001):
            nc_fid.variables['tillf'][jj,0,:]=' '*10            
            nc_fid.variables['fertf'][jj,0,:]=' '*10
            nc_fid.variables['irrigf'][jj,0,:]=' '*10

            nc_fid.variables['tillf'][0,0,0:5]=['m','e','0','1','t']
            nc_fid.variables['fertf'][0,0,0:5]=['m','e','0','1','f']
            nc_fid.variables['irrigf'][0,0,0:2]=['N','O']

            nc_fid.variables['tillf'][1,0,0:2]=['N','O']
            nc_fid.variables['fertf'][1,0,0:2]=['N','O']
            nc_fid.variables['irrigf'][1,0,0:2]=['N','O']

            nc_fid.variables['tillf'][2,0,0:2]=['N','O']
            nc_fid.variables['fertf'][2,0,0:5]=['m','e','0','3','f']
            nc_fid.variables['irrigf'][2,0,0:2]=['N','O']

            nc_fid.variables['tillf'][3,0,0:2]=['N','O']
            nc_fid.variables['fertf'][3,0,0:2]=['N','O']
            nc_fid.variables['irrigf'][3,0,0:2]=['N','O']

            nc_fid.variables['tillf'][4,0,0:2]=['N','O']
            nc_fid.variables['fertf'][4,0,0:5]=['m','e','0','5','f']
            nc_fid.variables['irrigf'][4,0,0:2]=['N','O']

            nc_fid.variables['tillf'][5,0,0:2]=['N','O']
            nc_fid.variables['fertf'][5,0,0:2]=['N','O']
            nc_fid.variables['irrigf'][5,0,0:2]=['N','O']

    elif case=='sample':
        nc_fid.variables['year'][:]=range(1979,2011)
        for jj in range(2011-1979):
            nc_fid.variables['fertf'][jj,0,:]=' '*10
            nc_fid.variables['tillf'][jj,0,:]=' '*10
            nc_fid.variables['irrigf'][jj,0,:]=' '*10
            nc_fid.variables['fertf'][jj,0,0:2]=['N','O']
            nc_fid.variables['tillf'][jj,0,0:2]=['N','O']
            nc_fid.variables['irrigf'][jj,0,0:2]=['N','O']
    elif case=='lake':
        nc_fid.variables['NH1'][:]=[1,2]
        nc_fid.variables['NV1'][:]=[1,1]
        nc_fid.variables['NH2'][:]=[1,2]
        nc_fid.variables['NV2'][:]=[1,1]
        nc_fid.variables['year'][:]=range(2001,2009)
        for jj in range(2009-2001):
            nc_fid.variables['fertf'][jj,:,:]=' '*10
            nc_fid.variables['tillf'][jj,:,:]=' '*10
            nc_fid.variables['irrigf'][jj,:,:]=' '*10
            nc_fid.variables['fertf'][jj,:,0:2]=[['N','O'],['N','O']]
            nc_fid.variables['tillf'][jj,:,0:2]=[['N','O'],['N','O']]
            nc_fid.variables['irrigf'][jj,:,0:2]=[['N','O'],['N','O']]
    else:

        if 'NH1' in config_dict:
            nc_fid.variables['NH1'][:]=config_dict['NH1']
        if 'NV1' in config_dict:
            nc_fid.variables['NV1'][:]=config_dict['NV1']
        if 'NH2' in config_dict:
            nc_fid.variables['NH2'][:]=config_dict['NH2']
        if 'NV2' in config_dict:
            nc_fid.variables['NV2'][:]=config_dict['NV2']
        
        if 'mefile' in config_dict and 'years' in config_dict:
            yearstr=config_dict['years']
            year1=int(yearstr[0:4])
            year2=int(yearstr[5:])+1
            mefile=config_dict['mefile']
            nc_fid.variables['year'][:]=range(year1,year2)
            
            for year in range(year1,year2):
                jj=year-year1
                fsmgmt=mdir+mefile.replace('xxxx', str(year))
                print('read file %s'%fsmgmt)       
                with open(fsmgmt,"r") as infile:
                    ntopo=0
                    while True:
                        line=infile.readline().strip()                
                        if not line:
                            break
                        #read coordinate    
                        numbers = [int(x) for x in line.split()]
                        #locate topo unit
                        for ng in range(ntopu):
                            if numbers[0] == nc_fid.variables['NH1'][ng] and \
                                numbers[1] == nc_fid.variables['NV1'][ng] and \
                                numbers[2] == nc_fid.variables['NH2'][ng] and \
                                numbers[3] == nc_fid.variables['NV2'][ng]:
                                break                        
                        #read management file
                        line=infile.readline().strip()   
                        fnms= line.split()
                        print(fnms)
                        nc_fid.variables['tillf'][jj,ng,:]=' '*10            
                        nc_fid.variables['fertf'][jj,ng,:]=' '*10
                        nc_fid.variables['irrigf'][jj,ng,:]=' '*10        
                        #tillage
                        if fnms[0] == 'NO':
                            nc_fid.variables['tillf'][jj,ng,0:2]=['N','O']
                        else:                            
                            for ic in range(len(fnms[0])):                                
                                nc_fid.variables['tillf'][jj,ng,ic]=fnms[0][ic]
                            ifile=mdir+fnms[0]    
                            nrecords=count_lines_iterative(ifile)
                            if 'ntill' not in nc_fid.dimensions:
                                if nrecords > 300:
                                    nrecord=367
                                    nc_fid.createDimension('ntill', 367)
                                else:
                                    nrecord=12
                                    nc_fid.createDimension('ntill', 12)
                            w_nc_var=nc_fid.createVariable(fnms[0], 'S1', ('ntill','nchart'))
                            w_nc_var.long_name='Tillage file'                            
                            read_till_file(ifile,fnms[0],nc_fid,nrecord)

                                
                        #fertilization
                        if fnms[1] == 'NO':
                            nc_fid.variables['fertf'][jj,ng,0:2]=['N','O']
                        else:                            
                            for ic in range(len(fnms[1])):                                
                                nc_fid.variables['fertf'][jj,ng,ic]=fnms[1][ic]
                            ifile=mdir+fnms[1]
                            w_nc_var=nc_fid.createVariable(fnms[1], 'S1', ('nfert','ncharf'))
                            w_nc_var.long_name='Fertilization file'                            
                            read_fert_file(ifile,fnms[1],nc_fid)    
                        #irrigation
                        if fnms[2] == 'NO':
                            nc_fid.variables['irrigf'][jj,ng,0:2]=['N','O']
                        else:                            
                            for ic in range(len(fnms[2])):                                
                                nc_fid.variables['irrigf'][jj,ng,ic]=fnms[2][ic]
                            ifile=mdir+fnms[2]
                            w_nc_var=nc_fid.createVariable(fnms[2], 'S1', ('nirri','nchari'))
                            w_nc_var.long_name='Irrigation file'                            
                            read_irrig_file(ifile,fnms[2],nc_fid)                            
                                                        
                        ntopo=ntopo+1
            
        if 'firef' in config_dict:
            #assume firef is given a string splitted by ';'
            firef=config_dict['firef']
            #seporate files
            result = firef.split(';')            
            for filen in result:
                w_nc_var = nc_fid.createVariable(filen, 'S1', ('ntopou','nchar1'))
                w_nc_var.long_name='Fire event info for a topo unit'
                
                with open(mdir+filen,"r") as infile:
                    ntopo=0
                    while True:
                        line=infile.readline().strip()                
                        if not line:
                            break         
                        numbers = [int(x) for x in line.split()]
                        #locate topo unit
                        for ng in range(ntopu):
                            if numbers[0] == nc_fid.variables['NH1'][ng] and \
                                numbers[1] == nc_fid.variables['NV1'][ng] and \
                                numbers[2] == nc_fid.variables['NH2'][ng] and \
                                numbers[3] == nc_fid.variables['NV2'][ng]:
                                break                        
                        line=infile.readline().strip()   
                        fnms= line.split()
                        print(fnms)
                        nc_fid.variables[filen][ng,:]=' '*10   
                        if fnms[0] == 'NO':
                            nc_fid.variables[filen][jj,ng,0:2]=['N','O']
                        else:                            
                            for ic in range(len(fnms[0])):                                
                                nc_fid.variables[filen][ng,ic]=fnms[0][ic]
                            ifile=mdir+fnms[0]    
                            w_nc_var=nc_fid.createVariable(fnms[0], 'S1', ('nfire','nchart'))
                            w_nc_var.long_name='Fire file'                            
                            read_till_file(ifile,fnms[0],nc_fid)
                            
#                        nc_fid.variables['firef'][jj,ng,:]=' '*10            
                        ntopo=ntopo+1
            

    nc_fid.close()  # close the new file

