

import address_planner
import os


def test_smoke():

    rootdir = os.getcwd()

    example_file    = "%s/example/test.py" % rootdir
    example_res_dir = "%s/example/test_build" % rootdir



    assert os.system('python %s' % example_file) == 0
