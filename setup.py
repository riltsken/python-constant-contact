from setuptools import setup, find_packages

setup(
    name='python-constantcontact',
    version='0.1',
    description='Constant contact lib for python, with stuff for Django too',
    author='Sam Toriel',
    author_email='samueltoriel@gmail.com',
    url='http://github.com/riltsken/python-constantcontact/tree/master',
    packages=find_packages(),
	install_requires=['httplib2','feedparser'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
