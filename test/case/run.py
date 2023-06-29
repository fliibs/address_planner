

import unittest


# pytest test --cov-report xml:cov.xml --cov address_planner

suite = unittest.TestLoader().discover('./test','test_*.py')
runner = unittest.TextTestRunner()
runner.run(suite)