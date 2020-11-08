#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import sys
import argparse
import datetime
import numpy

from matplotlib import pyplot as mpl
from matplotlib.dates import HourLocator, DateFormatter
from matplotlib.backends.backend_pdf import PdfPages

from astropy.time import Time
from astropy.table import Table
import astropy.units as u

from astroplan import Observer, FixedTarget, AltitudeConstraint, AirmassConstraint, AtNightConstraint, MoonSeparationConstraint, MoonIlluminationConstraint
from astroplan import months_observable

from .lookuptarget import lookuptarget, lookuptargettype

def run_months(observers, nameList, outFileNameBase):

    targets = [FixedTarget(coord=lookuptarget(name),name=name) for name in nameList]
    targetTypes = [lookuptargettype(name) for name in nameList]

    ylabelsize = "medium"
    if len(targets) < 25:
        targetLabelList = ["{0}\n({1})".format(x,t[0]) for x, t in zip(nameList,targetTypes)]
        ylabelsize = "medium"
    else:
        targetLabelList = ["{0} ({1})".format(x,t[0]) for x, t in zip(nameList,targetTypes)]
        ylabelsize = "x-small"

    minAlt = 45
    minMoonSep = 50

    constraints = [
        AltitudeConstraint(min=minAlt*u.deg),
        AtNightConstraint.twilight_astronomical(),
        #MoonSeparationConstraint(min=minMoonSep*u.deg),
    ]
    
    outfn = outFileNameBase+"_monthly.pdf"
    with PdfPages(outfn) as pdf:
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
            #fig.text(1.0,0.0,"Constraints: Astronomical Twilight, Altitude $\geq {:.0f}^\circ$, Moon Seperation $\geq {:.0f}^\circ$".format(minAlt,minMoonSep),ha="right",va="bottom")
            fig.text(1.0,0.0,"Constraints: Astronomical Twilight, Altitude $\geq {:.0f}^\circ$".format(minAlt),ha="right",va="bottom")
            pdf.savefig(fig)
        print(f"Writing out file: {outfn}")
        

def main():
    parser = argparse.ArgumentParser(description="Makes observability tables. Best to include less than 50 or so targets")
    parser.add_argument("outFileNameBase",help="Output file name base (will end in _monthly.pdf for month chart, etc.")
    parser.add_argument("objectNames",nargs='*',help='Object name (e.g. "M42" "Polaris" "Gam Cru" "Orion Nebula")')
    #parser.add_argument("--startDate",'-s',default=str(datetime.date.today()),help=f"Start date in ISO format YYYY-MM-DD (default: today, {datetime.date.today()})")
    #parser.add_argument("--nNights",'-n',type=int,default=5,help=f"Number of nights to show including STARTDATE (default: 5)")
    parser.add_argument("--printObjectLists","-p",action="store_true",help="Print out Messier and Caldwell catalogues.")
    parser.add_argument("--GlCl",action="store_true",help="Run all globular clusters from Messier and Caldwell catalogues")
    parser.add_argument("--OpCl",action="store_true",help="Run all open clusters from Messier and Caldwell catalogues")
    parser.add_argument("--G",'-g',action="store_true",help="Run all galaxies from Messier and Caldwell catalogues")
    parser.add_argument("--PN",action="store_true",help="Run all planatary nebulae from Messier and Caldwell catalogues")
    parser.add_argument("--Other",action="store_true",help="Run everything else from Messier and Caldwell catalogues")
    args = parser.parse_args()

    observers = [
            Observer(name="NM Skies",latitude=32.903308333333335*u.deg,longitude=-106.96066666666667*u.deg,elevation=2225.*u.meter,timezone='US/Mountain'),
            Observer(name="Sierra Remote Obs., CA",latitude=37.0703*u.deg,longitude=-119.4128*u.deg,elevation=1405.*u.meter,timezone='US/Pacific'),
            Observer(name="AstroCamp, Spain",latitude=38.15*u.deg,longitude=-2.31*u.deg,elevation=1650.*u.meter,timezone='Europe/Madrid'),
            Observer(name="Siding Spring, AUS",latitude=-31.27333*u.deg,longitude=-149.064444*u.deg,elevation=1165.*u.meter,timezone='Australia/Melbourne'),
    ]

    #time_range = Time(["2020-11-01 00:00", "2021-10-31 00:00"])
    
    messierAndCaldwellNames = ["M"+str(i) for i in range(1,111)]+["C"+str(i) for i in range(1,110)]
    messierAndCaldwellTypes = [lookuptargettype(name) for name in messierAndCaldwellNames]
    messierAndCaldwellGlClNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "GlCl" in t] # globular clusters
    messierAndCaldwellOpClNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "OpCl" == t[0]] # main type open cluster
    messierAndCaldwellGNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "G" in t] # galaxies
    messierAndCaldwellPNNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "PN" in t] # planetary nebulae
    messierAndCaldwellNotGNorGlClNorOpClNorPNNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if not (("G" in t) or ("GlCl" in t) or ("OpCl" == t[0]) or ("PN" in t))] # not galaxies nor globular clusters nor main type open cluster nor planetary nebula
    
    if args.printObjectLists:
        print(f"GlCl: {len(messierAndCaldwellGlClNames)}")
        for name in messierAndCaldwellGlClNames:
            print(f"  {name}")
        print(f"OpCl: {len(messierAndCaldwellOpClNames)}")
        for name in messierAndCaldwellOpClNames:
            print(f"  {name}: {lookuptargettype(name)}")
        print(f"G: {len(messierAndCaldwellGNames)}")
        for name in messierAndCaldwellGNames:
            print(f"  {name}")
        print(f"PN: {len(messierAndCaldwellPNNames)}")
        for name in messierAndCaldwellPNNames:
            print(f"  {name}: {lookuptargettype(name)}")
        print(f"Not G nor GlCl nor OpCl nor PN: {len(messierAndCaldwellNotGNorGlClNorOpClNorPNNames)}")
        for name in messierAndCaldwellNotGNorGlClNorOpClNorPNNames:
            print(f"  {name}: {lookuptargettype(name)}")
        sys.exit(0)

    nameList = args.objectNames
    messierAndCaldwellNamesToUse = []
    if args.GlCl:
        messierAndCaldwellNamesToUse += messierAndCaldwellGlClNames
    if args.OpCl:
        messierAndCaldwellNamesToUse += messierAndCaldwellOpClNames
    if args.G:
        messierAndCaldwellNamesToUse += messierAndCaldwellGNames
    if args.PN:
        messierAndCaldwellNamesToUse += messierAndCaldwellPNNames
    if args.Other:
        messierAndCaldwellNamesToUse += messierAndCaldwellNotGNorGlClNorOpClNorPNNames
    #messierAndCaldwellNamesToUse.sort() #need number sort not lexical
    nameList += messierAndCaldwellNamesToUse
    
    run_months(observers, nameList, args.outFileNameBase)
