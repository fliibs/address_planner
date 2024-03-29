import sys
sys.path.append('.')
from address_planner import *


reg_bank_B = RegSpace(name='regbank_pulse',size=8*KB,description='write one pulse test',bus_width=16,software_interface='apb')

reg_B = Register(name='internal_reg',description='reg0',reg_type=Normal)
reg_B.add_incr(Field(name='w1pulse',bit=10,sw_access=Write1Pulse, hw_access=ReadOnly,init_value=0,description='fied0, software write one pulse.' ))
reg_B.add_incr(Field(name='w0pulse',bit=10,sw_access=Write0Pulse, hw_access=ReadOnly,init_value=0,description='fied0, software write one pulse.' ))

reg_bank_B.add(reg_B,0x4,'internal_reg')
reg_bank_B.generate('build/example')