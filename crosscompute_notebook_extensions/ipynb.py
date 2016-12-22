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
from nbconvert.exporters import PythonExporter
from os.path import abspath, dirname, join
from six import string_types

from .macros import get_tool_name, load_notebook


class IPythonNotebookTool(ToolExtension):

    @classmethod
    def prepare_tool_definition(self, path):
        tool_name = get_tool_name(path)
        script_folder = make_enumerated_folder(join(
            HOME_FOLDER, '.crosscompute', tool_name, 'tools'))
        prepare_script_folder(script_folder, path, tool_name)
        return find_tool_definition(script_folder, default_tool_name=tool_name)


def prepare_script_folder(script_folder, notebook_path, tool_name):
    notebook = load_notebook(notebook_path)
    notebook_folder = dirname(abspath(notebook_path))
    tool_arguments = load_tool_arguments(notebook)
    tool_arguments = make_absolute_paths(tool_arguments, notebook_folder)
    tool_arguments = corral_arguments(script_folder, tool_arguments)
    # Save script
    script_content = prepare_script(tool_arguments, notebook)
    script_name = 'run.py'
    copy_text(join(script_folder, script_name), script_content)
    # Save configuration
    command_name = notebook['metadata']['kernelspec']['name']
    configuration_content = prepare_configuration(
        tool_name, command_name, script_name, tool_arguments)
    configuration_name = 'cc.ini'
    copy_text(join(script_folder, configuration_name), configuration_content)


def load_tool_arguments(notebook):
    g, l = OrderedDict(), OrderedDict()
    try:
        cell = notebook['cells'][0]
    except IndexError:
        raise CrossComputeError('Cannot convert empty notebook')
    exec(cell['source'], g, l)
    return l


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
    notebook = deepcopy(notebook)
    notebook.cells[0]['source'] = '\n'.join(script_lines)
    script_content = nbconvert.export(PythonExporter, notebook)[0]
    return script_content


def prepare_configuration(
        tool_name, command_name, script_name, tool_arguments):
    configuration_lines = []
    configuration_lines.append('[crosscompute %s]' % tool_name)
    configuration_lines.append('command_template = %s %s %s' % (
        command_name, script_name, ' '.join(
            '{%s}' % x for x in tool_arguments)))
    for k, v in tool_arguments.items():
        if k in RESERVED_ARGUMENT_NAMES:
            continue
        configuration_lines.append('%s = %s' % (k, v))
    configuration_content = '\n'.join(configuration_lines)
    return configuration_content
