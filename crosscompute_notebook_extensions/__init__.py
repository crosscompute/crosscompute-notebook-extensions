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

from .settings import SETTINGS, TOOL_HOST, TOOL_PORT


class ToolPreviewJson(IPythonHandler):

    def get(self):
        stop_servers()
        notebook_path = self.get_argument('notebook_path')
        tool_port = SETTINGS['tool_port']
        process = Popen((
            'crosscompute', 'serve', notebook_path,
            '--host', SETTINGS['tool_host'],
            '--port', str(tool_port),
            '--base_url', SETTINGS['tool_base_url'],
            '--debug', '--without_browser', '--quietly'), stderr=PIPE)
        d = {}
        for x in range(10):
            try:
                requests.get('http://localhost:%s' % tool_port)
            except ConnectionError:
                sleep(1)
            else:
                status_code = 200
                d['tool_url'] = self._get_tool_url()
                break
            if process.poll():
                status_code = 400
                d['text'] = process.stderr.read()
                break
        else:
            status_code = 400
        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)
        self.write(json.dumps(d))

    def _get_tool_url(self):
        tool_base_url = SETTINGS['tool_base_url']
        if tool_base_url == '/':
            request_host = self.request.host.split(':')[0]
            tool_port = SETTINGS['tool_port']
            tool_url = '//%s:%s' % (request_host, tool_port)
        else:
            tool_url = tool_base_url
        return tool_url


def stop_servers():
    for process in process_iter():
        if process.name() != 'crosscompute':
            continue
        x = process.cmdline()
        if len(x) > 3 and x[2] == 'serve':
            process.send_signal(SIGINT)


def load_jupyter_server_extension(notebook_app):
    base_url = notebook_app.base_url
    namespace_url = url_path_join(base_url, '/extensions/crosscompute')
    preview_url = url_path_join(namespace_url, 'preview')
    # Configure settings
    settings = notebook_app.config.get('CrossCompute', {})
    SETTINGS['tool_host'] = settings.get('host', TOOL_HOST)
    SETTINGS['tool_port'] = int(settings.get('port', TOOL_PORT))
    SETTINGS['tool_base_url'] = '/' if base_url == '/' else preview_url
    # Configure routes
    host_pattern = r'.*$'
    if notebook_app.password:
        ToolPreviewJson.get = web.authenticated(ToolPreviewJson.get)
    web_app = notebook_app.web_app
    web_app.add_handlers(host_pattern, [
        (preview_url + '.json', ToolPreviewJson),
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
