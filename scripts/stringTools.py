import numpy as np
"""
define auxillary functions
"""
def split_var(var_info):
  x=var_info.split(':')
  return x


def string2arr(string,len1=0):
  """
  conver a string into array of chars
  """
  if len1 == 0:
    to_array = []
    for x in string:
      to_array.extend(x)
  else:
    to_array=np.array([' '] * len1, dtype='S1')
    ll=0
    for x in string:
      to_array[ll]=x
      ll=ll+1
  return to_array

def strpack(strarr):
  """
  pack the string array, to remove empty elements
  """
  to_array = []
  for x in strarr:
    if x:
      to_array.append(x)
  return to_array
