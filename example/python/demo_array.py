import sys
sys.path.append('.')
from address_planner import *


reg_bank_B = RegSpace(name='reg_bank_table_array',size=8*KB,description='reg_bank_B,contain many regs.',bus_width=16,software_interface='apb')

for i in range(4):
    reg_B = Register(name=f'internal_reg_{i}',description='reg0',reg_type=Normal)

    reg_B.add(Field(name='field0',bit=1,sw_access=ReadOnly, hw_access=ReadWrite,init_value=0,description='fied0, software read only.' ),offset=0)
    reg_B.add(Field(name='field1',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,init_value=0,description='fied1, software write only.'),offset=1)
    reg_B.add(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,init_value=0,description='fied2, software read write.'),offset=3)
    reg_B.add(Field(name='field3',bit=3,sw_access=ReadWrite,hw_access=ReadOnly, init_value=0,description='fied3, hardware read only.' ),offset=6)
    reg_bank_B.add(reg_B,32+i*32,f'internal_reg_{i}')

reg_C={}
for j in range(16):
    reg_C[j] = Register(name=f'external_reg_{j}',description='reg1',reg_type=Normal)

    reg_C[j].add(ExternalField(name='field0',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied0, external hardware read only.' ),offset=1)
    reg_C[j].add(ExternalField(name='field1',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied1, external hardware write only.'),offset=3)
    reg_C[j].add(ExternalField(name='field2',bit=3,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied2, external hardware read write.'),offset=7)
    reg_C[j].add(ExternalField(name='field3',bit=4,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied3, external hardware read only.' ),offset=11)
    reg_bank_B.add(reg_C[j],352+j*32,f'external_reg_{j}')

reg_bank_B.generate('build/example')