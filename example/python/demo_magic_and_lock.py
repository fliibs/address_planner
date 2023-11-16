import sys
sys.path.append('.')
from address_planner import *

reg_bank_B = RegSpace(name='reg_bank_tables',size=8*KB,description='reg_bank_B,contain many regs.',bus_width=16,software_interface='apb')

internal_reg_0 = Register(name='internal_reg_0',description='reg0_0',reg_type=Normal)

internal_reg_0.add(Field(name='field0',bit=1,sw_access=ReadOnly, hw_access=ReadWrite,init_value=0,description='fied0, software read only.' ),offset=0)
internal_reg_0.add(Field(name='field1',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,init_value=0,description='fied1, software write only.'),offset=1)
internal_reg_0.add(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,init_value=0,description='fied2, software read write.'),offset=3)
internal_reg_0.add(Field(name='field3',bit=3,sw_access=ReadWrite,hw_access=ReadOnly, init_value=0,description='fied3, hardware read only.' ),offset=4)

reg_bank_B.add(internal_reg_0, offset=0x20, magic_list=['magic_reg_0','magic_reg_1'])


internal_reg_1 = Register(name='internal_reg_1',description='reg0_1',reg_type=Normal)

internal_reg_1.add(Field(name='field0',bit=1,sw_access=Write1Pulse, hw_access=ReadOnly,init_value=0,description='fied0, write one pulse.' ),offset=0, lock_list=['lock_reg_0.lock_field_1'])
internal_reg_1.add(Field(name='field1',bit=2,sw_access=Write0Pulse,hw_access=ReadOnly,init_value=0,description='fied1, write zero pulse.'),offset=1, lock_list=['lock_reg_1.lock_field_0'])
internal_reg_1.add(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,init_value=0,description='fied2, software read write.'),offset=3)
internal_reg_1.add(Field(name='field3',bit=3,sw_access=ReadWrite,hw_access=ReadOnly, init_value=0,description='fied3, hardware read only.' ),offset=4)

reg_bank_B.add(internal_reg_1, offset=0x24, lock_list=['lock_reg_0.lock_field_0'], magic_list=['magic_reg_1'])


internal_reg_2 = Register(name='internal_reg_2',description='reg0_2',reg_type=Normal)

internal_reg_2.add(Field(name='field0',bit=1,sw_access=ReadOnly, hw_access=ReadWrite,init_value=0,description='fied0, software read only.' ),offset=0)
internal_reg_2.add(Field(name='field1',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,init_value=0,description='fied1, software write only.'),offset=1)
internal_reg_2.add(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,init_value=0,description='fied2, software read write.'),offset=3)
internal_reg_2.add(Field(name='field3',bit=3,sw_access=ReadWrite,hw_access=ReadOnly, init_value=0,description='fied3, hardware read only.' ),offset=4, lock_list=['lock_reg_1.lock_field_1'])

reg_bank_B.add(internal_reg_2, offset=0x28, magic_list=['magic_reg_0'])


magic_reg_0      = Register(name="magic_reg_0",description='magic 0',reg_type=Magic)
magic_reg_0.add_magic(bit=32, password=0xff, init_value=0)

reg_bank_B.add(magic_reg_0, offset=0x80)


magic_reg_1      = Register(name="magic_reg_1",description='magic 1',reg_type=Magic)
magic_reg_1.add_magic(bit=32, password=0xff, init_value=0)

reg_bank_B.add(magic_reg_1, offset=0x84)


lock_reg_0      = Register(name="lock_reg_0",description='lock 0',reg_type=Lock)
lock_reg_0.add(LockField('lock_field_0', bit=1,description='lock field 0'), offset=0)
lock_reg_0.add(LockField('lock_field_1', bit=1,description='lock field 1'), offset=7)

reg_bank_B.add(lock_reg_0, offset=0x88)


lock_reg_1      = Register(name="lock_reg_1",description='lock 1',reg_type=Lock)
lock_reg_1.add(LockField('lock_field_0', bit=1,description='lock field 0'), offset=0)
lock_reg_1.add(LockField('lock_field_1', bit=1,description='lock field 1'), offset=6)

reg_bank_B.add(lock_reg_1, offset=0x8c)

reg_bank_B.generate('build')
# reg_bank_B.check('build')


