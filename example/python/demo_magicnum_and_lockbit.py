import sys
sys.path.append('.')
from address_planner import *


reg_bank_B = RegSpace(name='regbank',size=8*KB,description='magic number and lock bit test',bus_width=16,software_interface='apb')

reg_locker      = Register(name="reg_locker", bit=32)
reg_locker.add(LockField('field_lock_test', bit=1), offset=2)
reg_locker.add(LockField('field_lock_test_2', bit=1), offset=3)

reg_magics      = Register(name="reg_magics", bit=32)
reg_magics.add_magic(name='field_magic',password=0xff, lock_list=['reg_locker.field_lock_test'])
reg_magics_2    = Register(name="reg_magics_2", bit=32)
reg_magics_2.add_magic(name='field_magic',password=0xff, lock_list=['reg_locker.field_lock_test'])

reg_locked      = Register(name="reg_locked", bit=32)
reg_locked.add(Field(name='test_field',bit=3), offset=3,lock_list=['reg_locker.field_lock_test'])
reg_locked.add_lock_list('reg_locker_2.field_lock_test_2')
reg_locked.add_magic_list('magics')

reg_bank_B.add_incr(reg_locker, name='reg_locker', lock_list=['reg_locker_2.field_lock_test_2'])
reg_bank_B.add_incr(reg_locker, name='reg_locker_2')
reg_bank_B.add(reg_magics, offset=128, name='magics')
reg_bank_B.add(reg_locked, offset=96, name='locked',magic_list=['magic_2'])
reg_bank_B.add_incr(reg_locked, name='locked_2')
reg_bank_B.add(reg_magics_2, offset=160,name='magic_2')


reg_bank_B.generate('build/example')

print(reg_bank_B.sub_space_list[0].lock_list)






# print(reg_bank_B.sub_space_list)
# print(reg_bank_B.sub_space_list[0].__dict__)
# print(reg_bank_B.sub_space_list[0].field_list[0].__dict__)
# print(reg_bank_B.sub_space_list[0].field_list[0].get_lock_list)
# print(reg_bank_B.sub_space_list[0].get_magic_list)






