from os.path import abspath, dirname, join
from setuptools import find_packages, setup


ENTRY_POINTS = """
[crosscompute.extensions]
ipynb = crosscompute_notebook_extensions.ipynb:IPythonNotebookTool
"""
FOLDER = dirname(abspath(__file__))
DESCRIPTION = '\n\n'.join(open(join(FOLDER, x)).read().strip() for x in [
    'README.rst', 'CHANGES.rst'])
setup(
    name='crosscompute-notebook-extensions',
    version='0.4.2.2',
    description='CrossCompute extensions for Jupyter Notebook',
    long_description=DESCRIPTION,
    classifiers=[
        'Programming Language :: Python',
    ],
    author='CrossCompute Inc',
    author_email='support@crosscompute.com',
    url='https://crosscompute.com/docs',
    keywords='web crosscompute jupyter',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'crosscompute>=0.6.8.2',
        'crosscompute-types>=0.6.8',
        'jinja2',
        'notebook>=4.4.1',
        'psutil',
        'requests',
        'simplejson',
    ],
    tests_require=[
        'pytest',
    ],
    entry_points=ENTRY_POINTS)
