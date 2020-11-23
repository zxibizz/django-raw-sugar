import os
from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open("README.md", 'r') as f:
    long_description = f.read()
    print(long_description)

setup(
    name='django-raw-sugar',
    version='0.1.14',
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    description='Turns your raw sql into a QuerySet',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/zxibizz/django-raw-sugar',
    author='Roman Lee',
    author_email='romanlee1996@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
