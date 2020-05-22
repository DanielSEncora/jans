import os
import pathlib

APP_ROOT = pathlib.Path(__file__).parent.as_posix()
INSTALL_DIR = pathlib.Path(__file__).parent.parent.as_posix()
DATA_DIR = os.path.join(APP_ROOT, 'data')
LOG_DIR = os.path.join(INSTALL_DIR, 'logs')

LOG_FILE = os.path.join(LOG_DIR, 'setup.log')
LOG_ERROR_FILE = os.path.join(LOG_DIR, 'setup_error.log')
LOG_OS_CHANGES_FILE = os.path.join(LOG_DIR, 'os-changes.log')

cmd_ln = '/bin/ln'
cmd_chmod = '/bin/chmod'
cmd_chown = '/bin/chown'
cmd_chgrp = '/bin/chgrp'
cmd_mkdir = '/bin/mkdir'
cmd_rpm = '/bin/rpm'
cmd_dpkg = '/usr/bin/dpkg'
opensslCommand = '/usr/bin/openssl'
cmd_wget = os.popen('which wget').read().strip()
cmd_sed = os.popen('which sed').read().strip()
