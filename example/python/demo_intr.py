import sys
sys.path.append('.')
from address_planner import *


reg_bank_B = RegSpace(name='reg_bank_intr_test',size=8*KB,description='reg_bank_B,contain many regs.',bus_width=16,software_interface='apb')


reg_B = InterruptRegister(name='intr_reg', description='reg0',reg_type=Intr)

reg_B.add_intr_field(name='field0',bit=1,init_value=0,description='fied0, software read only.' ,offset=0)
reg_B.add_intr_field(name='field1',bit=2,init_value=0,description='fied1, software write only.',offset=1)
reg_B.add_intr_field(name='field2',bit=1,init_value=0,description='fied2, software read write.',offset=3)
reg_B.add_intr_field(name='field3',bit=3,init_value=0,description='fied3, hardware read only.' ,offset=6)

reg_C = Register(name='external_reg',description='reg1',reg_type=Normal)

reg_C.add(ExternalField(name='field0',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied0, external hardware read only.' ),offset=1)
reg_C.add(ExternalField(name='field1',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied1, external hardware write only.'),offset=3)
reg_C.add(ExternalField(name='field2',bit=3,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied2, external hardware read write.'),offset=7)
reg_C.add(ExternalField(name='field3',bit=4,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0,description='fied3, external hardware read only.' ),offset=11)

reg_bank_B.add_intr(reg_B,0x4)

reg_bank_B.add_incr(reg_C)
for sub in reg_bank_B.sub_space_list:
    print(sub)

reg_bank_B.generate('build/example')