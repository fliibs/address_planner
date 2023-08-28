import os,sys 
sys.path.append(os.getcwd())
from address_planner import * # pylint: disable=unused-wildcard-import

sys.path.append(os.getcwd()+'/example/tablelike')


RS_0 = import_inst('ip0/ip_0_0/regspace_demo_0.py','RS_0')
RS_1 = import_inst('ip1/regspace_demo_1.py','RS_1')
RS_2 = import_inst('ip1/regspace_demo_1.py','RS_2')

u_ap = AddressSpace(name='mem_B',size=5*KB,description='mem_B,size 2KB.')\
    .addrspace(RS_0, 0*KB, 'demo_0')\
    .addrspace(RS_1, 2*KB, 'demo_1')\
    .addrspace(RS_2, 3*KB, 'demo_2')

u_ap.generate('build/example')