Head = '''
import sys
sys.path.append('.')
from address_planner import *

regBank = RegSpace(name='{name}',size={size}*KB,description="{description}",bus_width={width},software_interface='{interface}')
'''
Reg = '''
reg_{cnt} = {Register}(name='{name}',description="{Description}",reg_type={RegType}, parity={Parity}, rst_domain='{ResetDomain}')
'''
RegCfg = '''
reg_{cnt}.add({Field}Field(name='{name}',bit={bit},sw_access={SoftwareAccess}, hw_access={HardwareAccess},init_value={initValue},description="{description}" ),offset={offset},lock_list={lockList})
'''
MagicRegCfg = '''
reg_{cnt}.add_magic(bit={bit}, password={MagicValue}, init_value={initValue})
'''
LockRefCfg = '''
reg_{cnt}.add(LockField('{name}', bit={bit},description="{description}"), offset={offset})
'''
IntrRegCfg = '''
reg_{cnt}.add_intr_field(name='{name}', bit={bit},init_value={initValue}, enable_init_value={enableInitValue}, description='{description}', offset={offset})
'''
IntrMaskRegCfg = '''
reg_{cnt}.add_intr_field(name='{name}', bit={bit},init_value={initValue}, enable_init_value={enableInitValue}, mask_init_value={maskInitValue}, description='{description}', offset={offset})
'''
ADD= '''
regBank.{add}(reg_{cnt}, offset={OffsetAddress}, lock_list={lockList}, magic_list={magicList})
'''
Gen = '''
if __name__ == '__main__':
    regBank.generate('{build}')
'''
Check = '''
regBank.check('{build}')
'''
