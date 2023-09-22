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
reg_{cnt}.add(Field(name='{name}',bit={bit},sw_access={SoftwareAccess}, hw_access={HardwareAccess},init_value={initValue},description="{description}" ),offset={offset})
'''
ADD= '''
regBank.add(reg_{cnt},{OffsetAddress},'{name}')
'''
Gen = '''
regBank.generate('{name}')
'''
Check = '''
regBank.check('{name}')
'''