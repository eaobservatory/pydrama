#!/local/python3/bin/python3
'''
test/get.py     RMB 20190708


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

import sys
import os
import jac_sw
import drama
import time

taskname = 'PYGET_' + str(os.getpid())

import drama.log
drama.log.setup()
import logging
log = logging.getLogger(taskname)
#logging.getLogger('drama').setLevel(logging.DEBUG)

GET_STOP = True
GET_A_STOP = True

def GET(msg):
    '''WARNING 20190708
    Due to how DRAMA copies messages inside a wait() loop,
    the argument SDS will have its "external" flag cleared.
    Without this flag, SdsPointer will allocate memory for
    undefined fields instead of setting SDS__UNDEFINED status.
    
    So instead of 'None', synchronous gets will fill in undefined values
    with whatever garbage is currently in memory.  TODO: fix DRAMA.
    '''
    task = sys.argv[1]
    parm = sys.argv[2]
    log.info('GET %s %s', task, parm)
    try:
        reply = drama.get(task, parm).wait().arg
        log.info('GET reply: %s', reply)
    except:
        # due to stop() in "finally:" we must log our errors here
        log.exception('GET exception')
    finally:
        if GET_STOP:
            drama.stop()


def GET_A(msg):  # async version
    try:
        if msg.reason == drama.REA_OBEY:
            if len(sys.argv) > 2:
                task = sys.argv[1]
                parm = sys.argv[2]
            else:
                task = taskname  # self
                parm = 'TIME'
            log.info('GET_A %s %s', task, parm)
            drama.get(task, parm)
            drama.reschedule(5)
            return
        elif msg.reason == drama.REA_COMPLETE:
            reply = msg.arg
            log.info('GET_A reply: %s', reply)
        else:
            log.error('GET_A unexpected msg: %s', msg)
    except:
        log.exception('GET_A exception')
    if GET_A_STOP:
        # test: catch Exit, see if task still dies.
        try:
            drama.stop()
        except:
            pass


def GET_NESTED(msg):  # call the async version from a wait() loop
    '''
    Will GET_A still see Undefined values as None
    if it is called from inside a synchronous wait() loop?
    Result: YES, Undefined values are set to None.
            So it's just a direct wait().arg that has trouble.
    '''
    try:
        if msg.reason == drama.REA_OBEY:
            log.info('GET_NESTED wait() for GET_A...')
            global GET_STOP, GET_A_STOP
            GET_STOP = GET_A_STOP = False
            drama.obey(taskname, 'GET_A').wait()
            log.info('GET_NESTED done.')
        else:
            log.error('GET_NESTED unexpected msg: %s', msg)
    except:
        log.exception('GET_NESTED exception')
    drama.stop()


def PUB(msg):
    drama.set_param('TIME', time.time())
    drama.reschedule(1)


try:
    log.info('drama.init(%s)', taskname)
    drama.init(taskname, actions=[GET, GET_A, GET_NESTED, PUB])
    drama.blind_obey(taskname, 'PUB')
    drama.blind_obey(taskname, 'GET_A')#_NESTED')
    drama.run()
finally:
    log.info('drama.stop()')
    drama.stop()


'''
TODO: check blind_obey().  if the taskname is us, we can check the action
      list and at least raise an error if action is not in the list --
      as opposed to now, where nothing happens with no error.
      However, needs the full action list (including e.g. EXIT),
      not just the actions registered via python.
'''
