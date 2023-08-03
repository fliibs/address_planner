# First, add head.
import os,sys 
sys.path.append(os.getcwd())
from address_planner import * # pylint: disable=unused-wildcard-import

# add extra head.
add_scope(globals=globals(), locals=locals())

# use "import_inst" to import register instance.
# file_path: file path of ip.
# var_list : register instance list which will import to python file.
import_inst(file_path='example/ip0/register_demo_0.py', var_list=['R_0', 'R_1'])
import_inst(file_path='example/ip1/register_demo_1.py',
            var_list=['R_3'])

# generate a regbank.
RegSpace                (name='reg_multifile_test',size=1*KB,description='reg_bank_B,contain few reg.', software_interface="apb")\
        .add_register   (R_0, offset=0, name='Reg0')\
        .add_register   (R_1, offset=32, name='Reg1')\
        .add_register   (R_3, offset=64, name='Reg3')\
.generate

