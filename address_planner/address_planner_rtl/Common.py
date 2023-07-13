# import sys 
# sys.path.append("..")
from ..uhdl.uhdl import *

def get_sw_readable(sub_space_list, readable=False):
    for sub_space in sub_space_list:
        for field in sub_space.filled_field_list:
            if field.sw_readable:
                return True  
    return readable

def get_sw_writeable(sub_space_list, writeable=False):
    for sub_space in sub_space_list:
        for field in sub_space.filled_field_list:
            if field.sw_writeable:
                return True  
    return writeable

def byte_mask(data, mask):
    mask_data = []
    for i in range(mask.width):
        mask_data.append( BitAnd(data[8*i+7:8*i], Combine(mask[i],mask[i],mask[i],mask[i],mask[i],mask[i],mask[i],mask[i])) )
    return Combine(*mask_data)