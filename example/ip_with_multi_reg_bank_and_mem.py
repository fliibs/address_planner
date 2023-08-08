import sys
sys.path.append('.')
from address_planner import *

###################################################
# Define ip_B
#
#   ip_B contains a mem and a reg space
###################################################

# declare ip_B with 4KB space.
ip_B = AddressSpace(name='ip_B',size=4*KB,description='ip_B,contains mem_B and reg_bank_B.')  

# declare mem_B with 2KB space
mem_B = AddressSpace(name='mem_B',size=2*KB,description='mem_B,size 2KB.')

# declare reg bank for ip_B
reg_bank_B = RegSpace(name='reg_bank_B',size=1*KB,description='reg_bank_B,contain many regs.')

# declare reg_B
reg_B = Register(name='regB',bit=32,description='contain many fields.')
# add many field to reg_B
reg_B.add_incr(ExternalField(name='field0',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0,ext read only.'))
reg_B.add_incr(ExternalField(name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'))
reg_B.add_incr(ExternalField(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,ext read write.'))
reg_B.add_incr(Field(name='field3',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,description='fied0,read only.'))
reg_B.add_incr(Field(name='field4',bit=1,sw_access=ReadWrite,hw_access=WriteOnly,description='fied0,write only.'))
reg_B.add_incr(Field(name='field5',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,read write.'))

#add reg0 and reg1(inst from reg_B) to reg_bank_B
reg_bank_B.add_incr(reg_B,'reg0')
reg_bank_B.add_incr(reg_B,'reg1')


ip_B.add(mem_B,name='mem',offset=0*KB)
ip_B.add(reg_bank_B,name='rb0',offset=2*KB)
ip_B.add(reg_bank_B,name='rb1',offset=3*KB)


ip_B.path = ('build/example/%s' % ip_B.module_name)
ip_B.clean_dir()
ip_B.build_dir()
ip_B.report_html()
ip_B.report_chead()
ip_B.report_vhead()
ip_B.check_chead()