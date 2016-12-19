import nbformat
from crosscompute.exceptions import CrossComputeError
from invisibleroads_macros.table import normalize_key
from os.path import basename, splitext


def get_tool_name(path):
    file_name = basename(path)
    base_name = splitext(file_name)[0]
    return normalize_key(
        base_name, word_separator='-', separate_camel_case=True,
        separate_letter_digit=True)


def load_notebook(path):
    for version in sorted(nbformat.versions, reverse=True):
        try:
            notebook = nbformat.read(path, as_version=version)
            break
        except Exception:
            pass
    else:
        raise CrossComputeError('Could not load notebook (path=%s)' % path)
    return notebook
