import sys
sys.path.append('.')
from address_planner import *


ddr = import_inst('/home/liuyunqi/huangtao/ap/example/matrix/test_ring.py', 'ddr')

ddr_sub_0  = MatrixSpace('dram 0', size=2*GB  , bus_width=40, data_width=1024, software_interface='AXI4')
ddr_sub_1  = MatrixSpace('dram 0', size=30*GB , bus_width=40, data_width=1024, software_interface='AXI4')
ddr_sub_2  = MatrixSpace('dram 0', size=32*GB , bus_width=40, data_width=1024, software_interface='AXI4')

ddr.add(ddr_sub_0,'dram 0', 0x0080000000)
ddr.add(ddr_sub_1,'dram 1', 0x0880000000)
ddr.add(ddr_sub_2,'dram 2', 0x8800000000)

if __name__ == '__main__':
    ddr.generate_matrix_excel('build')