import sys
sys.path.append('.')
from address_planner import *


ring_niu = AddressSpace('ring_niu')


npu     = MatrixSpace('npu',  bus_width=40, data_width=1024, software_interface='AXI4')
mem_bus = MatrixSpace('mem_bus',  bus_width=40, data_width=1024, software_interface='AXI4')

npu_attr     = MstMatrixAttr(name='npu attr', support_incr=True, support_wrap=True, support_fixed=False, 
                         support_reordering=False, support_exclusive=False, max_len=1, min_size=7, 
                         w_req_auser_width=1, r_req_auser_width=1, rd_id_width=12, wr_id_width=12, rd_ost=64, wr_ost=32)
mem_bus_attr = MstMatrixAttr(name='mem bus attr', support_incr=True, support_wrap=True, support_fixed=False, 
                         support_reordering=False, support_exclusive=False, max_len=1, min_size=7, 
                         w_req_auser_width=1, r_req_auser_width=1, rd_id_width=12, wr_id_width=12, rd_ost=64, wr_ost=32)


ocm_attr = SlvMatrixAttr(name='ocm attr', support_incr=True, support_wrap=True, support_fixed=False,
                         support_reordering=False, max_len=1, min_size=7, 
                         w_req_auser_width=1, r_req_auser_width=1, rd_id_width=16, wr_id_width=16, rd_ost=512, wr_ost=512)
ddr_attr = SlvMatrixAttr(name='ddr attr', support_incr=True, support_wrap=True, support_fixed=False,
                         support_reordering=False, max_len=1, min_size=7, 
                         w_req_auser_width=1, r_req_auser_width=1, rd_id_width=16, wr_id_width=16, rd_ost=512, wr_ost=512)

ocm        = MatrixSpace('ocm'   , size=8*MB  , bus_width=40, data_width=1024, software_interface='AXI4')
ddr        = MatrixSpace('ddr'   , offset=[0x0080000000, 0x0880000000, 0x8800000000], size=[2*GB, 30*GB, 32*GB] , bus_width=40, data_width=1024, software_interface='AXI4')


npu.add_attr(npu_attr)
mem_bus.add_attr(mem_bus_attr)
ddr.add_attr(ddr_attr)
ocm.add_attr(ocm_attr)

npu.add(ddr, 'ddr_0')
npu.add(ocm, 'ocm 0', 0x0011000000)
npu.add_incr(ocm, 'ocm 1')
npu.add_incr(ocm, 'ocm 2')

mem_bus.add(ddr, 'ddr_0')
mem_bus.add(ocm, 'ocm 0', 0x0011000000, attr=ocm_attr)
mem_bus.add_incr(ocm, 'ocm 1', attr=ocm_attr)
mem_bus.add_incr(ocm, 'ocm 2', attr=ocm_attr)

ring_niu.add_matrix(npu, 'npu_0')
ring_niu.add_matrix(npu, 'npu_1')
ring_niu.add_matrix(npu, 'npu_2')
ring_niu.add_matrix(mem_bus, 'mem_bus')
ring_niu.generate_matrix_excel('build')

