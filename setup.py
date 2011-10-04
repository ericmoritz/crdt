from setuptools import setup, find_packages
import sys, os

version = '0.0.1a'

setup(name='crdt',
      version=version,
      description="A toolbox of CRDT classes",
      long_description="""\
A toolbox of Convergent and Commutative Replicated Data Types as defined by http://hal.archives-ouvertes.fr/docs/00/55/55/88/PDF/techreport.pdf""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='crdt distributed nosql',
      author='Eric Moritz',
      author_email='eric@themoritzfamily.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
