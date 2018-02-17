"""Server extensions for Jupyter Notebook

Adapted from prototypes by [Salah Ahmed](https://github.com/salah93)
"""
import atexit
import requests
from configparser import ConfigParser
from crosscompute.exceptions import CrossComputeError
from invisibleroads_macros.disk import compress, make_folder
from invisibleroads_macros.text import unicode_safely
from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join
from os.path import abspath, expanduser, join
from psutil import process_iter
from requests.exceptions import ConnectionError
from signal import SIGINT
from subprocess import Popen, check_call, PIPE
from tempfile import gettempdir
from time import sleep
from tornado import web

from .ipynb import IPythonNotebookTool
from .settings import S


class NotebookBackupJson(IPythonHandler):

    def post(self):
        notebook_push_path = expect_variable('notebook_push_path', '')
        if not notebook_push_path:
            self.set_status(501)
            return self.write({})
        if check_call([notebook_push_path]):
            self.set_status(503)
            return self.write({})
        notebook_url = expect_variable('notebook_url', '')
        self.write({'notebook_url': notebook_url})


class ConfigurationUpdateJson(IPythonHandler):

    def post(self):
        variable_name = self.get_argument('variable_name')
        if variable_name not in ['server_token']:
            self.set_status(400)
            return self.write({variable_name: 'unexpected'})
        variable_value = self.get_argument('variable_value')
        configuration = ConfigParser()
        configuration_path = get_configuration_path()
        configuration.read(configuration_path)
        if 'crosscompute-website' not in configuration:
            configuration.add_section('crosscompute-website')
        configuration_section = configuration['crosscompute-website']
        configuration_section[variable_name] = variable_value
        configuration.write(open(configuration_path, 'wt'))
        S[variable_name] = variable_value
        self.write({})


class ToolPreviewJson(IPythonHandler):

    def post(self):
        stop_servers()
        notebook_path = self.get_argument('notebook_path')
        tool_port = S['tool_port']
        process_arguments = [
            'crosscompute', 'serve', abspath(notebook_path),
            '--host', S['tool_host'],
            '--port', str(tool_port),
            '--base_url', S['tool_base_url'],
            '--without_browser', '--without_logging', '--with_debugging']
        for x in 'brand_url', 'website_name', 'website_owner':
            y = expect_variable(x, '')
            if y:
                process_arguments.extend(('--' + x, y))
        open(join(
            DEBUGGING_FOLDER, 'preview-tool.sh',
        ), 'wt').write(' '.join((
            '"%s"' % x if ' ' in x else x) for x in process_arguments))
        process = Popen(process_arguments, stderr=PIPE)
        d = {}
        for x in range(10):
            try:
                requests.get('http://127.0.0.1:%s' % tool_port)
            except ConnectionError:
                sleep(1)
            else:
                status_code = 200
                d['tool_url'] = self._get_tool_url()
                break
            if process.poll():
                status_code = 400
                d['text'] = unicode_safely(process.stderr.read().strip())
                break
        else:
            status_code = 400
        self.set_status(status_code)
        self.write(d)

    def _get_tool_url(self):
        tool_base_url = S['tool_base_url']
        if tool_base_url == '/':
            request_host = self.request.host.split(':')[0]
            tool_port = S['tool_port']
            tool_url = '//%s:%s' % (request_host, tool_port)
        else:
            tool_url = tool_base_url
        return tool_url


class ToolDeployJson(IPythonHandler):

    def post(self):
        try:
            server_token = expect_variable('server_token')
        except KeyError as e:
            self.set_status(401)
            return self.write({})
        server_url = expect_variable('server_url', 'https://crosscompute.com')
        notebook_id = expect_variable('notebook_id', '')
        notebook_path = self.get_argument('notebook_path')
        try:
            tool_definition = IPythonNotebookTool.prepare_tool_definition(
                notebook_path, with_debugging=False)
        except CrossComputeError as e:
            self.set_status(400)
            return self.write({'text': str(e)})
        archive_path = compress(tool_definition['configuration_folder'])

        response = requests.post(server_url + '/tools.json', headers={
            'Authorization': 'Bearer ' + server_token,
        }, data={
            'notebook_id': notebook_id,
            'notebook_path': notebook_path,
            'environment_level': expect_variable('environment_level', 0),
            'processor_level': expect_variable('processor_level', 0),
            'memory_level': expect_variable('memory_level', 0),
        } if notebook_id else {}, files={
            'tool_folder': open(archive_path, 'rb'),
        })
        status_code = response.status_code
        if status_code != 200:
            self.set_status(status_code)
            return self.write({})
        try:
            d = response.json()
            tool_url = d['tool_url']
        except Exception:
            self.set_status(503)
            return self.write({})
        self.write({'tool_url': server_url + tool_url})


def get_configuration_path():
    return expanduser('~/.crosscompute/.settings.ini')


def load_jupyter_server_extension(notebook_app):
    base_url = notebook_app.base_url
    backup_url = get_extension_url(base_url, 'backup')
    configure_url = get_extension_url(base_url, 'configure')
    preview_url = get_extension_url(base_url, 'preview')
    deploy_url = get_extension_url(base_url, 'deploy')
    # Configure settings
    settings = notebook_app.config.get('CrossCompute', {})
    S['tool_host'] = settings.get('host', '127.0.0.1')
    S['tool_port'] = int(settings.get('port', 4444))
    S['tool_base_url'] = '/' if base_url == '/' else preview_url
    # Configure routes
    host_pattern = r'.*$'
    if notebook_app.password:
        for x in [
            NotebookBackupJson,
            ConfigurationUpdateJson,
            ToolPreviewJson,
            ToolDeployJson,
        ]:
            x.post = web.authenticated(x.post)
    web_app = notebook_app.web_app
    web_app.add_handlers(host_pattern, [
        (backup_url + '.json', NotebookBackupJson),
        (configure_url + '.json', ConfigurationUpdateJson),
        (preview_url + '.json', ToolPreviewJson),
        (deploy_url + '.json', ToolDeployJson),
    ])
    # Set exit hooks
    atexit.register(stop_servers)


def get_extension_url(base_url, verb):
    namespace_url = get_namespace_url(base_url)
    return url_path_join(namespace_url, verb)


def get_namespace_url(base_url):
    return url_path_join(base_url, '/extensions/crosscompute')


def stop_servers():
    for process in process_iter():
        if process.name() != 'crosscompute':
            continue
        x = process.cmdline()
        if len(x) > 3 and x[2] == 'serve':
            process.send_signal(SIGINT)


def expect_variable(variable_name, default_value=None):
    try:
        return S[variable_name]
    except KeyError:
        pass
    configuration = ConfigParser()
    configuration_path = get_configuration_path()
    configuration.read(configuration_path)
    try:
        value = configuration['crosscompute-website'][variable_name]
    except KeyError:
        pass
    else:
        S[variable_name] = value
        return value
    if default_value is None:
        raise KeyError
    return default_value


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


DEBUGGING_FOLDER = make_folder(join(
    gettempdir(), 'crosscompute-notebook-extensions'))
