
from tkinter import Tcl
import ast
import json
import os, sys
# sys.path.append('..')
# from Field import *

env_tcl_path = 'test_1.tcl'
# env_tcl_path = '/home/liuyunqi/huangtao/ap/build/addrmap/block/ralf/excel_parse.ralf'

with open(env_tcl_path,'r') as f:
    env_tcl_code = f.read()

tcl_interpreter = Tcl()
tcl_interpreter.eval("source ralf_parser.tcl")
tcl_interpreter.eval(env_tcl_code)

py_dict = {}

from ralf_parser import build_addrspace
build_addrspace()
print(py_dict)
