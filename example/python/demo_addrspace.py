import sys
sys.path.append('.')
from address_planner import *


addr_space = AddressSpace(name='total', size = 8*MB)

reg_bank_B = RegSpace(name='reg_bank_tables_demo',size=8*KB,description='reg_bank_B,contain many regs.',bus_width=16,software_interface='apb4')

reg_B = Register(name='internal_reg',bit=32, description='reg0',reg_type=Normal)

reg_B.add(Field(name='field0',bit=1,sw_access=ReadOnly, hw_access=ReadWrite,init_value=0,description='fied0, software read only.' ),offset=0)
reg_B.add(Field(name='field1',bit=2,sw_access=Write1Clean,hw_access=Null,init_value=0,description='fied1, software write only.'),offset=1)
reg_B.add(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,init_value=0,description='fied2, software read write.'),offset=3)
reg_B.add(Field(name='field3',bit=3,sw_access=ReadWrite,hw_access=ReadOnly, init_value=0,description='fied3, hardware read only.' ),offset=6)

reg_C = Register(name='external_reg',description='reg1',reg_type=Normal)

reg_C.add(ExternalField(name='field0',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied0, external hardware read only.' ),offset=1)
reg_C.add(ExternalField(name='field1',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied1, external hardware write only.'),offset=3)
reg_C.add(ExternalField(name='field2',bit=3,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied2, external hardware read write.'),offset=7)
reg_C.add(ExternalField(name='field3',bit=4,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied3, external hardware read only.' ),offset=11)

reg_bank_B.add(reg_B,0x4,'internal_reg')
reg_bank_B.add(reg_C,0xc,'external_reg')


addr_space.add(reg_bank_B, 8*KB, 'sub_1')
p


for addr in addr_space.filled_sub_space_list:
    print(addr.module_name, hex(int(addr.global_offset/8)), addr.size)
    for sub in addr.filled_sub_space_list:
        print(sub.module_name, hex(int(sub.global_offset/8)), sub.size)


addr_space.generate('build/example')