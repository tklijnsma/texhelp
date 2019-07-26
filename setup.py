from setuptools import setup

setup(name='texhelp',
      version='0.1',
      description='Helps with tex files',
      url='https://github.com/tklijnsma/texhelp.git',
      author='Thomas Klijnsma',
      author_email='thomasklijnsma@gmail.com',
      packages=['texhelp'],
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'],
      scripts=[
        'bin/texhelp-structure',
        'bin/texhelp-cites',
        'bin/texhelp-ascii',
        'bin/texhelp-bib',
        'bin/texhelp-flatten',
        'bin/texhelp-commands',
        'bin/texhelp-cmsfigrenaming',
        # 
        # 'bin/texhelp-figs',
        # 'bin/texhelp-imgs',
        # 'bin/texhelp-cmp',
        # 'bin/texhelp-inputs',
        # 'bin/texhelp-labels',
        ]
      )