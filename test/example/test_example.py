
import os
import importlib


def test_smoke():
    importlib.import_module('example.test')

def test_single_reg_bank():
    importlib.import_module('example.single_reg_bank')
   
def test_ip_with_multi_reg_bank_and_mem():
    importlib.import_module('example.ip_with_multi_reg_bank_and_mem')
    






#example_path = "%s/example" % os.getcwd()
    #example_build_dir   = '%s/test'    % example_path
    #example_file        = "%s.test" % example_path
    #example_file        = "%s/single_reg_bank.py" % example_path
    #example_file        = "%s/ip_with_multi_reg_bank_and_mem.py" % example_path
    #assert os.system('python %s' % example_file) == 0
    #assert os.system('python %s' % example_file) == 0
    #assert os.system('python %s' % example_file) == 0