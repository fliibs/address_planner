import sys
sys.path.append('.')
from address_planner import *



reg_bank_B = RegSpace(name='reg_bank_tables_demo',size=8*KB,description='reg_bank_B,contain many regs.',bus_width=16,software_interface='apb4')

reg_A = InterruptRegister(name='internal_reg_0', description='reg0',reg_type=Intr, parity=True, rst_domain='rst_domain_a')
reg_A.add_intr_field(name='field0',bit=1,init_value=0, enable_init_value=1, description='fied0, software read only.' ,offset=0)
reg_A.add_intr_field(name='field1',bit=2,init_value=0, enable_init_value=0, description='fied1, software write only.',offset=1)
reg_A.add_intr_field(name='field2',bit=1,init_value=0, enable_init_value=0, description='fied2, software read write.',offset=3)
reg_A.add_intr_field(name='field3',bit=3,init_value=1, enable_init_value=1, description='fied3, hardware read only.' ,offset=6)
reg_bank_B.add_intr(reg_A,0x4)

reg_D = InterruptRegister(name='intr_reg_2', description='reg0',reg_type=IntrMask, parity=True, rst_domain='rst_domain_b')
reg_D.add_intr_field(name='field0',bit=1,init_value=0, enable_init_value=1, mask_init_value=1, description='fied0, software read only.' ,offset=0)
reg_D.add_intr_field(name='field1',bit=2,init_value=0, enable_init_value=0, mask_init_value=0, description='fied1, software write only.',offset=1)
reg_D.add_intr_field(name='field2',bit=1,init_value=0, enable_init_value=0, mask_init_value=0, description='fied2, software read write.',offset=3)
reg_D.add_intr_field(name='field3',bit=3,init_value=0, enable_init_value=0, mask_init_value=0, description='fied3, hardware read only.' ,offset=6)

# reg_bank_B.add_intr(reg_D,0x4+20)

reg_bank_B.generate('build/example')