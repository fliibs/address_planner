
from tkinter import Tcl
import sys, re

env_tcl_path = 'test.tcl'
# env_tcl_path = '/home/liuyunqi/huangtao/ap/build/addrmap/block/ralf/excel_parse.ralf'

with open(env_tcl_path,'r') as f:
    env_tcl_code = f.read()

env_tcl_code = env_tcl_code.replace("[","").replace("]","")
env_tcl_code = re.sub(r'\([^)]*\)', '', env_tcl_code)

tcl_interpreter = Tcl()
tcl_interpreter.eval("source ralf_parser.tcl")
tcl_interpreter.eval(env_tcl_code)




