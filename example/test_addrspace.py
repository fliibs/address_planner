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

import_inst(file_path='example/ip0/regspace_demo_0.py')



u = AddressSpace                (name="Address Space Test", size=10*KB) \
    .regspace               (name='reg_bank_tables_3',size=1*KB,description='reg_bank_B,contain few reg.', software_interface="apb", offset=1*KB)\
        .register           (name='internal_reg',       bit=32,description='contain many fields.', offset=32) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end\
        .register           (name='internal_reg_2',       bit=32,description='contain many fields.', offset=96) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end \
    .end\
    .regspace               (name='reg_bank_tables_4',size=1*KB,description='reg_bank_B,contain few reg.', software_interface="apb", offset=2*KB)\
        .register           (name='internal_reg',       bit=32,description='contain many fields.', offset=32) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end\
        .register           (name='internal_reg_2',       bit=32,description='contain many fields.', offset=96) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end \
    .end\
    .regspace               (name='reg_multifile_test',size=1*KB,description='reg_bank_B,contain few reg.', software_interface="apb", offset=5*KB)\
        .add_register       (R_0, offset=0, name='Reg0')\
        .add_register       (R_1, offset=32, name='Reg1')\
        .add_register       (R_3, offset=64, name='Reg3')\
    .end\
    .addrspace(RS_0, 3*KB, 'demo_0')\
    .generate


