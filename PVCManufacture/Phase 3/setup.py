from setuptools import setup, find_packages

setup(
    name="pvc_simulation",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'simpy',
    ],
)
