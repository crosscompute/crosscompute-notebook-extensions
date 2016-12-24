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


SETTINGS = {}


class ToolPreviewJson(IPythonHandler):

    def get(self):
        stop_servers()
        notebook_path = self.get_argument('notebook_path')
        tool_host, tool_port = SETTINGS['host'], SETTINGS['port']
        process = Popen((
            'crosscompute', 'serve', notebook_path, '--without_browser',
            '--host', tool_host, '--port', str(tool_port)), stderr=PIPE)
        d = {}
        for x in range(5):
            try:
                requests.get('http://localhost:%s' % tool_port)
            except ConnectionError:
                sleep(1)
            else:
                status_code = 200
                d['tool_url'] = '%s://%s:%s' % (
                    self.request.protocol, self.request.host.split(':')[0],
                    tool_port)
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
    settings = notebook_app.config.get('CrossCompute', {})
    SETTINGS['port'] = int(settings.get('port', 4444))
    SETTINGS['host'] = settings.get('host', '127.0.0.1')
    # Configure routes
    base_url = url_path_join(notebook_app.base_url, 'crosscompute')
    host_pattern = r'.*$'
    if notebook_app.password:
        ToolPreviewJson.get = web.authenticated(ToolPreviewJson.get)
    web_app = notebook_app.web_app
    web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, 'preview.json'), ToolPreviewJson),
    ])
    # Set exit hooks
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
