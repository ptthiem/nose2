"""
Output test reports in junit-xml format.

This plugin implements :func:`startTest`, :func:`testOutcome` and
:func:`stopTestRun` to compile and then output a test report in
junit-xml format. By default, the report is written to a file called
``nose2-junit.xml`` in the current working directory. You can
configure the output filename by setting ``path`` in a ``[junit-xml]``
section in a config file.

"""
# Based on unittest2/plugins/junitxml.py,
# which is itself based on the junitxml plugin from py.test
import datetime
from xml.etree import ElementTree as ET

from nose2 import events, result, util, uuid, sqlite3


__unittest = True


class SQLiteReporter(events.Plugin):
    """Output junit-xml test report to file"""
    configSection = 'sqlite'
    commandLineSwitch = ('sqlite', 'Generate results in a sqlite db.')

    def __init__(self):
        self.path = self.config.as_str('path', default='nose2.dat')
	self._runid = str(uuid.uuid4())
	self._runstart = None
	self._id = None
        self._db = None

    def startTestRun(self, event):
        """Create/Open DB"""
        self._db = sqlite3.connect(self.path)
	self._db.execute(("CREATE TABLE IF NOT EXISTS runs ("
                           "id TEXT PRIMARY KEY, "
                           "start DATETIME NOT NULL, "
                           "finish DATETIME)")
	self._db.execute(("CREATE TABLE IF NOT EXISTS results ("
                           "id INTEGER PRIMARY KEY AUTOINCREMENET, "
			   "name TEXT, runid TEXT, desc TEXT, result TEXT, " 
			   "msg TEXT, start DATETIME NOT NULL, "
                           "finish DATETIME)")
	self._db.execute(("CREATE TABLE IF NOT EXISTS props ("
                           "id TEXT, key TEXT, value TEXT,
			   PRIMARY KEY (id, key))")
	self._runstart = event.startTime
	self._db.execute("INSERT INTO runs (id, start) VALUES (?,?)",
		         (self.runid, self._runstart))
	self._db.commit()

    def startTest(self, event):
        """Count test, record start time"""
        start = datetime.datetime.now()
	runid = self._runid
        name = test.id()
	desc = test.shortDescription()
	cur = self._db.cursor()
	curr.execute(("INSERT INTO results (name, runid, desc, start) "
                           "VALUES (?, ?, ?, ?)"), (name, runid, desc, start))
	self._id = cur.lastrowid
	self._db.commit()


    def testOutcome(self, event):
        """Add test outcome to xml tree"""
        finish = datetime.datetime.now()
	result = 'passed'
        msg = ''
        if event.exc_info:
            msg = util.exc_info_to_string(event.exc_info, test)
        elif event.reason:
            msg = event.reason

        if event.outcome == result.ERROR:
            result = 'error'
        elif event.outcome == result.FAIL and not event.expected:
            result = 'failure'
        elif event.outcome == result.PASS and not event.expected:
            result = 'skipped'
	    msg = 'Test passed unexpectedly.'
        elif event.outcome == result.SKIP:
	    result = 'skipped'
        elif event.outcome == result.FAIL and event.expected:
	    result = 'skipped'
	    msg  = 'Text failure expected'

	self._db.execute(("UPDATE tests SET finish=?, result=?, msg=? "
                           "WHERE id=?"), (finish, result, msg, self._id))
	self._db.commit()

    def stopTestRun(self, event):
        """Output xml tree to file"""
	finish = datetime.datetime.now()
	self._db.execute(("UPDATE runs SET finish=?, WHERE id=?"),
			 (finish, self._runid))
	self._db.commit()

