# Author: Anand Patil
# Date: 6 Feb 2009
# License: Creative Commons BY-NC-SA
####################################

from setuptools import setup
from numpy.distutils.misc_util import Configuration
import os
config = Configuration('map_utils',parent_package=None,top_path=None)

config.add_extension(name='variograms.directions',sources=['map_utils/variograms/directions.f'])

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(  version="0.1",
            description="The Malaria Atlas Project's utility functions.",
            author="Peter Gething and Anand Patil", 
            author_email="map@map.ox.ac.uk",
            url="www.map.ox.ac.uk",
            packages=['map_utils','map_utils/variograms'],
            license="Public domain",
            **(config.todict()))
    for ex_fname in ['trace-to-txt']:
        os.system('chmod ugo+x %s'%ex_fname)
        os.system('cp %s /usr/local/bin'%ex_fname)

