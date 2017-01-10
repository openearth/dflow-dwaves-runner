from setuptools import setup, find_packages

setup(
    name='dfwr',
    version='0.0',
    author='Bas Hoonhout',
    author_email='bas.hoonhout@deltares.nl',
    packages=find_packages(),
    description='BMI-compatible runner for combined DFLOW/DWAVES computations',
    long_description=open('README.txt').read(),
    install_requires=[
    ],
)
