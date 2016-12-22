"""Server extensions for Jupyter Notebook

Adapted from prototypes by [Salah Ahmed](https://github.com/salah93)
"""
import atexit
import requests
import simplejson as json
from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join
from psutil import process_iter
from requests.exceptions import ConnectionError
from signal import SIGINT
from subprocess import Popen, PIPE
from time import sleep
from tornado import web


class ToolPreview(IPythonHandler):

    def post(self):
        d = {}
        stop_servers()
        notebook_path = self.get_argument('notebook_path')
        arguments = 'crosscompute', 'serve', notebook_path, '--without_browser'
        process = Popen(arguments, stderr=PIPE)

        tool_url = 'http://localhost:4444'
        for x in range(5):
            try:
                requests.get(tool_url)
            except ConnectionError:
                sleep(1)
            else:
                status_code = 200
                d['tool_url'] = tool_url
                break
            if process.poll():
                status_code = 400
                d['text'] = process.stderr.read()
                break
        else:
            status_code = 400
            d['text'] = process.stderr.read()

        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)
        self.write(json.dumps(d))


def stop_servers():
    for process in process_iter():
        if process.name() != 'crosscompute':
            continue
        x = process.cmdline()
        if len(x) > 3 and x[2] == 'serve':
            process.send_signal(SIGINT)


def load_jupyter_server_extension(notebook_app):
    base_url = notebook_app.base_url
    host_pattern = r'.*$'
    if notebook_app.password:
        ToolPreview.post = web.authenticated(ToolPreview.post)
    notebook_app.web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, 'crosscompute', 'preview'), ToolPreview),
    ])
    atexit.register(stop_servers)


def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'assets',
        'dest': 'crosscompute',
        'require': 'crosscompute/tools',
    }]


def _jupyter_server_extension_paths():
    return [{
        'module': 'crosscompute_notebook_extensions',
    }]
