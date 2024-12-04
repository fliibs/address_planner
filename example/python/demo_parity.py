import sys
sys.path.append('.')
from address_planner import *



reg_bank_B = RegSpace(name='reg_bank_tables_demo',size=8*KB,description='reg_bank_B,contain many regs.',bus_width=16,software_interface='apb4')

reg_A = Register(name='internal_reg_0',bit=32, description='reg0',reg_type=Normal, parity=True, rst_domain='rst_domain_a')

reg_A.add(Field(name='field0',bit=2,sw_access=Null,hw_access=Null,init_value=1,description='fied0, Null.' ),offset=0)
reg_A.add(Field(name='field1',bit=2,sw_access=Null,hw_access=ReadWrite,init_value=1,description='fied1, ReadWrite.'),offset=2)
reg_A.add(Field(name='field2',bit=2,sw_access=Null,hw_access=ReadOnly,init_value=1,description='fied2, ReadOnly.'),offset=4)
reg_A.add(Field(name='field3',bit=2,sw_access=Null,hw_access=ReadClean, init_value=0,description='fied3, ReadClean.' ),offset=6)
reg_A.add(Field(name='field4',bit=2,sw_access=Null,hw_access=WriteReadSet, init_value=1,description='fied3, WriteReadSet.' ),offset=8)
reg_A.add(Field(name='field5',bit=2,sw_access=Null,hw_access=WriteClean,init_value=1,description='fied0, WriteClean.' ),offset=10)
reg_A.add(Field(name='field6',bit=2,sw_access=Null,hw_access=WriteCleanReadSet,init_value=1,description='fied1, WriteCleanReadSet.'),offset=12)
reg_A.add(Field(name='field7',bit=2,sw_access=Null,hw_access=Write1CleanReadSet,init_value=1,description='fied2, Write1CleanReadSet.'),offset=14)
reg_A.add(Field(name='field8',bit=2,sw_access=Null,hw_access=Write1Toggle, init_value=0,description='fied3, Write1Toggle.' ),offset=16)
reg_A.add(Field(name='field9',bit=2,sw_access=Null,hw_access=WriteOnce, init_value=1,description='fied3, WriteOnce.' ),offset=18)

reg_B = Register(name='internal_reg_2',bit=32, description='reg0',reg_type=Normal, parity=True, rst_domain='rst_domain_b')

reg_B.add(Field(name='field0',bit=2,sw_access=Null,hw_access=Null,init_value=1,description='fied0, Null.' ),offset=0)
reg_B.add(Field(name='field1',bit=2,sw_access=ReadWrite,hw_access=Null,init_value=1,description='fied1, ReadWrite.'),offset=2)
reg_B.add(Field(name='field2',bit=2,sw_access=ReadOnly,hw_access=Null,init_value=1,description='fied2, ReadOnly.'),offset=4)
reg_B.add(Field(name='field3',bit=2,sw_access=ReadClean,hw_access=Null, init_value=0,description='fied3, ReadClean.' ),offset=6)
reg_B.add(Field(name='field4',bit=2,sw_access=WriteReadSet,hw_access=Null, init_value=1,description='fied3, WriteReadSet.' ),offset=8, lock_list=["internal_reg_3.field_lock_test"])
reg_B.add(Field(name='field5',bit=2,sw_access=WriteClean,hw_access=Null,init_value=1,description='fied0, WriteClean.' ),offset=10)
reg_B.add(Field(name='field6',bit=2,sw_access=WriteCleanReadSet,hw_access=Null,init_value=1,description='fied1, WriteCleanReadSet.'),offset=12)
reg_B.add(Field(name='field7',bit=2,sw_access=Write1CleanReadSet,hw_access=Null,init_value=1,description='fied2, Write1CleanReadSet.'),offset=14)
reg_B.add(Field(name='field8',bit=2,sw_access=Write1Toggle,hw_access=Null, init_value=0,description='fied3, Write1Toggle.' ),offset=16)
reg_B.add(Field(name='field9',bit=2,sw_access=WriteOnce,hw_access=Null, init_value=1,description='fied3, WriteOnce.' ),offset=18)

reg_C = Register(name='internal_reg_3',bit=32, description='reg0',reg_type=Normal, parity=True, rst_domain='rst_domain_c')

reg_C.add(Field(name='field0',bit=2,sw_access=Null,hw_access=Null,init_value=1,description='fied0, Null.' ),offset=0)
reg_C.add(Field(name='field1',bit=2,sw_access=ReadWrite,hw_access=ReadWrite,init_value=1,description='fied1, ReadWrite.'),offset=2)
reg_C.add(Field(name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadOnly,init_value=1,description='fied2, ReadOnly.'),offset=4)
reg_C.add(Field(name='field3',bit=2,sw_access=ReadClean,hw_access=ReadClean, init_value=0,description='fied3, ReadClean.' ),offset=6)
reg_C.add(Field(name='field4',bit=2,sw_access=WriteReadSet,hw_access=WriteReadSet, init_value=1,description='fied3, WriteReadSet.' ),offset=8)
reg_C.add(Field(name='field5',bit=2,sw_access=WriteClean,hw_access=WriteClean,init_value=1,description='fied0, WriteClean.' ),offset=10)
reg_C.add(Field(name='field6',bit=2,sw_access=WriteCleanReadSet,hw_access=WriteCleanReadSet,init_value=1,description='fied1, WriteCleanReadSet.'),offset=12)
reg_C.add(Field(name='field7',bit=2,sw_access=Write1CleanReadSet,hw_access=Write1CleanReadSet,init_value=1,description='fied2, Write1CleanReadSet.'),offset=14)
reg_C.add(Field(name='field8',bit=2,sw_access=Write1Toggle,hw_access=Write1Toggle, init_value=0,description='fied3, Write1Toggle.' ),offset=16)
reg_C.add(Field(name='field9',bit=2,sw_access=WriteOnce,hw_access=WriteOnce, init_value=1,description='fied3, WriteOnce.' ),offset=18)
reg_C.add(LockField('field_lock_test', bit=1), offset=20)

reg_ext_A = Register(name='external_reg_0',bit=32, description='reg0',reg_type=Normal, parity=True, rst_domain='rst_domain_a_ext')

reg_ext_A.add(ExternalField(name='field0',bit=2,sw_access=Null,hw_access=Null,init_value=1,description='fied0, Null.' ),offset=0)
reg_ext_A.add(ExternalField(name='field1',bit=2,sw_access=Null,hw_access=ReadWrite,init_value=1,description='fied1, ReadWrite.'),offset=2)
reg_ext_A.add(ExternalField(name='field2',bit=2,sw_access=Null,hw_access=ReadOnly,init_value=1,description='fied2, ReadOnly.'),offset=4)
reg_ext_A.add(ExternalField(name='field3',bit=2,sw_access=Null,hw_access=ReadClean, init_value=0,description='fied3, ReadClean.' ),offset=6)
reg_ext_A.add(ExternalField(name='field4',bit=2,sw_access=Null,hw_access=WriteReadSet, init_value=1,description='fied3, WriteReadSet.' ),offset=8)
reg_ext_A.add(ExternalField(name='field5',bit=2,sw_access=Null,hw_access=WriteClean,init_value=1,description='fied0, WriteClean.' ),offset=10)
reg_ext_A.add(ExternalField(name='field6',bit=2,sw_access=Null,hw_access=WriteCleanReadSet,init_value=1,description='fied1, WriteCleanReadSet.'),offset=12)
reg_ext_A.add(ExternalField(name='field7',bit=2,sw_access=Null,hw_access=Write1CleanReadSet,init_value=1,description='fied2, Write1CleanReadSet.'),offset=14)
reg_ext_A.add(ExternalField(name='field8',bit=2,sw_access=Null,hw_access=Write1Toggle, init_value=0,description='fied3, Write1Toggle.' ),offset=16)
reg_ext_A.add(ExternalField(name='field9',bit=2,sw_access=Null,hw_access=WriteOnce, init_value=1,description='fied3, WriteOnce.' ),offset=18)

reg_ext_B = Register(name='external_reg_2',bit=32, description='reg0',reg_type=Normal, parity=False, rst_domain='rst_domain_b_ext')

reg_ext_B.add(ExternalField(name='field0',bit=2,sw_access=Null,hw_access=Null,init_value=1,description='fied0, Null.' ),offset=0)
reg_ext_B.add(ExternalField(name='field1',bit=2,sw_access=ReadWrite,hw_access=Null,init_value=1,description='fied1, ReadWrite.'),offset=2)
reg_ext_B.add(ExternalField(name='field2',bit=2,sw_access=ReadOnly,hw_access=Null,init_value=1,description='fied2, ReadOnly.'),offset=4)
reg_ext_B.add(ExternalField(name='field3',bit=2,sw_access=ReadClean,hw_access=Null, init_value=0,description='fied3, ReadClean.' ),offset=6)
reg_ext_B.add(ExternalField(name='field4',bit=2,sw_access=WriteReadSet,hw_access=Null, init_value=1,description='fied3, WriteReadSet.' ),offset=8)
reg_ext_B.add(ExternalField(name='field5',bit=2,sw_access=WriteClean,hw_access=Null,init_value=1,description='fied0, WriteClean.' ),offset=10)
reg_ext_B.add(ExternalField(name='field6',bit=2,sw_access=WriteCleanReadSet,hw_access=Null,init_value=1,description='fied1, WriteCleanReadSet.'),offset=12)
reg_ext_B.add(ExternalField(name='field7',bit=2,sw_access=Write1CleanReadSet,hw_access=Null,init_value=1,description='fied2, Write1CleanReadSet.'),offset=14)
reg_ext_B.add(ExternalField(name='field8',bit=2,sw_access=Write1Toggle,hw_access=Null, init_value=0,description='fied3, Write1Toggle.' ),offset=16)
reg_ext_B.add(ExternalField(name='field9',bit=2,sw_access=WriteOnce,hw_access=Null, init_value=1,description='fied3, WriteOnce.' ),offset=18)

reg_ext_C = Register(name='external_reg_3',bit=32, description='reg0',reg_type=Normal, parity=True, rst_domain='rst_domain_c_ext')

reg_ext_C.add(ExternalField(name='field0',bit=2,sw_access=Null,hw_access=Null,init_value=1,description='fied0, Null.' ),offset=0)
reg_ext_C.add(ExternalField(name='field1',bit=2,sw_access=ReadWrite,hw_access=ReadWrite,init_value=1,description='fied1, ReadWrite.'),offset=2)
reg_ext_C.add(ExternalField(name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadOnly,init_value=1,description='fied2, ReadOnly.'),offset=4)
reg_ext_C.add(ExternalField(name='field3',bit=2,sw_access=ReadClean,hw_access=ReadClean, init_value=0,description='fied3, ReadClean.' ),offset=6)
reg_ext_C.add(ExternalField(name='field4',bit=2,sw_access=WriteReadSet,hw_access=WriteReadSet, init_value=1,description='fied3, WriteReadSet.' ),offset=8)
reg_ext_C.add(ExternalField(name='field5',bit=2,sw_access=WriteClean,hw_access=WriteClean,init_value=1,description='fied0, WriteClean.' ),offset=10)
reg_ext_C.add(ExternalField(name='field6',bit=2,sw_access=WriteCleanReadSet,hw_access=WriteCleanReadSet,init_value=1,description='fied1, WriteCleanReadSet.'),offset=12)
reg_ext_C.add(ExternalField(name='field7',bit=2,sw_access=Write1CleanReadSet,hw_access=Write1CleanReadSet,init_value=1,description='fied2, Write1CleanReadSet.'),offset=14)
reg_ext_C.add(ExternalField(name='field8',bit=2,sw_access=Write1Toggle,hw_access=Write1Toggle, init_value=0,description='fied3, Write1Toggle.' ),offset=16)
reg_ext_C.add(ExternalField(name='field9',bit=2,sw_access=WriteOnce,hw_access=WriteOnce, init_value=1,description='fied3, WriteOnce.' ),offset=18)

reg_bank_B.add(reg_A,0x0)
reg_bank_B.add(reg_B,0x4)
reg_bank_B.add(reg_C,0x8)
reg_bank_B.add(reg_ext_A,0x10)
reg_bank_B.add(reg_ext_B,0x14)
reg_bank_B.add(reg_ext_C,0x18)



reg_bank_B.generate('build/example')