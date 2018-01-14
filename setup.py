from os.path import abspath, dirname, join
from setuptools import find_packages, setup


ENTRY_POINTS = """
[crosscompute.extensions]
ipynb = crosscompute_notebook_extensions.ipynb:IPythonNotebookTool"""
FOLDER = dirname(abspath(__file__))
DESCRIPTION = '\n\n'.join(open(join(FOLDER, x)).read().strip() for x in [
    'README.rst', 'CHANGES.rst'])
setup(
    name='crosscompute-notebook-extensions',
    version='0.5.2',
    description='CrossCompute extensions for Jupyter Notebook',
    long_description=DESCRIPTION,
    classifiers=[
        'Framework :: Jupyter',
        'Framework :: Pyramid',
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
        'invisibleroads-macros>=0.9.3',
        'crosscompute>=0.7.5',
        'crosscompute-types>=0.7.5',
        'configparser',
        'jinja2',
        'mock',
        'nbconvert',
        'nbformat',
        'notebook>=5.0.0',
        'psutil',
        'requests',
        'six',
        'tornado',
    ],
    tests_require=[
        'pytest',
    ],
    entry_points=ENTRY_POINTS)
