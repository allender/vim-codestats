# importing the requests library 
import requests 
import datetime
import json
import threading
import time 
import vim

filetype_map = {
    "c":                  "C/C++",
    "cs":                 "C#",
    "cmake":              "CMake",
    "cpp":                "C/C++",
    "css":                "CSS",
    "elixir":             "Elixir",
    "erlang":             "Erlang",
    "go":                 "Go",
    "h":                  "C/C++",
    "haskell":            "Haskell",
    "html":               "HTML",
    "hpp":                "C/C++",
    "java":               "Java",
    "javascript":         "JavaScript",
    "json":               "JSON",
    "markdown":           "Markdown",
    "objc":               "Objective-C",
    "objcpp":             "Objective-C++",
    "ocaml":              "OCaml",
    "pascal":             "Pascal",
    "perl":               "Perl",
    "php":                "PHP",
    "plsql":              "PL/SQL",
    "python":             "Python",
    "ruby":               "Ruby",
    "rust":               "Rust",
    "scala":              "Scala",
    "scheme":             "Scheme",
    "sh":                 "Shell Script",
    "tcsh":               "Shell Script (tcsh)",
    "typescript":         "TypeScript",
    "vb":                 "Visual Basic",
    "vbnet":              "Visual Basic .NET",
    "vim":                "VimL",
    "yaml":               "YAML",
    "zsh":                "Shell Script (Zsh)",
}

BETA_URL = 'https://beta.codestats.net'
INTERVAL = 10
SLEEP_INTERVAL = 0.1

# semaphore needed to protect the dictionary

class CodeStats():
    def __init__(self, xp_dict):
        self.xp_dict = xp_dict 
        self.sem = threading.Semaphore()

        # start the main thread
        self.cs_thread = threading.Thread(target = self.main_thread, args = (), daemon = True)
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

    def send_xp(self):
        if len(self.xp_dict) == 0:
            return

        # acquire the lock to get the list of xp to send
        self.sem.acquire()
        xp_list = [ dict(language=ft, xp=xp) for ft,xp in self.xp_dict.items() ]
        self.xp_dict = { }
        self.sem.release()

        url = vim.eval("g:vim_codestats_url")
        if url is None:
            return

        if url.endswith('/') == False:
            url = url + '/'
        url = url + 'api/my/pulses'
        machine_key = vim.eval("g:vim_codestats_key")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "vim_codestats",
            "X-API-Token": machine_key,
            "Accept": "*/*"
        }

        # after lock is released we can send the payload
        utc_now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond = 0).astimezone().isoformat()
        pulse_json = json.dumps({"coded_at":'{0}'.format(utc_now), "xps": xp_list}).encode('utf-8')
        r = requests.post(url = url, data = pulse_json, headers = headers)

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
        self.send_xp()

# plugin startup.  Need to allow for vimrc getting reloaded and
# this module getting restarted, potentially with pending xp
if __name__ == "__main__":
    xp_dict = {}
    # allow reentrancy
    if 'codestats' in globals():
        xp_dict = codestats.xp_dict
        del(codestats)

    codestats = CodeStats(xp_dict)