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

def get_sw_read_clean_and_set(sub_space, read_valid=False, outer=False):
    if not outer:
        for field in sub_space.filled_field_list:
            if field.sw_read_clean or field.sw_read_set:
                return True 
    else:
        for sub in sub_space.sub_space_list:
            for field in sub.filled_field_list:
                if field.sw_read_clean or field.sw_read_set:
                    return True 
    return read_valid        
    
def get_sw_write_clean_and_set(sub_space, write_valid=False, outer=False):
    if not outer:
        for field in sub_space.field_list:
            if not (field.sw_write_clean or field.sw_write_set):
                return True 
    else:
        for sub in sub_space.sub_space_list:
            for field in sub.field_list:
                if not (field.sw_write_clean or field.sw_write_set):
                    return True 
    return write_valid 

def get_field_external(sub_space, outer=False):
    if not outer:
        for field in sub_space.filled_field_list:
            if field.is_external:
                return True 
    else:
        for sub in sub_space.sub_space_list:
            for field in sub.filled_field_list:
                if field.is_external:
                    return True 
    return False   

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