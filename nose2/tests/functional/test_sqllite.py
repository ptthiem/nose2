import sys

from nose2 import session
from nose2.compat import unittest
from nose2.plugins.sqlite import SQLiteReporter
from nose2.plugins import buffer
from nose2.plugins.loader import discovery, testcases
from nose2.tests._common import FunctionalTestCase, support_file, Conn



class TestSqlLitePlugin(FunctionalTestCase):

    def setUp(self):
        super(TestMpPlugin, self).setUp()
        self.session = session.Session()
        self.plugin = MultiProcess(session=self.session)

    def test_not_sure_yet(self):
        #sys.path.append(support_file('scenario/slow'))
        #import test_slow as mod

        suite = unittest.TestSuite()
	#Need ok
	#Need error
	#Need failure
	#Need Unexpected Success
	#Need Expected failure
	#Need Skip
        #suite.addTest(mod.TestSlow('test_ok'))
        #suite.addTest(mod.TestSlow('test_fail'))
        #suite.addTest(mod.TestSlow('test_err'))

        #flat = list(self.plugin._flatten(suite))
        #self.assertEqual(len(flat), 3)



class SqlLiteTestRuns(FunctionalTestCase):

    def test_tests_in_package(self):
        #TODO
        proc = self.runIn(
            'scenario/tests_in_package',
            '-v',
            '--plugin=nose2.plugins.sqlite')
        self.assertTestRunOutputMatches(proc, stderr='Ran 25 tests')
        self.assertEqual(proc.poll(), 1)

    def test_package_in_lib(self):
        #TODO
        proc = self.runIn(
            'scenario/package_in_lib',
            '-v',
            '--plugin=nose2.plugins.sqlite')
        self.assertTestRunOutputMatches(proc, stderr='Ran 3 tests')
        self.assertEqual(proc.poll(), 1)

    def test_module_fixtures(self):
        #TODO
        proc = self.runIn(
            'scenario/module_fixtures',
            '-v',
            '--plugin=nose2.plugins.sqlite')
        self.assertTestRunOutputMatches(proc, stderr='Ran 5 tests')
        self.assertEqual(proc.poll(), 0)

    def test_class_fixtures(self):
        #TODO
        proc = self.runIn(
            'scenario/class_fixtures',
            '-v',
            '--plugin=nose2.plugins.sqlite')
        self.assertTestRunOutputMatches(proc, stderr='Ran 4 tests')
        self.assertEqual(proc.poll(), 0)
