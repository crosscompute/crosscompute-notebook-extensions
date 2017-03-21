import nbconvert
from collections import OrderedDict
from copy import deepcopy
from crosscompute.configurations import find_tool_definition
from crosscompute.exceptions import CrossComputeError
from crosscompute.extensions import ToolExtension
from crosscompute.scripts import corral_arguments
from crosscompute.types import RESERVED_ARGUMENT_NAMES
from invisibleroads_macros.configuration import make_absolute_paths
from invisibleroads_macros.disk import (
    copy_text, make_enumerated_folder, HOME_FOLDER)
from invisibleroads_macros.text import unicode_safely
from jinja2 import Environment, PackageLoader
from nbconvert.exporters import PythonExporter
from os.path import abspath, dirname, join
from six import string_types

from .macros import get_tool_name, load_notebook


JINJA2_ENVIRONMENT = Environment(loader=PackageLoader(
    'crosscompute_notebook_extensions'))


class IPythonNotebookTool(ToolExtension):

    @classmethod
    def prepare_tool_definition(self, path, debug=False):
        tool_name = get_tool_name(path)
        script_folder = make_enumerated_folder(join(
            HOME_FOLDER, '.crosscompute', tool_name, 'tools'))
        prepare_script_folder(script_folder, path, tool_name, debug)
        return find_tool_definition(script_folder, default_tool_name=tool_name)


def prepare_script_folder(
        script_folder, notebook_path, tool_name, debug=False):
    notebook = load_notebook(notebook_path)
    notebook_folder = dirname(abspath(notebook_path))
    tool_arguments = load_tool_arguments(notebook)
    tool_arguments = make_absolute_paths(tool_arguments, notebook_folder)
    tool_arguments = corral_arguments(script_folder, tool_arguments)
    kw = {'debug': debug}
    # Save script
    script_content = prepare_script(tool_arguments, notebook)
    script_name = 'run.py'
    copy_text(join(script_folder, script_name), script_content)
    # Save tool template
    cell = notebook['cells'][0]
    if cell['cell_type'] == u'markdown':
        template_name = 'tool.md'
        copy_text(join(script_folder, template_name), cell['source'])
        kw['tool_template_path'] = template_name
    # Save result template
    cell = notebook['cells'][-1]
    if cell['cell_type'] == u'markdown':
        template_name = 'result.md'
        copy_text(join(script_folder, template_name), cell['source'])
        kw['result_template_path'] = template_name
    # Save configuration
    command_name = notebook['metadata']['kernelspec']['name']
    configuration_content = prepare_configuration(
        tool_name, command_name, script_name, tool_arguments, **kw)
    configuration_name = 'cc.ini'
    copy_text(join(script_folder, configuration_name), configuration_content)


def load_tool_arguments(notebook):
    g, l = OrderedDict(), OrderedDict()
    code_cells = get_code_cells(notebook)
    if not code_cells:
        raise CrossComputeError('cannot make a tool without code')
    try:
        exec(code_cells[0]['source'], g, l)
    except Exception as e:
        raise CrossComputeError(e)
    d = OrderedDict()
    for k, v in l.items():
        d[unicode_safely(k)] = unicode_safely(v)
    return d


def prepare_script(tool_arguments, notebook):
    script_lines = []
    script_lines.append('from sys import argv')
    for index, k in enumerate(tool_arguments):
        v = tool_arguments[k]
        if isinstance(v, string_types):
            line_template = '{argument_name} = argv[{i}]'
        else:
            line_template = '{argument_name} = {value_type}(argv[{i}])'
        script_lines.append(line_template.format(
            argument_name=k, i=index + 1, value_type=type(v).__name__))
    script_lines.extend(['\n'] + JINJA2_ENVIRONMENT.get_template(
        'python.jinja2').render().splitlines())
    notebook = deepcopy(notebook)
    code_cells = get_code_cells(notebook)
    code_cells[0]['source'] = '\n'.join(script_lines)
    script_content = nbconvert.export(PythonExporter, notebook)[0]
    return script_content


def get_code_cells(notebook):
    code_cells = []
    for cell in notebook['cells']:
        if cell['cell_type'] == u'code':
            code_cells.append(cell)
    return code_cells


def prepare_configuration(
        tool_name, command_name, script_name, tool_arguments,
        tool_template_path=None, result_template_path=None, debug=False):
    configuration_lines = []
    configuration_lines.append('[crosscompute %s]' % tool_name)
    configuration_lines.append('command_template = %s %s %s' % (
        command_name, script_name, ' '.join(
            '{%s}' % x for x in tool_arguments)))
    for k, v in tool_arguments.items():
        if k in RESERVED_ARGUMENT_NAMES:
            continue
        configuration_lines.append('%s = %s' % (k, v))
    if tool_template_path:
        configuration_lines.append(
            'tool_template_path = %s' % tool_template_path)
    if result_template_path:
        configuration_lines.append(
            'result_template_path = %s' % result_template_path)
    if debug:
        configuration_lines.extend([
            'show_standard_error = True',
            'show_standard_output = True',
        ])
    configuration_content = '\n'.join(configuration_lines)
    return configuration_content
