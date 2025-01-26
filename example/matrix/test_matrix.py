import sys
sys.path.append('.')
from address_planner import *


interconnect_0 = AddressSpace('interconnect')

master_0 = MatrixSpace('npu',  bus_width=40, data_width=1024, software_interface='AXI4')
master_1 = MatrixSpace('mem bus',  bus_width=40, data_width=256, software_interface='AXI4')
mst_attr_0 = MstMatrixAttr(name='ocm attr', support_incr=True, support_wrap=True, others='xxxx')
mst_attr_1 = MstMatrixAttr(name='ocm attr', support_incr=True, support_wrap=True, rd_enable=False, wr_enable=False)
master_0.add_attr(mst_attr_0)
master_1.add_attr(mst_attr_1)

ocm_attr = SlvMatrixAttr(name='ocm attr', support_incr=True, support_wrap=True, others='yyyy')
ddr_attr = SlvMatrixAttr(name='ddr attr', support_incr=True, support_wrap=True, wr_bandwidth='this is an example', others='yyyy')

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


interconnect_0.add_matrix(master_0, 'npu_0')
interconnect_0.add_matrix(master_0, 'npu_1')
interconnect_0.add_matrix(master_0, 'npu_2')
interconnect_0.add_matrix(master_1, 'mem_bus')

interconnect_0.report_matrix('build')
interconnect_0.generate_matrix_excel('build')
master_0.generate_matrix_excel('build')

# import openpyxl
# from address_planner.address_planner_rtl.MatrixCFG import *


# wb = openpyxl.Workbook()
# ws0 = wb.active
# ws0.title = "Master"

# headers0 = list(master_mapping.keys())
# ws0.append(headers0)

# mapping_dict0 = master_0.report_master_matrix()

# for key, values in mapping_dict0.items():
#     row = values
#     ws0.append(row)
    
# ws1 = wb.create_sheet(title="Slave")
# headers1 = list(slave_mapping.keys())
# ws1.append(headers1)
    
# mapping_dict1 = master_0.report_slave_matrix()
# for key, values in mapping_dict1.items():
#     row = values
#     ws1.append(row)
    
# ws2 = wb.create_sheet(title="Interconnect")
# mapping_dict2 = master_0.report_interconnect_matrix()
# headers2 = ['name'] + list(mapping_dict2['name'])
# ws2.append(headers2)

# for key in mapping_dict2.keys():
#     if key == 'name':   continue
#     row = list([key] + mapping_dict2[key])
#     ws2.append(row)



# wb.save("build/mapping_data.xlsx")