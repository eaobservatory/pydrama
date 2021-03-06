'''
drama/log.py    RMB 20140926

Classes and setup routines for DRAMA logging.


Copyright (C) 2020 East Asian Observatory

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import time as _time
import logging as _logging
import os as _os
import drama as _drama
import traceback
import sys


class StrftimeHandler(_logging.FileHandler):
    '''
    You supply a strftime format string as the filename,
    along with whether to use local time or utc.
    Rolls over to a new dir/file when the resulting path changes.
    This lets you rollover every day, minute, year, whatever.
    
    For example, for standard DRAMA logs, use:
        StrftimeHandler('/jac_logs/%Y%m%d/MYTASK.log', utc=True, chmod=02777)
    
    NOTE: I'm not inheriting BaseRotatingHandler because I don't
    like the design of breaking up shouldRollover()/doRollover().
    '''
    def __init__(self, filefmt, utc=False, chmod=None):
        '''
        filefmt: strftime-compatible file path format string.
        utc: if True, use gmtime instead of localtime (default False).
        chmod: permission mask for new directories (default None).
            02777 results in drwxrwsrwx (a+rwx with setgid bit).
            Leave as None (the default) to skip the chmod step.
            chmod is best-effort; errors are not detected.
        
        You may change any of these parameters on the fly after
        the instance is created, though chmod will not take effect
        until a new directory is created.
        '''
        self.filefmt = filefmt
        self.utc = utc
        self.chmod = chmod
        self.filestr = '.'  # fixed on first emit()
        _logging.FileHandler.__init__(self, self.filestr, mode='a', delay=1)
    
    def emit(self, record):
        '''
        Emit a record, opening a new file if strftime path changes.
        '''
        try:
            t = record.created
            if self.utc:
                filestr = _time.strftime(self.filefmt, _time.gmtime(t))
            else:
                filestr = _time.strftime(self.filefmt, _time.localtime(t))
            
            if filestr != self.filestr:
                self.filestr = filestr
                self.baseFilename = _os.path.abspath(self.filestr)
                if self.stream:
                    self.stream.close()
                    self.stream = None
                # create the path if needed; this is a little bit tricky
                path = _os.path.dirname(self.baseFilename) or '.'
                try:
                    _os.makedirs(path)
                    if self.chmod is not None:
                        _os.chmod(path, self.chmod)
                except OSError:
                    if not _os.path.isdir(path):
                        raise
            _logging.FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class MsgOutHandler(_logging.Handler):
    '''
    Emits formatted log records via drama.msgout or drama.ersout,
    depending on the severity of the logging level.
    '''
    def emit(self, record):
        '''emit(self, record)
        If level < WARN send formatted record via MsgOut, else via ErsOut.
        '''
        try:
            # force use of self.formatter.formatException instead of cached value.
            # seems ugly and intrusive to me...
            record.exc_text = None
            msg = self.format(record)
            record.exc_text = None
            if record.levelno < _logging.WARNING:
                _drama.msgout(msg)
            else:
                t,v,tb = sys.exc_info()
                s = 0
                if t == _drama.BadStatus:
                    s = v.status
                _drama.ersout(msg, s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class MsgOutFormatter(_logging.Formatter):
    '''
    Skip lengthy exception tracebacks for msgout/ersout;
    you should save these to a file instead.
    '''
    def formatException(self, exc_info):
        if exc_info[0] == _drama.BadStatus:
            return exc_info[1].message
        else:
            return ''.join(traceback.format_exception(exc_info[0], exc_info[1], None)).strip()
    
    def formatStack(self, stack_info):
        return ''


def setup(taskname=None):
    '''
    Simple setup for DRAMA tasks:
        - root level set to INFO
        - console output to stderr
        - <=INFO to MsgOut, >=WARN to ErsOut
        - if taskname, file output to /jac_logs/YYYYMMDD/<taskname>.log
    
    Returns the handlers added to logging.root if you need to customize:
        (stream_handler, msgout_handler, strftime_handler)
    '''
    
    f = _logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    strftime_h = None
    if taskname:
        strftime_h = StrftimeHandler('/jac_logs/%%Y%%m%%d/%s.log' % (taskname),
                                     utc=True, chmod=0o2777)
        strftime_h.setFormatter(f)
        _logging.root.addHandler(strftime_h)

    stream_h = _logging.StreamHandler()
    stream_h.setFormatter(f)
    _logging.root.addHandler(stream_h)
    
    #f = _logging.Formatter('%(levelname)s:%(message)s')
    f = MsgOutFormatter('%(levelname)s:%(message)s')
    msgout_h = MsgOutHandler()
    msgout_h.setFormatter(f)
    msgout_h.setLevel(_logging.INFO)
    _logging.root.addHandler(msgout_h)

    _logging.root.setLevel(_logging.INFO)
    
    return stream_h, msgout_h, strftime_h


