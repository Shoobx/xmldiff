from io import open
from setuptools import setup, find_packages

version = '2.0rc1'

with open('README.rst', 'rt', encoding='utf8') as readme:
    description = readme.read()

with open('CHANGES.rst', 'rt', encoding='utf8') as changes:
    history = changes.read()


setup(name='xmldiff',
      version=version,
      description="Creates diffs of XML files",
      long_description=description + '\n' + history,
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Development Status :: 4 - Beta',
                   'Topic :: Text Processing :: Markup :: XML',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'License :: OSI Approved :: MIT License',
                   ],
      keywords='xml html diff',
      author='Lennart Regebro',
      author_email='lregebro@shoobx.com',
      url='https://github.com/Shoobx/xmldiff',
      license='MIT',
      packages=find_packages(exclude=['doc', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'lxml>=3.1.0',
          'six',
      ],
      test_suite='tests',
      entry_points={
               'console_scripts': [
                   'xmldiff = xmldiff.main:run',
               ],
      },
)
