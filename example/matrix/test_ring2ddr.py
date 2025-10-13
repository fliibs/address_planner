import sys
sys.path.append('.')
from address_planner import *


ring_niu = import_inst('/home/liuyunqi/huangtao/ap/example/matrix/test_ring.py', 'ring_niu')

ddr = import_inst('/home/liuyunqi/huangtao/ap/example/matrix/test_ddr_xbar.py', 'ddr')

ring_niu.module_name = 'ring_niu_update'
ring_niu.update_matrix(ddr, 'ddr_0')

if __name__ == '__main__':
    ddr.generate_matrix_excel('build')
    ring_niu.generate_matrix_excel('build')