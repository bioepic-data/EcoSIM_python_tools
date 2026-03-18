#libraries
import numpy as np
from netCDF4 import Dataset
import subprocess
from pathlib import Path
import json
import os
from . import stringTools as strtool
import netCDF4 as nc

class ParEditor:
    # contruct the parameter editor ParEditor
    def __init__(self,pftparfile=None,micparfile=None):
        self.mic_recordjsonl=''
        self.pft_recordjsonl=''
        if pftparfile:
            self.pftparfile=pftparfile
            self.pft_recordjsonl=self.__get_jsonf_stem(pftparfile)
        if micparfile:    
            self.micparfile=micparfile        
            self.mic_recordjsonl=self.__get_jsonf_stem(micparfile)
        
    def reset(self,sure=False):
        """
        remove jsonl file if reset
        """
        if not sure:
            prompt='do you want remove the jasonl files that records past changes?'
            user_input = input(prompt).lower().strip()
            if user_input in ['y', 'yes']:
                self.__rmfile(self.mic_recordjsonl)
                self.__rmfile(self.pft_recordjsonl)
                print('Old jsonl files are removed.')
            else:
                print('Old jsonl files are used.')
        else:
            self.__rmfile(self.mic_recordjsonl)
            self.__rmfile(self.pft_recordjsonl)           
            print('Old jsonl files are removed.')

        
    def __rmfile(self,filepath):
        """
        remove filepath if it exists
        """
        filePath=filepath+'.jsonl'
        if os.path.exists(filePath):
            os.remove(filePath)    
            
    
    def __get_jsonf_stem(self,fname):
        """
        extract file stem for the jsonl file
        """
        parts0=fname.split('/')
        parts1=parts0[-1].split('.')
        return parts1[0]

    def __ExtractPftPars(self,pft):
        """
        extract parameters for designated pft
        """
        try:
            print(self.pftparfile)
        except NameError:
            print("The pft parameter file is not defined.")
        new_dict={}
        with Dataset(self.pftparfile, 'r') as nc_file:
            variable = nc_file.variables['pfts']        
            pft_loc=0
            for var in variable:
                result_string=''
                for byte in var:
                    if byte:
                        result_string=''.join([result_string,byte.decode('utf-8')])
                #locate the pft       
                if result_string.strip()==pft:      
                    #start extracting variables
                    for var_name in nc_file.variables:
                        if 'pfts' not in var_name and 'koppen' not in var_name:
                            variable1=nc_file.variables[var_name]
                            long_name = variable1.getncattr('long_name') if 'long_name' in variable1.ncattrs() else 'No long_name attribute'
                            new_dict[var_name]=[long_name,str(variable1[pft_loc].data)]
                            
                pft_loc=pft_loc+1
            return new_dict

    def __ExtractPftKeys(self,pft):
        """
        extract parameters for designated pft
        """
        try:
            print(self.pftparfile)
        except NameError:
            print("The pft parameter file is not defined.")
        new_keys=[]
        with Dataset(self.pftparfile, 'r') as nc_file:
            variable = nc_file.variables['pfts']        
            pft_loc=0
            pft_loc_cp=-1
            for var in variable:
                result_string=''
                for byte in var:
                    if byte:
                        result_string=''.join([result_string,byte.decode('utf-8')])
                #locate the pft       
                if result_string.strip()==pft:      
                    #start extracting variables
                    for var_name in nc_file.variables:
                        if 'pfts' not in var_name and 'koppen' not in var_name:
                            new_keys.append(var_name)
                    pft_loc_cp=pft_loc        
                pft_loc=pft_loc+1
            return new_keys,pft_loc_cp
    
    def CopyPlantPft(self,pft_from,pft_to):
        """
        copy parameters from pft_from to pft_to
        """
        pft_from_keys,pft_from_loc=self.__ExtractPftKeys(pft_from)
        if pft_from_loc ==-1:
            print(f"Parameters for {pft_from} not found")
            return

        pft_to_keys,pft_to_loc=self.__ExtractPftKeys(pft_to)
        if pft_to_loc== -1:
            with Dataset(self.pftparfile, 'a') as nc_file:
                new_index = nc_file.dimensions['npfts'].size
                variable = nc_file.variables['pfts']
                variable[new_index]=strtool.string2arr(pft_to,10)
                for key in pft_from_keys:
                    var = nc_file.variables[key]
                    shape=list(var.shape)
                    shape[0]=1
                    var[new_index]=var[pft_from_loc]
        else:
            with Dataset(self.pftparfile, 'r+') as nc_file:
                pft_to_keys.update(pft_from_keys)
        
    
    def PlantParCompare(self,pft1,pft2):
        """
        compare the parameters for two pfts
        """
        pft1_dict=self.__ExtractPftPars(pft1)
        pft2_dict=self.__ExtractPftPars(pft2)
        print('='*100)
        print(f"Compare plant traits: {pft1} vs {pft2}")
        print('-'*100)
        for key, val in pft1_dict.items():
            val2=pft2_dict[key]
            if val2[1]==val[1]: 
                a='yes' 
            else: 
                a='NO'
                print('%-120s(%-6s):%4s,%s,%s'%(val[0],key,a,val[1],val2[1]))
        
    def PlantParamModify(self,pft,pars,iscale=False,verbose=False):
        """
        Modify parameter parnames using parvals for pft on file parfile
        """
        try:
            print(self.pftparfile)
        except NameError:
            print("The pft parameter file is not defined.")
    
        new_dict={}
        with Dataset(self.pftparfile, 'r+') as nc_file:
            variable = nc_file.variables['pfts']        
            pft_loc=0
            #initialize list for recording parameter values
        
            for var in variable:
                result_string=''
                for byte in var:
                    if byte:
                        result_string=''.join([result_string,byte.decode('utf-8')])
                #locate the pft       
                if result_string.strip()==pft:                
                    #locate the variable
                    parvs= [0] * len(pars) 
                    parnames=['']*len(pars)
                    id=0
                    for parnm,parval in pars.items():
                        variable1=nc_file.variables[parnm]
                        long_name = variable1.getncattr('long_name') if 'long_name' in variable1.ncattrs() else 'No long_name attribute'

                        parval1=parval
                        if iscale:
                            parval1=parval*variable1[pft_loc]
                            if verbose:
                                print("%-100s: %s for %s is %f, and changed to %f"%(long_name,parnm,pft,variable1[pft_loc],parval1))
                            variable1[pft_loc]=parval*variable1[pft_loc]
                        else:                            
                            if verbose:                                
                                print(f"%-100s: {parnm} for {pft} is {variable1[pft_loc]}, and changed to {parval}"%(long_name))
                            variable1[pft_loc]=parval1    
                        parvs[id]=parval1
                        parnames[id]=parnm
                        id=id+1                    
                    new_dict={'pft':pft,'parvarnames':parnames,'parvals':parvs}
                    break                                                    
                pft_loc=pft_loc+1
        if new_dict:
            self.RecordPftPars(new_dict,self.pft_recordjsonl)
            

    def MicrobeParamModify(self,pars,iscale=False,verbose=False):
        """
        Modify microbial parameters parnames using parvals on file parfile
        """
        try:
            print(self.micparfile)
        except NameError:
            print("The microbial parameter file is not defined.")
            
        new_dict={}
        with Dataset(self.micparfile, 'r+') as nc_file:
            #initialize list for recording parameter values
            parvs=[0]*len(pars)
            parnames=['']*len(pars)
            id=0
            #locate the variable
            for parnm,parval in pars.items():
                variable1=nc_file.variables[parnm]
            
                long_name = variable1.getncattr('long_name') if 'long_name' in variable1.ncattrs() else 'No long_name attribute'
                if iscale:
                    if verbose:
                        print("%80s: %s is %f, and changed to %f"%(long_name,parnm,variable1[:],parval*variable1[:]))
                    variable1[:]=parval*variable1[:]                
                else:
                    if verbose:
                        print("%80s: %s is %f, and changed to %f"%(long_name,parnm,variable1[:],parval))
                    variable1[:]=parval
                parvs[id]=float(variable1[:])
                parnames[id]=parnm
                id=id+1
        new_dict={'parvarnames':parnames,'parvals':parvs}
        self.RecordPftPars(new_dict,self.mic_recordjsonl)
        

    def RecordPftPars(self,new_dict,RecordFileName):
        #record the old parameters
        # 'a' means append mode
        with open(RecordFileName+'.jsonl', 'a') as file:
            # Convert dict to a JSON string and write it, followed by a newline
            file.write(json.dumps(new_dict) + '\n')



    def delete_pft_records(self,input_file, output_file, names_to_delete):
        """
        names_to_delete: list of strings, e.g., ["gr3s32", "maiz31"]
        """
        with nc.Dataset(input_file, 'r') as src, nc.Dataset(output_file, 'w') as dst:
            # 1. Convert the character array 'pfts' into a list of strings for matching
            # Variable pfts has dimensions (npfts, nchars1) [cite: 107]            
            raw_pfts = src.variables['pfts'][:].filled(" ")
            pft_list = ["".join([c.decode('utf-8') if isinstance(c, bytes) else c for c in row]).strip() 
                    for row in raw_pfts]
        
            # 2. Identify indices for all requested names
            indices_to_delete = [i for i, name in enumerate(pft_list) if name in names_to_delete]
        
            if not indices_to_delete:
                print("No matching PFT names found to delete.")
                return

            print(f"Deleting {len(indices_to_delete)} records: {names_to_delete}")

            # 3. Copy Global Attributes (e.g., description, history) [cite: 108, 109]
            dst.setncatts({k: src.getncattr(k) for k in src.ncattrs()})

            # 4. Copy Dimensions, adjusting 'npfts' (UNLIMITED) 
            for name, dimension in src.dimensions.items():
                if name == 'npfts':
                    new_size = len(dimension) - len(indices_to_delete)
                    dst.createDimension(name, new_size if not dimension.isunlimited() else None)
                else:
                    dst.createDimension(name, len(dimension) if not dimension.isunlimited() else None)

            # 5. Copy and Filter Variables
            for name, variable in src.variables.items():
                # Create the variable with same datatype and dimensions (e.g., float, byte) [cite: 3, 14]
                dst_var = dst.createVariable(name, variable.datatype, variable.dimensions)
            
                # Copy variable attributes (e.g., long_name, units, flags) [cite: 4, 5, 15]
                dst_var.setncatts({k: variable.getncattr(k) for k in variable.ncattrs()})
            
                data = variable[:]
            
                # If the variable depends on the 'npfts' dimension, delete indices
                if 'npfts' in variable.dimensions:
                    pft_dim_axis = variable.dimensions.index('npfts')
                    # np.delete handles a list of indices efficiently
                    filtered_data = np.delete(data, indices_to_delete, axis=pft_dim_axis)
                    dst_var[:] = filtered_data
                else:
                    # Copy other variables (like pfts_short or pfts_long) as-is [cite: 107]
                    # Note: if those also relate to pft count, you may need to filter them similarly.
                    dst_var[:] = data

        print(f"Successfully created '{output_file}'. New record count: {len(pft_list) - len(indices_to_delete)}")

