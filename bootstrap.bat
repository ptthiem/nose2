#!/bin/bash
#
# NOTE: requires virtualenvwrapper
#
mkvirtualenv nose2
python "%PYTHONHOME%\scripts\pip-script.py" install -r requirements.txt
python setup.py develop
