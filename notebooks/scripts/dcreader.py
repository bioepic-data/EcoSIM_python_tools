import numpy as np

def tsdiff(ts):
    """
    apply backward difference to time series ts
    """
    ts1=np.zeros(np.shape(ts))
    nr=len(ts1)
    ts1[0]=ts[0]
    j=1
    while j<nr:
        ts1[j]=ts[j]-ts[j-1]
        j=j+1
    return ts1

class histd(object):

    """
    define class of daily output
    """
    def __init__(self,vars):
        """
        """
        self._vars=vars
        self.nvars=len(vars)
        self._data=np.zeros((self.nvars,366))
        self.recs=0
    def add_record(self,datav):
        """
        add a new data record
        """
#        print(datav)
        self._data[:,self.recs]=datav
#        print(self._data[:,self.recs])
        self.recs=self.recs+1

    def get_tsvarj(self,j):
        """
        get time series for the jth variable
        """
        if j>self.nvars:
            raise RuntimeError("The queried variable is outside the list")
        return np.reshape(self._data[j-1,0:self.recs],(self.recs))

    def get_tsvars(self,var):
        """
        get time series of variable var
        """
        j=0
        for v in self._vars:
            if v==var:
#                print('j=%d,%s'%(j,self._vars[j]))
#                print(self._data[j-1,0:self.recs])
                return np.reshape(self._data[j,0:self.recs],(self.recs))
            else:
                j=j+1
        raise RuntimeError("The queried variable is not in the list")

def ischar(c):
    """
    determine if c is a legitimate
    """
    if c=='_' or c=='[' or c==']' or c=='.' or c=='/' or c=='+':
        return True
    if ord(c)>=ord('0') and ord(c)<=ord('9'):
        return True
    if ord(c)>=ord('a') and ord(c)<=ord('z'):
        return True
    if ord(c)>=ord('A') and ord(c)<=ord('Z'):
        return True
    return False

def getvarls(tline):
    """
    get list of variables
    """
    docp=False
    v=''
    vl=[]
    nvar=0
    for c in tline:
        if ischar(c):
            if not docp:
                docp=True
            v=v+c
        else:
            if docp:
                vl.append(v)
                docp=False
                v=''
                nvar=nvar+1
    if v:
        vl.append(v)
        nvar=nvar+1
    return vl,nvar

def dcread(fnm):
    """
    read daily carbon output file
    """
    with open(fnm,"r") as infile:
        line=infile.readline()
        tline=line.strip()
        vars,nvars=getvarls(tline)
        print("totally %d variables read in, including"%nvars)
        j=0
        for var in vars:
            j=j+1
            print('%d: %s'%(j,var))
        dchist=histd(vars)

        line=infile.readline()
        while line:
            tline=line.strip()
#            print(tline)
            sarr=tline.split()
            datav=np.zeros(nvars)
            for n in range(nvars):
#                print('%d,%s'%(n,sarr[n]))
                datav[n]=float(sarr[n])
            dchist.add_record(datav)
            line=infile.readline()
    return dchist


#dchist1=dcread('/Users/jinyuntang/work/ecosys_sims/run_2017_and_new/outputs/010101998dc')
#dchist2=dcread('/Users/jinyuntang/work/ecosys_sims/run_2017_and_new/outputs_2017_code/010101998dc')

dchist2=dcread('/Users/jinyuntang/work/ecosys_sims/point1pt_outputs/010102008dc')

#rh1=dchist1.get_tsvars('ECO_RH')
#rh1=tsdiff(rh1)

rh2=dchist2.get_tsvars('ECO_RH')
rh2=tsdiff(rh2)

doy=dchist2.get_tsvarj(1)

import matplotlib.pyplot as plt

#plt.plot(doy,rh2,doy,rh1)
plt.plot(doy,rh2)
plt.show()
