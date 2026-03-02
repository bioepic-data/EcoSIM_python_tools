#code to set up EcoSIM management inforation

#write fertilizer application into EcoSIM form
import numpy as np
from datetime import datetime
lb2kg=0.453592
hect2m2=1.e4
acre2m2=4046.86
ft2m=0.3048


class Fertilizer():
    """
    define fertilizer type
    """
    def __init__(self):
        
        self.fert={'DDMMYYYY':0,'NH4Soil[gN m-2]':0,'NH3Soil[gN m-2]':0,'UreaSoil[gN m-2]':0,'NO3Soil[gN m-2]':0,
      'NH4Band[gN m-2]':0,'NH3Band[gN m-2]':0,'UreaBand[gN m-2]':0,'NO3Band[gN m-2]':0, 
      'MonocalciumPhosphateSoil[gP m-2]':0,'MonocalciumPhosphateBand[gP m-2]':0,'hydroxyapatite[gP m-2]':0,
      'LimeStone[gCa m-2]':0,'Gypsum[gCa m-2]':0,'PlantResC[gC m-2]':0,'PlantResN[gN m-2]':0,'PlantResP[gP m-2]':0,
      'ManureC[gC m-2]':0,'ManureN[gN m-2]':0,'ManureP[gP m-2]':0,'AppDepth[m]':0,'BandWidth[m]':0,'PO4Soil[gP m-2]':0,
      'PO4Band[gP m-2]':0,'FertType':0,'LiterType':0,'ManureType':0}
        
        self.FertType={'11-52-0':'11-NH4;52-P2O5;0-K;','30-0-20':'30-NH4;0-P;20-K2O;',
                       '15-15-15':'8.9-NH4,2.9-NO3,3.2-Urea;15-P2O5;15-K2O'}
        self.scal=1

    def __reset(self):
        """
        """

        for key in self.fert:
            self.fert[key]=0
            
    def ISOUnit(self,FertAmount):
        """
        convert incoming fertilizer application unit
        """
        self.scal=1.
        amount,unitIn = FertAmount.split(' ', 1)
        #mass
        if 'lb' in unitIn:
            self.scal=lb2kg
        #area
        if 'ac-1' in unitIn:
            self.scal=self.scal/acre2m2
        elif 'sqft-1':
            self.scal=self.scal/(ft2m*ft2m)
        elif 'ha-1':
            self.scal=self.scal/hect2m2
        return self.scal*float(amount)
        
    def ConfigFert(self,FertType,Amount,ndays):
        """
        configure fertilizer string
        """
        chemstr=self.FertType[FertType]
        parts=chemstr.split(';')

        for comp in parts:
            if ',' in comp:
                parts1=comp.split(',')                
            else:
                parts1=[comp]
            for part in parts1:
                if '-' in part:
                    part1=part.split('-')                
                    pct=float(part1[0])
                    ntype=part1[1]
                    if ntype =='NH4':
                        self.fert['NH4Soil[gN m-2]']=pct*0.01*Amount*1000./ndays
                        self.fert['FertType']=1
                    elif ntype=='P2O5':
                        self.fert['PO4Soil[gP m-2]']=pct*0.01*Amount*1000./ndays
                        self.fert['FertType']=1
                    elif ntype=='Urea':
                        self.fert['UreaSoil[gN m-2]']=pct*0.01*Amount*1000./ndays
                        self.fert['FertType']=1
                    elif ntype=='NO3':
                        self.fert['NO3Soil[gN m-2]']=pct*0.01*Amount*1000./ndays
                        self.fert['FertType']=1
                    
                
    def dateParse(self,dates):
        """
        parse date string into DDMMYYYY format
        """
        monstr={'Jan':1,'Feb':2,'Mar':3,'Apr':4,
              'May':5,'Jun':6,'Jul':7,'Aug':8,
              'Sep':9,'Oct':10,'Nov':11,'Dec':12}
        
        days,mon,yyyy=dates.split(' ')
        if '-' in days:
            dat1,dat2=days.split('-')
            day1=int(dat1)
            day2=int(dat2)
            nday=day2-day1+1
        else:
            nday=1
            day1=int(days)
        datestrs=[]
        for d in range(nday):
            day=day1+d
            date_str=f"{day:02d}"+f"{monstr[mon]:02d}"+yyyy
            datestrs.append(date_str)
        return datestrs
        
    def writeFert(self,fertilizer=None):
        """
        convert fertilizer dict into a string
        """    
        ndays=0
        if fertilizer:
            """
            do something
            """
            dates,FertType,FertAmount=fertilizer.split(':')
            amount=self.ISOUnit(FertAmount)
            datestrs=self.dateParse(dates)
            ndays=len(datestrs)
            self.ConfigFert(FertType,amount,ndays)
        fert_strs=[]
        for nday in range(ndays):            
            for key in self.fert:
                if key=='DDMMYYYY':
                    fert_str=datestrs[nday]
                else:
                    val=self.fert[key]
                    if val != int(val):
                        fert_str=fert_str+' '+f"{val:.2f}"
                    else:
                        fert_str=fert_str+' '+str(self.fert[key])
            fert_strs.append(fert_str)
        return fert_strs
