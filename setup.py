from setuptools import setup

with open('README.md') as readme:
    long_desc = readme.read()

with open('requirements.txt') as requirements:
    requires = requirements.readlines()

setup(
    name='concatrim',
    version='1.0.3',
    python_requires='>=3',
    packages=['concatrim'],
    url='https://github.com/keighrim/concatrim',
    license='MIT',
    author='Keigh Rim',
    author_email='krim@brandeis.edu',
    description='Python program to trim-then-concatenate A/V media files using ffmpeg',
    long_description=long_desc,
    long_description_content_type="text/markdown",
    install_requires=requires,
)
