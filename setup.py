from setuptools import setup, find_packages
import os.path

long_description = None
readmeLocation = os.path.join(os.path.dirname(__file__), "README.rst")
with open(readmeLocation) as readmeFile:
  long_description = readmeFile.read()

requires=['numpy','matplotlib','pytz','pyephem','astropy',"astroplan","skyfield"]

setup(name='astroobsplanner',
      description='Astronomy Observability Planner',
      long_description=long_description,
      author='Justin Hugon',
      author_email='opensource AT hugonweb.com',
      version='1.0.beta',
      packages=find_packages(),
      license='GPLv3',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        ],
      entry_points = {
        'gui_scripts':['astroobsplanner = astroobsplanner:main'],
        'console_scripts':[
            'astroobsplannercmd = astroobsplanner.makeobsplot:main',
            'astroobsplanneraltcmd = astroobsplanner.makealtplot:main',
            'astroobsplannerschedcmd = astroobsplanner.makeplan:main',
        ]
      },
      provides=['astroobsplanner'],
      setup_requires = requires,
      install_requires = requires,
      )

