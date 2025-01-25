import sys
sys.path.append('.')
from address_planner import *


interconnect_0 = AddressSpace('interconnect')

master_0 = MatrixSpace('npu 0',  bus_width=40, data_width=1024, software_interface='AXI4')
master_1 = MatrixSpace('npu 1',  bus_width=40, data_width=1024, software_interface='AXI4')
master_2 = MatrixSpace('npu 2',  bus_width=40, data_width=1024, software_interface='AXI4')
master_3 = MatrixSpace('mem bus',bus_width=40, data_width=1024, software_interface='AXI4')


mst_attr = MstMatrixAttr(name='ocm attr', support_incr=True, support_wrap=True, others='xxxx')
master_0.add_attr(mst_attr)

ocm_attr = SlvMatrixAttr(name='ocm attr', support_incr=True, support_wrap=True, others='yyyy')
ddr_attr = SlvMatrixAttr(name='ddr attr', support_incr=True, support_wrap=True, others='yyyy')


ocm        = MatrixSpace('ocm'   , size=8*MB  , bus_width=40, data_width=1024, software_interface='AXI4')
ddr        = MatrixSpace('ddr'   , size=64*GB , bus_width=40, data_width=1024, software_interface='AXI4')
ddr_sub_0  = MatrixSpace('dram 0', size=2*GB  , bus_width=40, data_width=1024, software_interface='AXI4')
ddr_sub_1  = MatrixSpace('dram 0', size=30*GB , bus_width=40, data_width=1024, software_interface='AXI4')
ddr_sub_2  = MatrixSpace('dram 0', size=32*GB , bus_width=40, data_width=1024, software_interface='AXI4')


ddr.add(ddr_sub_0,'dram 0', ddr_attr, 0x0080000000)
ddr.add(ddr_sub_1,'dram 1', ddr_attr, 0x0880000000)
ddr.add(ddr_sub_2,'dram 2', ddr_attr, 0x8800000000)

master_0.add(ddr, "ddr", ddr_attr)
master_0.add(ocm, 'ocm 0', ocm_attr, 0x0011000000)
master_0.add_incr(ocm, 'ocm 1', ocm_attr)
master_0.add_incr(ocm, 'ocm 2', ocm_attr)

master_1.add(ddr, "ddr", ddr_attr)
master_1.add(ocm, 'ocm 0', ocm_attr, 0x0011000000)
master_1.add_incr(ocm, 'ocm 1', ocm_attr)
master_1.add_incr(ocm, 'ocm 2', ocm_attr)

master_2.add(ddr, "ddr", ddr_attr)
master_2.add(ocm, 'ocm 0', ocm_attr, 0x0011000000)
master_2.add_incr(ocm, 'ocm 1', ocm_attr)
master_2.add_incr(ocm, 'ocm 2', ocm_attr)

master_3.add(ddr, "ddr", ddr_attr)
master_3.add(ocm, 'ocm 0', ocm_attr, 0x0011000000)
master_3.add_incr(ocm, 'ocm 1', ocm_attr)
master_3.add_incr(ocm, 'ocm 2', ocm_attr)


interconnect_0.add_matrix(master_0)
interconnect_0.add_matrix(master_1)
interconnect_0.add_matrix(master_2)
interconnect_0.add_matrix(master_3)

print(interconnect_0.report_interconnect())
# print(interconnect_0.report_slave())
print(master_0.report_master_matrix())
interconnect_0.report_matrix('build')