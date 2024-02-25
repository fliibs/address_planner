from tkinter import Tcl
from ..GlobalValues import *
from copy               import deepcopy
import re 



# tcl_interpreter = Tcl()
# tcl_interpreter.eval("source ralf_parser.tcl")

py_dict = {}


def search_longest_string(tcl_interpreter):
    keys =  tcl_interpreter.eval('array names DEF')
    max_length_key  = max(keys.split(' '),key=lambda k: len(tcl_interpreter.eval(f'set result [dict get $DEF({k})]')))
    return max_length_key


def build_addrspace(tcl_interpreter):

    # search the longest string 
    key_array = search_longest_string(tcl_interpreter)
    py_dict[key_array] = {}

    #### update py_dict
    tcl_array = f'$DEF({key_array})'
    data_array = tcl_interpreter.eval(f'set result [dict get {tcl_array}]')
    keys_array = tcl_interpreter.eval('set keys [dict keys $result]')
    key_list = keys_array.split(' ')
    tcl_dict_recur(key_list, dict_=py_dict[key_array], tcl_dict=tcl_array, tcl_interpreter=tcl_interpreter)

    #### build rb
    from ..RegSpace import RegSpace
    reg_bank_B = RegSpace(name=py_dict[key_array]['name'], size=1e20*GB,bus_width=32,software_interface='apb')
    reg_bank_B_copy = build_subspace_recur(py_dict[key_array]['ADDR_DICT'], reg_bank_B, tcl_interpreter=tcl_interpreter)
    # reg_bank_B_copy.generate('build/ralf')
    reg_bank_B_copy = minimum_size(reg_bank_B_copy)
    return reg_bank_B_copy



def build_subspace_recur(dict_, father, tcl_interpreter):
    from ..Reg      import Register
    from ..RegSpace import RegSpace 
    from ..AddressSpace import AddressSpace

    father_copy = deepcopy(father)
    if 'name' not in dict_.keys():   
        for key in dict_.keys():   
            father_copy = build_subspace_recur(dict_[key], father_copy, tcl_interpreter)
        father_copy = minimum_size(father_copy)

    else:
        # recur field dict
        if dict_['FIELD_DICT']!=None:  
            
            reg_B = Register(name=dict_['name'])  
            reg_B_copy = build_field_recur(dict_['FIELD_DICT'], reg_B, tcl_interpreter)
            father_copy.add(sub_space=reg_B_copy,offset=int(dict_['addr']))
            
        # recur addr dict
        if dict_['ADDR_DICT']!=None:  
            reg_bank_B = RegSpace(name=dict_['name'], size=16*KB,bus_width=32,software_interface='apb')
            reg_bank_B_copy = build_subspace_recur(dict_['ADDR_DICT'], reg_bank_B, tcl_interpreter)
            
            if isinstance(father_copy, RegSpace):   father_copy = AddressSpace(name=father_copy.module_name, size=1e20*GB)
            father_copy.add(sub_space=reg_bank_B_copy, name=dict_['name'], offset=int(dict_['addr']))

    return father_copy
        

def build_field_recur(dict_, father, tcl_interpreter):
    father_copy = deepcopy(father)
    if 'name' not in dict_.keys():  
        for key in dict_.keys():    father_copy = build_field_recur(dict_[key], father_copy, tcl_interpreter)
    else:
        from ..Field    import Field
        sw_access = get_field_access_by_value(dict_['access'])
        father_copy.add(Field(name=dict_['name'],bit=int(dict_['bits']),sw_access=sw_access, init_value=int(dict_['reset'])),offset=int(dict_['addr']))
    
    return father_copy
    




















def tcl_dict_recur(key_list, dict_, tcl_dict, tcl_interpreter, father=None):
    # print('---------------------')
    for key in key_list:
        tcl_dict_tmp = f'{tcl_dict} {key}'
        # print('---', tcl_dict_tmp)
        value = tcl_interpreter.eval(f'set value [dict get {tcl_dict_tmp}]')

        # update py_dict
        if    (key == 'FIELD_DICT' or key == 'ADDR_DICT') and value=='':  dict_[key]=None
        elif  key == 'FIELD_DICT' and value!='':  
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, father)
        elif  key == 'ADDR_DICT' and value!='':  
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_recur(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, dict_)
        elif  key == 'addr':                                              dict_[key]= convert_address(value)
        elif  key == 'name':                                              dict_[key]=value  
        else:
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_recur(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, father)  
    

def tcl_dict_field(key_list, dict_, tcl_dict, tcl_interpreter, father=None):
    for key in key_list:
        tcl_dict_tmp = f'{tcl_dict} {key}'
        # print('===', tcl_dict_tmp)
        value = tcl_interpreter.eval(f'set value [dict get {tcl_dict_tmp}]')

        # update py_dict
        if 'name' not in key_list:
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, father)
        elif  key == 'addr':        dict_[key]=convert_address(value)
        elif  key == 'reset':       dict_[key]=convert_reset(value)
        else:                       dict_[key]=value 


def convert_address(address):
    clean_address = address.replace("@", "").replace("'", "")

    if clean_address.startswith('h'):
        return int(clean_address[1:], 16)
    elif clean_address.startswith('b'):
        return int(clean_address[1:], 2)
    else:
        return int(clean_address)
    
def convert_reset(reset):
    mb = re.match('([0-9]*)(\'[bB])([01_]+)'        ,reset)
    md = re.match('([0-9]*)(\'[dD])([0-9_]+)'       ,reset)
    mh = re.match('([0-9]*)(\'[hH])([0-9a-fA-F_]+)' ,reset)

    if mb:      value = int(mb.group(3).replace('_',''),2)
    elif md:    value = int(md.group(3).replace('_',''),10)
    elif mh:    value = int(mh.group(3).replace('_',''),16)
    else:       value = int(reset)
    
    return value


def minimum_size(father):
    from ..Reg import Register
    father_copy   = deepcopy(father)
    end_element   = max(father_copy.sub_space_list, key=lambda element: element.bit_offset)
    start_element = min(father_copy.sub_space_list, key=lambda element: element.bit_offset)
    if isinstance(end_element,Register):    father_copy.size=int(end_element.offset/8+end_element.bit/8-start_element.start_address/8)
    else:                                   father_copy.size=end_element.offset+end_element.size
    return father_copy