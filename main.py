
from tkinter import Tcl
from address_planner import *
from copy               import deepcopy

env_tcl_path = 'address_planner/ralf_parser/test.ralf'
# env_tcl_path = '/home/liuyunqi/huangtao/ap/build/addrmap/block/ralf/excel_parse.ralf'

with open(env_tcl_path,'r') as f:
    env_tcl_code = f.read()

tcl_interpreter = Tcl()
tcl_interpreter.eval("source address_planner/ralf_parser/ralf_parser.tcl")
tcl_interpreter.eval(env_tcl_code)

py_dict = {}

def search_longest_string():
    keys =  tcl_interpreter.eval('array names DEF')
    # testing
    max_length_key  = max(keys.split(' '),key=lambda k: len(tcl_interpreter.eval(f'set result [dict get $DEF({k})]')))
    return max_length_key


def build_addrspace():
    # search the longest string 
    key_array = search_longest_string()
    py_dict[key_array] = {}

    #### update py_dict
    tcl_array = f'$DEF({key_array})'
    data_array = tcl_interpreter.eval(f'set result [dict get {tcl_array}]')
    keys_array = tcl_interpreter.eval('set keys [dict keys $result]')
    key_list = keys_array.split(' ')
    tcl_dict_recur(key_list, dict_=py_dict[key_array], tcl_dict=tcl_array)
    print(py_dict)
    #### build rb
    reg_bank_B = RegSpace(name=py_dict[key_array]['name'], size=64*KB,bus_width=32,software_interface='apb')
    print(py_dict[key_array]['name'])
    reg_bank_B_copy = build_subspace_recur(py_dict[key_array]['ADDR_DICT'], reg_bank_B)
    reg_bank_B_copy.generate('build/ralf')


def build_subspace_recur(dict_, father):
    father_copy = deepcopy(father)
    if 'name' not in dict_.keys():   
        for key in dict_.keys():   father_copy = build_subspace_recur(dict_[key], father_copy)
    else:
        # recur field dict
        if dict_['FIELD_DICT']!=None:  
            reg_B = Register(name=dict_['name'])  
            reg_B_copy = build_field_recur(dict_['FIELD_DICT'], reg_B)
            father_copy.add(sub_space=reg_B_copy,offset=int(dict_['addr']))
        
        # recur addr dict
        if dict_['ADDR_DICT']!=None:  

            reg_bank_B = RegSpace(name=dict_['name'], size=16*KB,bus_width=32,software_interface='apb')
            reg_bank_B_copy = build_subspace_recur(dict_['ADDR_DICT'], reg_bank_B)
            if isinstance(father_copy, RegSpace):   father_copy = AddressSpace(name=father_copy.module_name, size=128*KB)
            father_copy.add(sub_space=reg_bank_B_copy, name=dict_['name'], offset=int(dict_['addr']))

    return father_copy
        

def build_field_recur(dict_, father):
    father_copy = deepcopy(father)
    if 'name' not in dict_.keys():  
        for key in dict_.keys():    father_copy = build_field_recur(dict_[key], father_copy)
    else:
        father_copy.add(Field(name=dict_['name'],bit=int(dict_['bits']), init_value=0),offset=int(dict_['addr']))
    
    return father_copy
    
    



def tcl_dict_recur(key_list, dict_, tcl_dict, father=None):
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
            tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, father)
        elif  key == 'ADDR_DICT' and value!='':  
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_recur(keys_dict.split(' '), dict_[key], tcl_dict_tmp, dict_)
        elif  key == 'addr':                                              dict_[key]= convert_address(value)
        elif  key == 'name':                                              dict_[key]=value  
        else:
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_recur(keys_dict.split(' '), dict_[key], tcl_dict_tmp, father)  
    

def tcl_dict_field(key_list, dict_, tcl_dict, father=None):
    for key in key_list:
        tcl_dict_tmp = f'{tcl_dict} {key}'
        # print('===', tcl_dict_tmp)
        value = tcl_interpreter.eval(f'set value [dict get {tcl_dict_tmp}]')
        print(key, value)

        # update py_dict
        if 'name' not in key_list:
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, father)
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
    



build_addrspace()
# print(py_dict)


print(convert_reset("'h3"))
