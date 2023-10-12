import sys
sys.path.append('.')
from address_planner import *

regBank = RegSpace(name='ast_reg8',size=16*KB,description="ast_reg",bus_width=32,software_interface='apb')

################################rg_normal_id0_read_nonsecure_permission_list_low#######################################
regOffset = 0
CycleIndex = 8

reg1 = Register(name='ast_base',description="ast_base",reg_type=Normal)
reg1.add(Field(name='ast_base_addr',bit=20,sw_access=ReadWrite, hw_access=ReadOnly,init_value=0,description="" ),offset=12)
reg1.add(Field(name='ast_base_addr_granularity',bit=12,sw_access=ReadOnly, hw_access=Null,init_value=0b111111111111,description="" ),offset=0)
for index in range(CycleIndex):
    regBank.add(reg1, regOffset,'ast_base_addr_'+str(index))
    regOffset += 4
    
    ##############################
reg2 = Register(name='ast_mask',description="ast_mask",reg_type=Normal)
reg2.add(Field(name='ast_mask_addr',bit=20,sw_access=ReadWrite, hw_access=ReadOnly,init_value=0,description="" ),offset=12)
reg2.add(Field(name='ast_mask_addr_granularity',bit=12,sw_access=ReadOnly, hw_access=Null,init_value=0b111111111111,description="" ),offset=0)
for index in range(CycleIndex):
    regBank.add(reg2, regOffset,'ast_mask_'+str(index))
    regOffset += 4
    

regTmp1 = Register(name='ast_target_l',description="ast_target_l",reg_type=Normal)
regTmp1.add(Field(name='ast_target_l',bit=20,sw_access=ReadWrite, hw_access=ReadOnly,init_value=0,description="" ),offset=12)
regTmp1.add(Field(name='ast_target_l_granularity',bit=12,sw_access=ReadOnly, hw_access=Null,init_value=0b111111111111,description="" ),offset=0)
regTmp2 = Register(name='ast_target_h',description="ast_target_h",reg_type=Normal)
regTmp2.add(Field(name='ast_target_h',bit=32,sw_access=ReadWrite, hw_access=ReadOnly,init_value=0,description="" ),offset=0)
for index in range(CycleIndex):
    regBank.add(regTmp1, regOffset,'ast_target_l_'+str(index))
    regOffset += 4
    regBank.add(regTmp2, regOffset,'ast_target_h_'+str(index))
    regOffset += 4

reg_4 = Register(name='ast_log_ctr',description="ast_log_ctr",reg_type=Normal)
reg_4.add(Field(name='bypass',bit=1,sw_access=ReadWrite, hw_access=ReadOnly,init_value=0,description="" ),offset=0)
reg_4.add(Field(name='region_en',bit=CycleIndex,sw_access=ReadWrite, hw_access=ReadOnly,init_value=0,description="" ),offset=1)
regBank.add(reg_4, regOffset,'ast_log_ctr')
regOffset += 4

regTmp = Register(name='ast_log',description="ast_log",reg_type=Normal)
regTmp.add(Field(name='ast_log',bit=32,sw_access=ReadOnly, hw_access=WriteOnly,init_value=0,description="" ),offset=0)
regBank.add(regTmp, regOffset,'ast_log')
regOffset += 4
    
reg_6 = Register(name='ast_intr',description="ast_intr",reg_type=Normal)
reg_6.add(Field(name='ast_intr_status',bit=1,sw_access=ReadWrite, hw_access=ReadWrite,init_value=0,description="" ),offset=0)
reg_6.add(Field(name='ast_intr_mask',bit=1,sw_access=ReadWrite, hw_access=ReadOnly,init_value=0,description="" ),offset=1)
regBank.add(reg_6, regOffset,'ast_intr')
regOffset += 4



regBank.generate('build/ast')