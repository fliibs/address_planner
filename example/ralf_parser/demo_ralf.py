import sys
sys.path.append('.')
from address_planner import *

GlobalValues.Options.MultiPortOption = True

mem_B = AddressSpace(name='mem_B',size=12800*MB)
# mem_B.add_ralf(sub_space='./address_planner/ralf_parser/test.ralf', name='test', offset=0)
# mem_B.add_ralf(sub_space='/prj/gs001/ge/lixy/gs001/chip/sys/sys_vpu/de/reg/E300/IP_Registers.ralf', name='test', offset=0)
mem_B.add_ralf(sub_space='/user/huangt/Desktop/ap/v2p3/address_planner/example/ralf_parser/peri_dma_uvm.ralf', name='test', offset=0)
# mem_B.add_ralf(sub_space='/prj/gs001/de/zhangpu/ip/dev/uart/de/reg/DW_apb_uart_uvm.ralf', name='Arm', offset=160*KB)
# mem_B.add_ralf(sub_space='/user/huangt/Desktop/ap2/v2p2/address_planner/dwc_ddrphy_top.ralf', name='Arm', offset=106*MB)
mem_B.generate('build/test')
