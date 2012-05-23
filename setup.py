from setuptools import setup, find_packages
import os

version = '0.1dev'

setup(name='uu.retrieval',
      version=version,
      description='Components for information retrieval, search, '\
                  'query, indexing for arbitrary schema-driven '\
                  'objects.',
      long_description=open('README.txt').read() + '\n' +
                       open(os.path.join('docs', 'HISTORY.txt')).read(),
      classifiers=[
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Framework :: ZODB',
        ],
      keywords='',
      author='Sean Upton',
      author_email='sean.upton@hsc.utah.edu',
      url='http://launchpad.net/upiq',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['uu'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'ZODB3',
          'zope.app.content',
          'zope.component',
          'zope.index',
          'zope.schema>=3.8.0',
          'repoze.catalog>=0.8.0',
          'plone.uuid',
          # -*- Extra requirements: -*-
      ],
      extras_require = {
          'test': [ 
            ## test running requires basic zope2 stack for integration
            ## tests
            'plone.testing [zodb, zca, security, publisher, z2]',
            'Products.CMFCore>=2.2.3',
            'zope.configuration',
            ],
      },
      entry_points='''
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      ''',
      )

