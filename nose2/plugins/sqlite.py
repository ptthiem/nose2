"""
Output test results into a sqlite3 database in realtime.

This plugin implements :func:`startTest`, :func:`testOutcome`, 
:func:`startTestRun` and :func:`stopTestRun` to create, add to, and close 
the database. By default, the report is written to a file called
``nose2.dat`` in the current working directory. You can
configure the output filename by setting ``path`` in a ``[junit-xml]``
section in a config file.

"""
# Based on unittest2/plugins/junitxml.py,
# which is itself based on the junitxml plugin from py.test
import datetime, sqlite3, uuid, six, sys, six
from nose2 import events, result, util


__unittest = True


class SQLiteReporter(events.Plugin):
    """Output junit-xml test report to file"""
    configSection = 'sqlite'
    commandLineSwitch = ('', 'sqlite', 'Generate results in a sqlite db.')

    def __init__(self):
        self.path = self.config.as_str('path', default='nose2.sl3sqlite')
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
                          "finish DATETIME)"))
        self._db.execute(("CREATE TABLE IF NOT EXISTS results ("
                          "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                          "name TEXT, runid TEXT, desc TEXT, result TEXT, "
                          "msg TEXT, start DATETIME NOT NULL, "
                          "finish DATETIME)"))
        self._db.execute(("CREATE TABLE IF NOT EXISTS props ("
                          "id INTEGER, key TEXT, value TEXT, "
                          "PRIMARY KEY (id, key))"))
        self._runstart = event.startTime
        self._db.execute("INSERT INTO runs (id, start) VALUES (?,?)",
                           (self._runid, self._runstart))
        self._db.commit()

    def stopTestRun(self, event):
        "Set the run's finish time and close the connection"
        finish = datetime.datetime.now()
        self._db.execute("UPDATE runs SET finish=? WHERE id=?", 
                   (finish, self._runid))
        self._db.commit()

    def afterSummaryReport(self, event):
        self._db.close()
        self._db = None

    def startTest(self, event):
        """Count test, record start time"""
        start = datetime.datetime.now()
        runid = self._runid
        test = event.test
        name = test.id()
        desc = test.shortDescription()
        cur = self._db.cursor()
        cur.execute(("INSERT INTO results (name, runid, desc, start) "
                      "VALUES (?, ?, ?, ?)"), (name, runid, desc, start))
        self._id = cur.lastrowid
        self._db.commit()


    def testOutcome(self, event):
        """Add test outcome to xml tree"""
        finish = datetime.datetime.now()
        if event.exc_info:
            msg = util.exc_info_to_string(event.exc_info, event.test)
        elif event.reason:
            msg = event.reason
        else:
            msg = ''
      
        test_outcome = event.outcome.lower()

        if event.outcome == result.PASS and not event.expected:
            msg = 'Test passed unexpectedly.'
        elif event.outcome == result.FAIL and event.expected:
            test_outcome = result.SKIP
            msg  = 'Test failure expected.'

        self._db.execute(("UPDATE results SET finish=?, result=?, msg=? "
                          "WHERE id=?"), (finish, test_outcome, msg, self._id))
        self._db.commit()
        try:
            self._save_stream(event, 'stdout')
            self._save_stream(event, 'stderr')
            self._save_string_lines(event, 'logs')
            self._db.commit()
        except Exception as exc: 
            six.print_('Error saving metadata to SQLite', file=sys.stderr)
            six.print_(str(exc), file=sys.stderr)
            self._db.rollback()

    def _save_stream(self, event, key):
        "Save event metadata and assume it will be a stream"
        if key in event.metadata:
            data = event.metadata[key].getvalue()
            if data:
                self._save_prop(key, data)

    def _save_string(self, event, key):
        "Save event metadata and assume it will be a string"
        if key in event.metadata:
            data = event.metadata[key]
            if data:
                if not issubclass(type(data), six.string_types):
                    raise TypeError("%s is not a string: %s" % 
                                    (type(data).__name__, str(data)[:60]))
                self._save_prop(key, data)

    def _save_string_lines(self, event, key):
        "Save event metadata and assume it will be an iterable of strings"
        if key in event.metadata:
            data = event.metadata[key]
            if data:
                self._save_prop(key, '\n'.join(data))

    def _save_prop(self, name, data):
        "Commit a value to the properties  table"
        try:
            self._db.execute(("INSERT INTO props (id, key, value) "
                              "VALUES (?, ?, ?)"), (self._id, name, data)) 
        except Exception as exc:
            raise RuntimeError( "Error: adding (%s,%s) - %s" %
                                (self._id, name, str(exc)) )




