"""Server extensions for Jupyter Notebook

Adapted from prototypes by [Salah Ahmed](https://github.com/salah93)
"""
import atexit
from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join
from os import kill
from psutil import process_iter
from signal import SIGINT
from subprocess import Popen, PIPE
from tornado import web


class ToolPreview(IPythonHandler):

    def post(self):
        stop_servers()
        notebook_path = self.get_argument('notebook_path')
        arguments = 'crosscompute', 'serve', notebook_path
        Popen(arguments)


def stop_servers():
    # arguments = 'pgrep', '-f', 'crosscompute serve'
    # pgrep_process = Popen(arguments, stdout=PIPE)
    # process_ids = [int(x) for x in pgrep_process.stdout.read().split()]
    # for process_id in process_ids:
        # kill(process_id, SIGINT)
    # return len(process_ids)
    for p in process_iter():
        if p.name() == 'crosscompute':
            cmdline = p.cmdline()
            if len(cmdline) > 3 and cmdline[2] == 'serve':
                p.send_signal(SIGINT)


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
