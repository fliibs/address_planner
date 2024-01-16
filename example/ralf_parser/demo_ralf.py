import sys
sys.path.append('.')
from address_planner import *


mem_B = AddressSpace(name='mem_B',size=128*KB)
mem_B.add_ralf('/home/liuyunqi/huangtao/ap/address_planner/ralf_parser/test.ralf',0)

mem_B.generate('build/ralf')