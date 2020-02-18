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
sem = threading.Semaphore()
xp_dict = { }
timer = None

def get_xp_list(xp_dict):
    xp_list = []
    for (ft, xp) in xp_dict.items():
        xp_list.append(dict(language=ft, xp=xp))
    return xp_list

def add_xp(filetype, xp):
    # get the langauge type based on what vim passed to us
    language_type = filetype_map.get(filetype, None)
    if language_type is None or xp == 0:
        return

    # insert the filetype into the dictionary.  Just try
    # and acquire the lock and if we can we can try again 
    # later
    if sem.acquire(blocking = False) == True:
        count = xp_dict.setdefault(language_type, 0)
        xp_dict[language_type] = count + xp
        sem.release()

def send_xp():
    global xp_dict
    if len(xp_dict) == 0:
        return

    # acquire the lock to get the list of xp to send
    sem.acquire()
    xp_list = get_xp_list(xp_dict)
    xp_dict = { }
    sem.release()

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
    print(url, headers, pulse_json)
    requests.post(url = url, data = pulse_json, headers = headers)

def running_thread():
    # loop and push out stats at regular interval
    send_xp()
    global timer
    timer = threading.Timer(INTERVAL, running_thread)
    timer.start()

def start_cs_thread():
    running_thread()

def exit_cs_thread():
    if timer is not None:
        timer.cancel()
        send_xp()
