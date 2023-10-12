import sys
sys.path.append('.')
from address_planner import *



reg_bank_B = RegSpace(name='regbank_pulse_lock',size=8*KB,description='write one pulse test',bus_width=16,software_interface='apb')


reg_locker      = Register(name="reg_locker", bit=32)
reg_locker.add(LockField('field_lock_test', bit=1), offset=2)
reg_locker.add(LockField('field_lock_test_2', bit=1), offset=3)

reg_B = Register(name='internal_reg',description='reg0',reg_type=Normal)
reg_B.add_incr(Field(name='w1pulse',bit=10,sw_access=Write1Pulse, hw_access=ReadOnly,init_value=0,description='fied0, software write one pulse.' ))
reg_B.add_incr(Field(name='w0pulse',bit=10,sw_access=Write0Pulse, hw_access=ReadOnly,init_value=0,description='fied0, software write one pulse.' ),lock_list=[['reg_locker', 'field_lock_test']])

reg_B.add_lock_list(['reg_locker_2', 'field_lock_test_2'])


reg_bank_B.add(reg_locker, 0x12, 'reg_locker')
reg_bank_B.add(reg_B,0x4,'internal_reg')
reg_bank_B.add(reg_locker, 0x8, 'reg_locker_2')
reg_bank_B.generate('build/example')

