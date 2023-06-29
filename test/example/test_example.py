
import os


example_path = "%s/example" % os.getcwd()

def test_smoke():
    example_file        = "%s/test.py" % example_path
    #example_build_dir   = '%s/test'    % example_path
    assert os.system('python %s' % example_file) == 0


def test_single_reg_bank():
    example_file        = "%s/single_reg_bank.py" % example_path
    assert os.system('python %s' % example_file) == 0


def test_ip_with_multi_reg_bank_and_mem():
    example_file        = "%s/ip_with_multi_reg_bank_and_mem.py" % example_path
    assert os.system('python %s' % example_file) == 0