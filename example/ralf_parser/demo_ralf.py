import sys
sys.path.append('.')
from address_planner import *


mem_B = AddressSpace(name='mem_B',size=128*MB)
mem_B.add_ralf(ralf_file='/home/liuyunqi/huangtao/ap/address_planner/ralf_parser/test.ralf',name='test',offset=0*KB)
mem_B.generate('build/ralf')