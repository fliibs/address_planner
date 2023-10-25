Head = '''
import sys
sys.path.append('.')
from address_planner import *

regBank = RegSpace(name='{name}',size={size}*KB,description="{description}",bus_width={width},software_interface='{interface}')
'''
Reg = '''
reg_{cnt} = Register(name='{name}',description="{Description}",reg_type={RegType})
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
ADD= '''
regBank.add(reg_{cnt},offset={OffsetAddress},lock_list={lockList},magic_list={magicList})
'''
Gen = '''
regBank.generate('build/{name}')
'''
Check = '''
regBank.check('build/{name}')
'''