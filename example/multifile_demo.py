import os,sys 
sys.path.append(os.getcwd())
from address_planner import * # pylint: disable=unused-wildcard-import

add_scope(globals=globals(), locals=locals())

import_inst(file_path='example/ip0/regspace_demo_0.py')
import_inst(file_path='example/ip1/regspace_demo_1.py',
            var_list=['RS_1','RS_2'])


u_ap = AddressSpace(name='mem_B',size=5*KB,description='mem_B,size 2KB.')\
    .addrspace(RS_0, 1*KB, 'demo_0')\
    .addrspace(RS_1, 2*KB, 'demo_1')\
    .addrspace(RS_2, 4*KB, 'demo_2')\
    .generate

