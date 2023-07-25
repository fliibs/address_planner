import sys
sys.path.append('.')
from address_planner import *

# declare reg bank for ip_B
reg_bank_B = RegSpace(name='all_kinds',size=1*KB,description='reg_bank_B,contain many regs.')

# declare reg_B
reg_B = Register(name='regB',bit=32,description='contain many fields.')
# add many field to reg_B
reg_B.add_incr(Field(name='field0',bit=1,sw_access=ReadOnly,hw_access=ReadWrite, description='sw read only.'))
reg_B.add_incr(Field(name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='sw write only.'))
reg_B.add_incr(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='sw read write.'))
reg_B.add_incr(Field(name='field3',bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='hw read only.'))
reg_B.add_incr(Field(name='field4',bit=1,sw_access=ReadWrite,hw_access=WriteOnly,description='hw write only.'))
reg_B.add_incr(Field(name='field5',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='hw read write.'))
reg_B.add_incr(Field(name='field6',bit=1,sw_access=ReadClean,hw_access=ReadWrite,description='sw read clean.'))
reg_B.add_incr(Field(name='field7',bit=1,sw_access=ReadCleanWrite,hw_access=ReadWrite,description='sw read clean write.'))
reg_B.add_incr(Field(name='field8',bit=1,sw_access=WriteClean,hw_access=ReadWrite,description='sw write clean.'))
reg_B.add_incr(Field(name='field9',bit=2,sw_access=Write1Clean,hw_access=ReadWrite,description='sw write one clean.'))
reg_B.add_incr(Field(name='field10',bit=2,sw_access=ReadSet,hw_access=ReadWrite,description='sw read set.'))
reg_B.add_incr(Field(name='field11',bit=2,sw_access=ReadSetWrite,hw_access=ReadWrite,description='sw read set write.'))
reg_B.add_incr(Field(name='field12',bit=2,sw_access=Write0Clean,hw_access=ReadWrite,description='sw write zero clean.'))
reg_B.add_incr(Field(name='field13',bit=2,sw_access=WriteSet,hw_access=ReadWrite,description='sw write set.'))
reg_B.add_incr(Field(name='field14',bit=2,sw_access=Write1Set,hw_access=ReadWrite,description='sw write one set.'))
reg_B.add_incr(Field(name='field15',bit=2,sw_access=Write0Set,hw_access=ReadWrite,description='sw write zero set.'))
reg_B.add_incr(Field(name='field16',bit=2,sw_access=Write1Toggle,hw_access=ReadWrite,description='sw write one toggle.'))
reg_B.add_incr(Field(name='field17',bit=1,sw_access=Write0Toggle,hw_access=ReadWrite,description='sw write zero toggle.'))

#add reg0 and reg1(inst from reg_B) to reg_bank_B
reg_bank_B.add_incr(reg_B,'reg0')
reg_bank_B.add_incr(reg_B,'reg1')


reg_bank_B.path = ('example_build/%s' % reg_bank_B.module_name)
reg_bank_B.clean_dir()
reg_bank_B.build_dir()
reg_bank_B.report_html()
reg_bank_B.report_chead()
reg_bank_B.report_vhead()
reg_bank_B.check_chead()
reg_bank_B.report_json()
reg_bank_B.report_rtl()
