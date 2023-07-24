
from address_planner import * # pylint: disable=unused-wildcard-import
from multifile_demo import *

u_ap = AddressSpace(name='mem_B',size=4*KB,description='mem_B,size 2KB.')\
    .add_regbank(RS_0)\
    .add_regbank(RS_1)\
    .generate
# RS_0.generate

# print(u_ap.__dict__)
