from crosscompute_notebook_extensions.macros import get_tool_name


def test_get_tool_name():
    f = get_tool_name
    assert f('/tmp/Untitled.ipynb') == 'untitled'
    assert f('AddIntegers') == 'add-integers'
    assert f('CountWords2016') == 'count-words-2016'
