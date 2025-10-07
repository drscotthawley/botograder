from setuptools import setup, find_packages

setup(
    name="botograder",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'canvasapi',
        'jupytext',
        'python-dateutil',
    ],
)

