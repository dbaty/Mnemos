import os
from setuptools import find_packages
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = ('celery',
            'deform',
            'deform_ext_autocomplete',
            'pymongo',
            'pyramid',
            'pyramid_celery',
            'pyramid_deform',
            'pyramid_beaker',
            'requests')

setup(name='Mnemos',
      version='0.1.0',
      description='Mnemos is a simple personal address book.',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Pyramid',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Natural Language :: French',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'),
      author='Damien Baty',
      author_email='damien.baty.remove@gmail.com',
      url='https://github.com/dbaty/Mnemos',
      keywords='web pyramid pylons address book contact directory',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      test_suite='mnemos.tests',
      entry_points = '''
      [paste.app_factory]
      main = mnemos.app:make_app
      ''',
      message_extractors={'.': (
            ('**.py', 'lingua_python', None),
            ('**.pt', 'lingua_xml', None),
            )},
      )
