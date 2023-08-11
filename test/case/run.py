

import unittest


# pytest test --cov-report xml:cov.xml --cov address_planner

suite = unittest.TestLoader().discover('./test','test_*.py')
suite_python = unittest.TestLoader().discover('./example/python','demo_*.py')
suite_table = unittest.TestLoader().discover('./example/tablelike','demo_*.py')
runner = unittest.TextTestRunner()
runner.run(suite)
runner.run(suite_python)
runner.run(suite_table)