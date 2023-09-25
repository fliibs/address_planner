import sys
sys.path.append('.')
from address_planner import *

# declare reg bank for ip_B
reg_bank_B = RegSpace(name='all_kinds',size=1*KB,description='reg_bank_B,contain many regs.')

# declare reg_B
reg_B = Register(name='regB',bit=32,description='test for software, contain many fields.')
# add many field to reg_B
reg_B.add_incr(Field(name='field0',bit=1,sw_access=ReadOnly,hw_access=ReadWrite, description='sw read only.'))
reg_B.add_incr(Field(name='field1',bit=2,sw_access=ReadSet,hw_access=ReadWrite,description='sw read set.'))
reg_B.add_incr(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='sw read write.'))
reg_B.add_incr(Field(name='field3',bit=1,sw_access=ReadClean,hw_access=ReadWrite,description='sw read clean.'))
# reg_B.add_incr(Field(name='field3',bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='hw read only.'))
# reg_B.add_incr(Field(name='field4',bit=1,sw_access=ReadWrite,hw_access=WriteOnly,description='hw write only.'))
# reg_B.add_incr(Field(name='field5',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='hw read write.'))
reg_B.add_incr(Field(name='field4',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='sw write only.'))
reg_B.add_incr(Field(name='field5',bit=1,sw_access=WriteReadClean,hw_access=ReadWrite,description='sw read clean write.'))
reg_B.add_incr(Field(name='field6',bit=1,sw_access=WriteClean,hw_access=ReadWrite,description='sw write clean.'))
reg_B.add_incr(Field(name='field7',bit=2,sw_access=Write1Clean,hw_access=ReadWrite,description='sw write one clean.'))
reg_B.add_incr(Field(name='field8',bit=2,sw_access=WriteReadSet,hw_access=ReadWrite,description='sw read set write.'))
reg_B.add_incr(Field(name='field9',bit=2,sw_access=Write0Clean,hw_access=ReadWrite,description='sw write zero clean.'))
reg_B.add_incr(Field(name='field10',bit=2,sw_access=WriteSet,hw_access=ReadWrite,description='sw write set.'))
reg_B.add_incr(Field(name='field11',bit=2,sw_access=Write1Set,hw_access=ReadWrite,description='sw write one set.'))
reg_B.add_incr(Field(name='field12',bit=2,sw_access=Write0Set,hw_access=ReadWrite,description='sw write zero set.'))
reg_B.add_incr(Field(name='field13',bit=2,sw_access=Write1Toggle,hw_access=ReadWrite,description='sw write one toggle.'))
reg_B.add_incr(Field(name='field14',bit=2,sw_access=Write0Toggle,hw_access=ReadWrite,description='sw write zero toggle.'))


reg_C = Register(name='regC',bit=32,description='test for software, contain many regs.')
reg_C.add_incr(Field(name='field15',bit=2,sw_access=WriteOnlyClean,hw_access=ReadWrite,description='sw write only clean.'))
reg_C.add_incr(Field(name='field16',bit=2,sw_access=WriteOnlySet,hw_access=ReadWrite,description='sw write only set.'))
reg_C.add_incr(Field(name='field17',bit=2,sw_access=WriteCleanReadSet,hw_access=ReadWrite,description='sw write clean read set.'))
reg_C.add_incr(Field(name='field18',bit=2,sw_access=Write1CleanReadSet,hw_access=ReadWrite,description='sw write 1 clean read set.'))
reg_C.add_incr(Field(name='field19',bit=2,sw_access=Write0CleanReadSet,hw_access=ReadWrite,description='sw write 0 clean read set.'))
reg_C.add_incr(Field(name='field20',bit=2,sw_access=WriteSetReadClean,hw_access=ReadWrite,description='sw write set read clean.'))
reg_C.add_incr(Field(name='field21',bit=2,sw_access=Write1SetReadClean,hw_access=ReadWrite,description='sw write 1 set read clean.'))
reg_C.add_incr(Field(name='field22',bit=2,sw_access=Write0SetReadClean,hw_access=ReadWrite,description='sw write 0 set read clean.'))
reg_C.add_incr(Field(name='field23',bit=2,sw_access=WriteOnce,hw_access=ReadWrite,description='sw write once.'))
reg_C.add_incr(Field(name='field24',bit=2,sw_access=WriteOnlyOnce,hw_access=ReadWrite,description='sw write only once.'))

# reg_bank_C = RegSpace(name='hardware_all_kinds',size=1*KB,description='reg_bank_C,contain many regs.')
reg_D = Register(name='regD',bit=32,description='test for software, contain many fields.')
# add many field to reg_D
reg_D.add_incr(Field(name='h_field0',bit=1,hw_access=ReadOnly, description='hw read only.'))
reg_D.add_incr(Field(name='h_field1',bit=2,hw_access=ReadSet,description='hw read set.'))
reg_D.add_incr(Field(name='h_field2',bit=1,hw_access=ReadWrite,description='hw read write.'))
reg_D.add_incr(Field(name='h_field3',bit=1,hw_access=ReadClean,description='hw read clean.'))
reg_D.add_incr(Field(name='h_field4',bit=1,hw_access=WriteOnly,description='hw write only.'))
reg_D.add_incr(Field(name='h_field5',bit=1,hw_access=WriteReadClean,description='hw read clean write.'))
reg_D.add_incr(Field(name='h_field6',bit=1,hw_access=WriteClean,description='hw write clean.'))
reg_D.add_incr(Field(name='h_field7',bit=2,hw_access=Write1Clean,description='hw write one clean.'))
reg_D.add_incr(Field(name='h_field8',bit=2,hw_access=WriteReadSet,description='hw read set write.'))
reg_D.add_incr(Field(name='h_field9',bit=2,hw_access=Write0Clean,description='hw write zero clean.'))
reg_D.add_incr(Field(name='h_field10',bit=2,hw_access=WriteSet,description='hw write set.'))
reg_D.add_incr(Field(name='h_field11',bit=2,hw_access=Write1Set,description='hw write one set.'))
reg_D.add_incr(Field(name='h_field12',bit=2,hw_access=Write0Set,description='hw write zero set.'))
reg_D.add_incr(Field(name='h_field13',bit=2,hw_access=Write1Toggle,description='hw write one toggle.'))
reg_D.add_incr(Field(name='h_field14',bit=2,hw_access=Write0Toggle,description='hw write zero toggle.'))


reg_E = Register(name='regE',bit=32,description='test for hardware, contain many regs.')
reg_E.add_incr(Field(name='h_field15',bit=2,hw_access=WriteOnlyClean,description='hw write only clean.'))
reg_E.add_incr(Field(name='h_field16',bit=2,hw_access=WriteOnlySet,description='hw write only set.'))
reg_E.add_incr(Field(name='h_field17',bit=2,hw_access=WriteCleanReadSet,description='hw write clean read set.'))
reg_E.add_incr(Field(name='h_field18',bit=2,hw_access=Write1CleanReadSet,description='hw write 1 clean read set.'))
reg_E.add_incr(Field(name='h_field19',bit=2,hw_access=Write0CleanReadSet,description='hw write 0 clean read set.'))
reg_E.add_incr(Field(name='h_field20',bit=2,hw_access=WriteSetReadClean,description='hw write set read clean.'))
reg_E.add_incr(Field(name='h_field21',bit=2,hw_access=Write1SetReadClean,description='hw write 1 set read clean.'))
reg_E.add_incr(Field(name='h_field22',bit=2,hw_access=Write0SetReadClean,description='hw write 0 set read clean.'))
reg_E.add_incr(Field(name='h_field23',bit=2,hw_access=WriteOnce,description='hw write once.'))
reg_E.add_incr(Field(name='h_field24',bit=2,hw_access=WriteOnlyOnce,description='hw write only once.'))

#add reg0 and reg1(inst from reg_B) to reg_bank_B
reg_bank_B.add_incr(reg_B,'reg0')
reg_bank_B.add_incr(reg_C,'reg1')
reg_bank_B.add_incr(reg_D,'reg2')
reg_bank_B.add_incr(reg_E,'reg3')


# reg_bank_B.path = ('example_build/%s' % reg_bank_B.module_name)

reg_bank_B.generate('build/example', report_dv=True)
# reg_bank_C.path = ('example_build/%s' % reg_bank_C.module_name)
# reg_bank_C.report_json()
# reg_bank_C.report_rtl()
