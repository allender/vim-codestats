import datetime
import json
import os.path
import sys
import threading
import time 
import vim

from ssl import CertificateError

# Python 2 and 3 have different modules for urllib2
try:
    from urllib.request import Request, urlopen, build_opener, ProxyHandler
    from urllib.error import URLError
    from http.client import HTTPException
except ImportError:
    from urllib2 import Request, urlopen, URLError, build_opener, ProxyHandler
    from httplib import HTTPException

# because of vim, we need to get the current folder
# into the path to load other modules
codestats_path = vim.eval('s:codestats_path')
if codestats_path not in sys.path:
    sys.path.append(codestats_path)
    
from codestats_filetypes import filetype_map
from localtz import LOCAL_TZ

# globals
INTERVAL = 10                # interval at which stats are sent
SLEEP_INTERVAL = 0.1         # sleep interval so that we can basically timeslice to see if we need to exit
VERSION = '1.0.0'            # versioning
TIMEOUT = 2                  # request timeout value (in seconds)

# Getting proxies with multiprocessing is buggy on MacOS, so disable them
# https://gitlab.com/code-stats/code-stats-vim/issues/8
# https://bugs.python.org/issue30837
if sys.platform == "darwin":
    _urlopen = build_opener(ProxyHandler({})).open
else:
    _urlopen = urlopen

class CodeStats():
    def __init__(self, xp_dict):
        self.xp_dict = xp_dict 
        self.sem = threading.Semaphore()

        # start the main thread
        self.cs_thread = threading.Thread(target = self.main_thread, args = ())
        self.cs_thread.daemon = True
        self.cs_thread.start()

    def add_xp(self, filetype, xp):
        # get the langauge type based on what vim passed to us
        language_type = filetype_map.get(filetype, None)
        if language_type is None or xp == 0:
            return

        # insert the filetype into the dictionary.  Just try
        # and acquire the lock and if we can we can try again 
        # later
        if self.sem.acquire(blocking = False) == True:
            count = self.xp_dict.setdefault(language_type, 0)
            self.xp_dict[language_type] = count + xp
            self.sem.release()

    def send_xp(self, exiting = False):
        if len(self.xp_dict) == 0:
            return

        # acquire the lock to get the list of xp to send
        self.sem.acquire()
        xp_list = [ dict(language=ft, xp=xp) for ft,xp in self.xp_dict.items() ]
        self.xp_dict = { }
        self.sem.release()

        url = vim.eval("g:codestats_api_url")
        if url is None:
            return

        if url.endswith('/') == False:
            url = url + '/'
        url = url + 'api/my/pulses'
        machine_key = vim.eval("g:codestats_api_key")
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'vim_codestats/{0}'.format(VERSION),
            'X-API-Token': machine_key,
            'Accept': '*/*'
        }

        # after lock is released we can send the payload
        utc_now = datetime.datetime.now().replace(microsecond = 0, tzinfo = LOCAL_TZ).isoformat()
        pulse_json = json.dumps({"coded_at":'{0}'.format(utc_now), "xps": xp_list}).encode('utf-8')
        req = Request(url=url, data = pulse_json, headers = headers)
        error = ''
        try:
            response = _urlopen(req, timeout=5)
            response.read()
            # connection might not be closed without .read()
        except URLError as e:
            try:
                # HTTP error
                error = '{0} {1}'.format(e.code, e.read().decode("utf-8"))
            except AttributeError:
                # non-HTTP error, eg. no network
                error = e.reason
        except CertificateError as e:
            # SSL certificate error (eg. a public wifi redirects traffic)
            error = e
        except HTTPException as e:
            error = 'HTTPException on send data. Msg: {0}\nDoc?:{1}'.format(e.message, e.__doc__)
        
        # hacky way to get around exiting and not needing to set the error
        if exiting is False and error is not '':
            vim.command('call codestats#set_error({0})'.format(error))


    # main thread, needs to be able to send XP at an interval
    # and also be able to stop when vim is exited without
    # pausing until the interval is done
    def main_thread(self):
        while True:
            cur_time = 0
            while cur_time < INTERVAL:
                time.sleep(SLEEP_INTERVAL)
                cur_time += SLEEP_INTERVAL 

            self.send_xp()

    def exit(self):
        self.send_xp(exiting = True)

# plugin startup.  Need to allow for vimrc getting reloaded and
# this module getting restarted, potentially with pending xp
if __name__ == "__main__":
    xp_dict = {}
    # allow reentrancy
    if 'codestats' in globals():
        xp_dict = codestats.xp_dict
        del(codestats)

    codestats = CodeStats(xp_dict)