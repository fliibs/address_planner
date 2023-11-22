import os,sys 
sys.path.append('.')
from address_planner import *

u_ap = import_inst('example/addrmap/get_addr_map.py','u_ap')

u_ap_l2 = AddressSpace(name='block_outer', size=80*KB, description='l2')

u_ap_l2.add(u_ap, 0, 'inner_inst_1')
u_ap_l2.add(u_ap, 40*KB, 'inner_inst_2')

u_ap_l2.generate('build/addrmap')