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

def get_sw_writevalid(sub_space, writevalid=False):
    for field in sub_space.filled_field_list:
        if field.sw_read_clean or field.sw_read_set or field.is_external:
            return True 
    return writevalid

def byte_mask(data, mask):
    mask_data = []
    for i in range(mask.width):
        mask_data.append(BitMask(data[8*i+7:8*i], mask[i]))
    mask_data.reverse()
    return Combine(*mask_data)

def perfect_get_io(component, string):
        match_io_list = []
        for io in component.io_list:
            if string==io.name:
                match_io_list.append(io)
        return match_io_list