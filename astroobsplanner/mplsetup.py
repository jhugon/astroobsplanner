#!/usr/bin/env python2
# vim: set fileencoding=utf-8

from matplotlib import pyplot as mpl

def mplSetupStandard():
  mpl.rcdefaults() 
  mpl.rc('figure',
        dpi         = 100,
        figsize     = (6,6),
        facecolor   = 'white',
        autolayout  = True
        )

def mplSetupSmall():
  mplSetupStandard()
  mpl.rc('font',
        size         = 10.0
        )

mplSetupStandard()
