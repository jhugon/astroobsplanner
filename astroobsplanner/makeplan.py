#!/usr/bin/env python2
# vim: set fileencoding=utf-8


import sys
import argparse
import datetime
import pytz
import numpy
from matplotlib import pyplot as mpl
from matplotlib.dates import HourLocator, DateFormatter

from astropy.time import Time
from astropy.table import Table
import astropy.units as u

from astroplan import Observer, FixedTarget, AltitudeConstraint, AirmassConstraint, AtNightConstraint, MoonSeparationConstraint, MoonIlluminationConstraint
from astroplan import months_observable

from .lookuptarget import lookuptarget, lookuptargettype

def monthly_observability_to_table():
    observability_table = Table()
    observability_table['targets'] = [target.name for target in targets]
    observability_table['ever_observable'] = ever_observable
    observability_table['always_observable'] = always_observable
    return observability_table

def run():

    observers = [
            Observer(name="NMSkies",latitude=32.903308333333335*u.deg,longitude=-106.96066666666667*u.deg,elevation=2225.*u.meter,timezone='US/Mountain'),
    ]

    #time_range = Time(["2020-11-01 00:00", "2021-10-31 00:00"])
    
    nameList = ["M"+str(i) for i in range(1,111)]
    #nameList = ["C"+str(i) for i in range(1,110)]
    #nameList = ["C"+str(i) for i in range(1,75)]
    targets = [FixedTarget(coord=lookuptarget(name),name=name) for name in nameList]
    targetTypes = [lookuptargettype(name) for name in nameList]

    ylabelsize = "medium"
    if len(targets) < 25:
        targetLabelList = ["{0}\n({1})".format(x,t) for x, t in zip(nameList,targetTypes)]
        ylabelsize = "medium"
    else:
        targetLabelList = ["{0} ({1})".format(x,t) for x, t in zip(nameList,targetTypes)]
        ylabelsize = "x-small"

    minAlt = 45
    minMoonSep = 50

    constraints = [
        AltitudeConstraint(min=minAlt*u.deg),
        AtNightConstraint.twilight_astronomical(),
        MoonSeparationConstraint(min=minMoonSep*u.deg),
    ]
    
    for observer in observers:
        observability_months_table = months_observable(constraints,observer,targets)

        observability_months_grid = numpy.zeros((len(targets),12))
        for i, observable in enumerate(observability_months_table):
            for jMonth in range(1,13):
                observability_months_grid[i,jMonth-1] = jMonth in observable

        fig, ax = mpl.subplots(
            figsize=(8.5,11),
            gridspec_kw={
                "top":0.92,
                "bottom":0.03,
                "left":0.13,
                "right":0.98,
            },
            tight_layout=False,constrained_layout=False
        )
        extent = [-0.5, -0.5+12, -0.5, len(targets)-0.5]
        ax.imshow(observability_months_grid, extent=extent, origin="lower", aspect="auto", cmap=mpl.get_cmap("Greens"))
        ax.xaxis.tick_top()
        ax.invert_yaxis()
        ax.set_yticks(range(0,len(targets)))
        ax.set_yticklabels(targetLabelList, fontsize=ylabelsize)
        ax.set_xticks(range(12))
        ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
        ax.set_xticks(numpy.arange(extent[0], extent[1]), minor=True)
        ax.set_yticks(numpy.arange(extent[2], extent[3]), minor=True)
        ax.grid(which="minor",color="white",ls="-", linewidth=2)
        ax.tick_params(axis='y', which='minor', left='off')
        ax.tick_params(axis='x', which='minor', bottom='off')
    
        fig.suptitle(f"Monthly Observability from {observer.name}")
        fig.text(1.0,0.0,"Constraints: Astronomical Twilight, Altitude $\geq {:.0f}^\circ$, Moon Seperation $\geq {:.0f}^\circ$".format(minAlt,minMoonSep),ha="right",va="bottom")
        fig.savefig("sched_months.pdf")
        

def main():
    parser = argparse.ArgumentParser(description="Makes observability tables. Best to include less than 50 or so targets")
    #parser.add_argument("outFileNames",metavar="out",nargs=1,help="Output file name (e.g. report1.png)")
    #parser.add_argument("objectNames",metavar="object",nargs='+',help='Object name (e.g. "M42" "Polaris" "Gam Cru" "Orion Nebula")')
    #parser.add_argument("--startDate",'-s',default=str(datetime.date.today()),help=f"Start date in ISO format YYYY-MM-DD (default: today, {datetime.date.today()})")
    #parser.add_argument("--nNights",'-n',type=int,default=5,help=f"Number of nights to show including STARTDATE (default: 5)")
    #parser.add_argument("--bw",action="store_true",help="Black and white mode.")
    args = parser.parse_args()
    
    run()
