import os,sys 
sys.path.append('.')
from address_planner import *

demo_w1p = import_inst('example/python/demo_w1p.py','reg_bank_B')

u_ap = AddressSpace(name='block', size=40*KB, description='00')
u_ap.add(import_inst(get_full_path('./example/python/demo_lock.py'),'reg_bank_B'), 2*KB, 'regbank_lock')
u_ap.add(import_inst(get_full_path('./example/python/demo_lock.py'),'reg_bank_B'), 10*KB, 'regbank_lock_1')
u_ap.add(demo_w1p,  20*KB, 'regbank_w1p')
u_ap.add(import_inst('build/reg_bank_table_rf_gen.py','regBank'), 30*KB, 'excel_parse')

u_ap.generate('build/addrmap')


for addr in u_ap.filled_sub_space_list:
    print("%s, %#x, %#x"%(addr.module_name, addr.offset, addr.offset+addr.size), hex(u_ap.size))
    # for sub in addr.filled_sub_space_list:
    #     print(sub.module_name, sub.offset, sub.size)

