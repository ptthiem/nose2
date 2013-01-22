from nose2.tests._common import TestCase
from nose2.compat import unittest
from nose2 import events, loader, result, session, tools
from nose2.plugins import sqlite
from nose2.plugins.loader import generators, parameters, testcases
from nose2.events import StartTestRunEvent
import datetime, sqlite3, re

class TestSQLitePlugin(TestCase):
    _RUN_IN_TEMP = True

    def setUp(self):
        super(TestSQLitePlugin, self).setUp()
        self.session = session.Session()
        self.loader = loader.PluggableTestLoader(self.session)
        self.result = result.PluggableTestResult(self.session)
        self.plugin = sqlite.SQLiteReporter(session=self.session)
        self.plugin.register()
        event = StartTestRunEvent(runner=None, suite=None, result=None,
                                  startTime=datetime.datetime.now(), 
				  executeTests=None)
        self.plugin.startTestRun(event)

        class Test(unittest.TestCase):
            def test(self):
                pass
            def test_fail(self):
                assert False
            @unittest.expectedFailure
            def test_unexp_pass(self):
                pass
            @unittest.expectedFailure	
            def test_exp_fail(self):
                assert False
            def test_err(self):
                1/0
            def test_skip(self):
                raise unittest.SkipTest('skip')
            def test_gen(self):
                def check(a, b):
                    self.assertEqual(a, b)
                yield check, 1, 1
                yield check, 1, 2
            @tools.params(1, 2, 3)
            def test_params(self, p):
                self.assertEqual(p, 2)
        self.case = Test

    def dump_db(self, expected_runs=None, expected_tests=None):
        runs = list()
        results = list()
        with sqlite3.connect(self.plugin.path) as db:
            db.row_factory = sqlite3.Row
	    cur = db.cursor()
	    cur.execute("select * from runs")
	    runs = cur.fetchall()
	    cur.execute("select * from results")
	    results = cur.fetchall()

        if expected_runs is not None:
            self.assertEqual(len(runs), expected_runs)
        if expected_tests is not None:
            self.assertEqual(len(results), expected_tests)

        return (runs, results)

    #TODO: unexpected success and expected failure

    def check_single_test(self, run, test, outcome, message):

        self.assertIsNotNone(test['id'])
        self.assertGreaterEqual(test['id'], 0)

        self.assertIsNotNone(test['name'])
        self.assertNotEqual(test['name'], '')

        self.assertIsNotNone(run['id'])
        self.assertIsNotNone(test['runid'])
        self.assertEqual(run['id'], test['runid'])

        self.assertIsNotNone(test['result'])
        self.assertEqual(test['result'], outcome)

        self.assertIsNotNone(test['msg'])
        regex = re.compile(message)
        self.assertRegexpMatches(test['msg'], regex)

        self.assertIsNotNone(run['start'])
        #This is run before testrun finishes
        #self.assertIsNotNone(run['finish'])
        self.assertIsNotNone(test['start'])
        self.assertIsNotNone(test['finish'])
        self.assertLessEqual(run['start'], test['start'])
        self.assertLessEqual(test['start'], test['finish'])
        #self.assertTrue(test['finish'] <= run['finish'])

    def test_success_added_to_db(self):
        test = self.case('test')
        test(self.result)
        runs, results = self.dump_db(1, 1)
        self.check_single_test(runs[0], results[0], 'passed', r'^$')

    def test_unexpected_success_added_to_db(self):
        test = self.case('test_unexp_pass')
        test(self.result)
        runs, results = self.dump_db(1, 1)
        self.check_single_test(runs[0], results[0], 'passed', 
                               r'^Test passed unexpectedly\.$')

    def test_expected_failure_added_to_db(self):
        test = self.case('test_exp_fail')
        test(self.result)
        runs, results = self.dump_db(1, 1)
        self.check_single_test(runs[0], results[0], 'skipped', 
                               r'^Test failure expected\.$')

    def test_failure_includes_traceback(self):
        test = self.case('test_fail')
        test(self.result)
        runs, results = self.dump_db(1, 1)
        self.check_single_test(runs[0], results[0], 'failed', 
                               r'Traceback')

    def test_error_includes_traceback(self):
        test = self.case('test_err')
        test(self.result)
        runs, results = self.dump_db(1, 1)
        self.check_single_test(runs[0], results[0], 'error', 
                               r'Traceback')

    def test_skip_includes_skipped(self):
        test = self.case('test_skip')
        test(self.result)
        runs, results = self.dump_db(1, 1)
        self.check_single_test(runs[0], results[0], 'skipped', r'')

    def test_generator_test_name_correct(self):
        gen = generators.Generators(session=self.session)
        gen.register()
        event = events.LoadFromTestCaseEvent(self.loader, self.case)
        self.session.hooks.loadTestsFromTestCase(event)
        cases = event.extraTests
        for case in cases:
            case(self.result)
        runs, results = self.dump_db(1, 2)
        expected = {
            'nose2.tests.unit.test_sqlite.Test.test_gen:1':
                ('passed', r'^$'),
            'nose2.tests.unit.test_sqlite.Test.test_gen:2':
                ('failed', r'1 != 2'),
        }
        for result in results:
           name = result['name'].split('\n')[0]
           self.assertIn(name, expected)
           outcome, message = expected[name]
           self.check_single_test(runs[0], result, outcome, message)

    def test_params_test_name_correct(self):
        # param test loading is a bit more complex than generator
        # loading. XXX -- can these be reconciled so they both
        # support exclude and also both support loadTestsFromTestCase?
        plug1 = parameters.Parameters(session=self.session)
        plug1.register()
        plug2 = testcases.TestCaseLoader(session=self.session)
        plug2.register()
        # need module to fire top-level event
        class Mod(object):
            pass
        m = Mod()
        m.Test = self.case
        event = events.LoadFromModuleEvent(self.loader, m)
        self.session.hooks.loadTestsFromModule(event)
        for case in event.extraTests:
            case(self.result)
        runs, results = self.dump_db(1, 10)
        expected = {
            'nose2.tests.unit.test_sqlite.Test.test': 
                ('passed', r'^$'),
            'nose2.tests.unit.test_sqlite.Test.test_unexp_pass':
                ('passed', r'^Test passed unexpectedly\.$'),
            'nose2.tests.unit.test_sqlite.Test.test_exp_fail':
                ('skipped', r'^Test failure expected\.$'),
            'nose2.tests.unit.test_sqlite.Test.test_fail':
                ('failed', r'Traceback'),
            'nose2.tests.unit.test_sqlite.Test.test_err':
                ('error', r'Traceback'),
            'nose2.tests.unit.test_sqlite.Test.test_skip':
                ('skipped', r''),
            'nose2.tests.unit.test_sqlite.Test.test_gen':
                ('passed', ''),
            'nose2.tests.unit.test_sqlite.Test.test_params:1':
                ('failed', r'Traceback'),
            'nose2.tests.unit.test_sqlite.Test.test_params:2':
                ('passed', r'^$'),
            'nose2.tests.unit.test_sqlite.Test.test_params:3':
                ('failed', r'Traceback'),
        }
        for result in results:
           name = result['name'].split('\n')[0]
           self.assertIn(name, expected)
           outcome, message = expected[name]
	   self.check_single_test(runs[0], result, outcome, message)


