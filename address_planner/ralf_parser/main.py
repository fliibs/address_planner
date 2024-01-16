
from tkinter import Tcl
import ast
import json
import os, sys
sys.path.append('..')
from Field import *

env_tcl_path = 'test.tcl'
# env_tcl_path = '/home/liuyunqi/huangtao/ap/build/addrmap/block/ralf/excel_parse.ralf'

with open(env_tcl_path,'r') as f:
    env_tcl_code = f.read()

tcl_interpreter = Tcl()
tcl_interpreter.eval("source ralf_parser.tcl")
tcl_interpreter.eval(env_tcl_code)

py_dict = {}

def build_addrspace():
    keys =  tcl_interpreter.eval('array names DEF')
    print(keys)
    # search the longest string 
    key_array = 'B1' 
    py_dict[key_array] = {}
    ####
    tcl_array = f'$DEF({key_array})'
    data_array = tcl_interpreter.eval(f'set result [dict get {tcl_array}]')
    keys_array = tcl_interpreter.eval('set keys [dict keys $result]')
    print(keys_array)
    key_list = keys_array.split(' ')
    tcl_dict_recur(key_list, dict_=py_dict[key_array], tcl_dict=tcl_array)


def tcl_dict_recur(key_list, dict_, tcl_dict, father=None):
    print('---------------------')
    for key in key_list:
        tcl_dict_tmp = f'{tcl_dict} {key}'
        print('---', tcl_dict_tmp)
        value = tcl_interpreter.eval(f'set value [dict get {tcl_dict_tmp}]')

        # update py_dict
        if    (key == 'FIELD_DICT' or key == 'ADDR_DICT') and value=='':  dict_[key]=None
        elif  key == 'FIELD_DICT' and value!='':  
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            field = tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, father)
            print(field)
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
        print('===', tcl_dict_tmp)
        value = tcl_interpreter.eval(f'set value [dict get {tcl_dict_tmp}]')

        # update py_dict
        if 'name' not in key_list:
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            return tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, father)
        elif  key == 'addr':        dict_[key]=convert_address(value)
        else:                       dict_[key]=value 

        # build field
        if 'name' in key_list:
            return Field(name=dict_['name'],bit=dict_['bits'])


def convert_address(address):
    clean_address = address.replace("@", "").replace("'", "")

    if clean_address.startswith('h'):
        return int(clean_address[1:], 16)
    elif clean_address.startswith('b'):
        return int(clean_address[1:], 2)
    else:
        return int(clean_address)

build_addrspace()
print(py_dict)


