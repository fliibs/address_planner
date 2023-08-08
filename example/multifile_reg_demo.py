# First, add head.
import os,sys 
sys.path.append(os.getcwd())
from address_planner import * # pylint: disable=unused-wildcard-import

# use "import_inst" to import register instance.
# file_path   : file path of ip.
# module_name : register instance list which will import to python file.
R_0 = import_inst(file_path='ip0/register_demo_0.py', module_name='R_0')
R_1 = import_inst(file_path='ip0/register_demo_0.py', module_name='R_1')
R_3 = import_inst(file_path='ip1/register_demo_1.py', module_name='R_3')

# generate a regbank.
u= RegSpace                (name='reg_multifile_test',size=1*KB,description='reg_bank_B,contain few reg.', software_interface="apb")\
        .add_register   (R_0, offset=0, name='Reg0')\
        .add_register   (R_1, offset=32, name='Reg1')\
        .add_register   (R_3, offset=64, name='Reg3')\
.generate