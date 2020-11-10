#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import sys
import argparse
import datetime
import numpy
import pytz

from matplotlib import pyplot as mpl
from matplotlib.dates import HourLocator, DateFormatter
from matplotlib.backends.backend_pdf import PdfPages

from astropy.time import Time
from astropy.table import Table
import astropy.units as u

from astroplan import Observer, FixedTarget, AltitudeConstraint, AirmassConstraint, AtNightConstraint, MoonSeparationConstraint, MoonIlluminationConstraint
from astroplan import months_observable, is_always_observable, is_observable
from astroplan.utils import time_grid_from_range

from .lookuptarget import lookuptarget, lookuptargettype, CALDWELL_MAP

def makeTargetLabels(nameList,args):
    targetTypes = [lookuptargettype(name) for name in nameList]

    result = []
    seperator = " "
    ylabelsize = "x-small"
    if len(nameList) < 25:
        seperator = "\n"
        ylabelsize = "medium"
    for x,t in zip(nameList,targetTypes):
            thisResult = ""
            try:
                othername = CALDWELL_MAP[x.lower()]
            except KeyError:
                thisResult += x
            else:
                if ("ngc" in othername) or ("ic" in othername):
                    othername = othername.upper()
                thisResult += f"{x} ({othername})"
            if args.showType:
                thisResult += f"{seperator}{t[0]}"
            result.append(thisResult)
    return result, ylabelsize

def run_months(observers, nameList, args):
    targets = [FixedTarget(coord=lookuptarget(name),name=name) for name in nameList]
    targetLabelList, ylabelsize = makeTargetLabels(nameList,args)

    constraints = [
        AltitudeConstraint(min=args.minAlt*u.deg),
        AtNightConstraint.twilight_astronomical(),
    ]
    
    outfn = args.outFileNameBase+"_monthly.pdf"
    with PdfPages(outfn) as pdf:
        for observer in observers:
            observability_months_table = months_observable(constraints,observer,targets,time_grid_resolution=1*u.hour)

            observability_months_grid = numpy.zeros((len(targets),12))
            for i, observable in enumerate(observability_months_table):
                for jMonth in range(1,13):
                    observability_months_grid[i,jMonth-1] = jMonth in observable

            observable_targets = targets
            observable_target_labels = targetLabelList
            ever_observability_months_grid = observability_months_grid
            if args.onlyEverObservable:
                target_is_observable = numpy.zeros(len(targets))
                for iMonth in range(observability_months_grid.shape[1]):
                    target_is_observable += observability_months_grid[:,iMonth]
                target_is_observable = target_is_observable > 0. # change to boolean numpy array
                observable_targets = [x for x, o in zip(targets,target_is_observable) if o]
                observable_target_labels = [x for x, o in zip(targetLabelList,target_is_observable) if o]
                ever_observability_months_grid = observability_months_grid[target_is_observable,:]

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
            extent = [-0.5, -0.5+12, -0.5, len(observable_targets)-0.5]
            ax.imshow(ever_observability_months_grid, extent=extent, origin="lower", aspect="auto", cmap=mpl.get_cmap("Greens"))
            ax.xaxis.tick_top()
            ax.invert_yaxis()
            ax.set_yticks(range(0,len(observable_targets)))
            ax.set_yticklabels(observable_target_labels, fontsize=ylabelsize)
            ax.set_xticks(range(12))
            ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
            ax.set_xticks(numpy.arange(extent[0], extent[1]), minor=True)
            ax.set_yticks(numpy.arange(extent[2], extent[3]), minor=True)
            ax.grid(which="minor",color="white",ls="-", linewidth=2)
            ax.tick_params(axis='y', which='minor', left=False, right=False)
            ax.tick_params(axis='x', which='minor', bottom=False, top=False)
        
            fig.suptitle(f"Monthly Observability at {observer.name}")
            fig.text(1.0,0.0,"Constraints: Astronomical Twilight, Altitude $\geq {:.0f}^\circ$".format(args.minAlt),ha="right",va="bottom")
            pdf.savefig(fig)
        print(f"Writing out file: {outfn}")

def run_nights(observers, nameList, args):
    # Define range of times to observe between
    startDate = datetime.datetime.strptime(args.startDate,"%Y-%m-%d")
    beginTimeFirstNight = datetime.datetime(startDate.year,startDate.month,startDate.day,hour=16)
    endTimeFirstNight = beginTimeFirstNight + datetime.timedelta(hours=16)
    t_datetimes_nights_list = []
    for iDay in range(args.nNights):
        beginTime = beginTimeFirstNight + datetime.timedelta(days=iDay)
        endTime = endTimeFirstNight + datetime.timedelta(days=iDay)
        currTime = beginTime
        t_datetime = []
        while currTime <= endTime:
            t_datetime.append(currTime)
            currTime += datetime.timedelta(hours=1)
        t_datetimes_nights_list.append(t_datetime)

    targets = [FixedTarget(coord=lookuptarget(name),name=name) for name in nameList]
    targetLabelList, ylabelsize = makeTargetLabels(nameList,args)

    constraints = [
        AltitudeConstraint(min=args.minAlt*u.deg),
        AtNightConstraint.twilight_astronomical(),
        MoonSeparationConstraint(min=args.minMoonSep*u.deg),
        MoonIlluminationConstraint(max=args.maxMoonIllum),
    ]

    outfn = args.outFileNameBase+"_nightly.pdf"
    with PdfPages(outfn) as pdf:
        for observer in observers:
            fig, axes = mpl.subplots(
                figsize=(8.5,11),
                ncols=args.nNights,
                sharex="col",
                gridspec_kw={
                    "top":0.92,
                    "bottom":0.03,
                    "left":0.13,
                    "right":0.98,
                    "hspace":0,
                    "wspace":0
                },
                tight_layout=False,constrained_layout=False
            )

            observability_grids = []
            for iNight in range(args.nNights):
                t_datetime = t_datetimes_nights_list[iNight]
                time_grid = [Time(observer.timezone.localize(t)) for t in t_datetime]
                
                observability_grid = numpy.zeros((len(targets),len(time_grid)-1))
                for i in range(len(time_grid)-1):
                    tmp = is_always_observable(constraints, observer, targets, times=[time_grid[i],time_grid[i+1]])
                    observability_grid[:, i] = tmp
                observability_grids.append(observability_grid)

            observable_targets = targets
            observable_target_labels = targetLabelList
            ever_observability_grids = observability_grids
            if args.onlyEverObservable:
                target_is_observable = numpy.zeros(len(targets))
                for observability_grid in observability_grids:
                    for iTime in range(observability_grid.shape[1]):
                        target_is_observable += observability_grid[:,iTime]
                target_is_observable = target_is_observable > 0. # change to boolean numpy array
                observable_targets = [x for x, o in zip(targets,target_is_observable) if o]
                observable_target_labels = [x for x, o in zip(targetLabelList,target_is_observable) if o]
                ever_observability_grids = []
                for observability_grid in observability_grids:
                    ever_observability_grid = observability_grid[target_is_observable,:]
                    ever_observability_grids.append(ever_observability_grid)

            for iNight in range(args.nNights):
                ax = axes[iNight]
                t_datetime = t_datetimes_nights_list[iNight]
                extent = [0, len(t_datetime)-1, -0.5, len(observable_targets)-0.5]
                ax.imshow(ever_observability_grids[iNight], extent=extent, origin="lower", aspect="auto", cmap=mpl.get_cmap("Greens"))
                ax.xaxis.tick_top()
                ax.xaxis.set_label_position("top")
                ax.invert_yaxis()

                if iNight == 0:
                    ax.set_yticks(range(0,len(observable_targets)))
                    ax.set_yticklabels(observable_target_labels, fontsize=ylabelsize)
                else:
                    ax.set_yticks([])

                ax.set_xticks(range(0,len(t_datetime)-1,4))
                ax.set_xticks(range(0,len(t_datetime)),minor=True)
                ax.set_xticklabels([t_datetime[i].strftime("%Hh") for i in range(0,len(t_datetime)-1,4)])

                ax.set_xlabel(t_datetime[0].strftime("%a %b %d"))

                ax.set_yticks(numpy.arange(extent[2], extent[3]), minor=True)

                ax.grid(axis="x",which="both",color="white",ls="-", linewidth=1)
                ax.grid(axis="y",which="minor",color="white",ls="-", linewidth=1)

                ax.tick_params(axis='y', which='minor', left=False, right=False)
                ax.tick_params(axis='x', which='minor', bottom=False, top=False)
        
            fig.suptitle(f"Observability at {observer.name} in {startDate.year}")
            fig.text(1.0,0.0,"Constraints: Astronomical Twilight, Altitude $\geq {:.0f}^\circ$, Moon Seperation $\geq {:.0f}^\circ$, Moon Illumination $\leq {:.2f}$".format(args.minAlt,args.minMoonSep,args.maxMoonIllum),ha="right",va="bottom")
            pdf.savefig(fig)
        print(f"Writing out file: {outfn}")


def main():
    parser = argparse.ArgumentParser(description="Makes observability tables. Best to include less than 100 or so targets")
    parser.add_argument("outFileNameBase",help="Output file name base (will end in _monthly.pdf for month chart, etc.")
    parser.add_argument("objectNames",nargs='*',help='Object name (e.g. "M42" "Polaris" "Gam Cru" "Orion Nebula")')
    parser.add_argument("--monthly",'-m',action="store_true",help="Make monthly visibility, otherwise, run nightly chart")
    parser.add_argument("--startDate",'-s',default=str(datetime.date.today()),help=f"Start date in ISO format YYYY-MM-DD (default: today, {datetime.date.today()})")
    parser.add_argument("--nNights",'-n',type=int,default=5,help=f"Number of nights to show including STARTDATE (default: 5)")
    parser.add_argument("--minAlt",'-a',type=float,default=45,help=f"Minimum altitude constraint, in degrees (default: 45)")
    parser.add_argument("--minMoonSep",type=float,default=60,help=f"Minimum angular seperation between target and moon constraint, in degrees (default: 60)")
    parser.add_argument("--maxMoonIllum",type=float,default=0.05,help=f"Maximum fractional moon illumination constraint: a float between 0.0 and 1.0. Also satisfied if moon has set. (default: 0.05)")
    parser.add_argument("--onlyEverObservable",'-o',action="store_true",help="For each site, only display objects that are ever observable in the time range (get rid of empty rows)")
    parser.add_argument("--showType",action="store_true",help="For each object, list the main type returned from looking it up in SIMBAD in the tables")
    parser.add_argument("--printObjectLists","-p",action="store_true",help="Print out Messier and Caldwell catalogues.")
    parser.add_argument("--GlCl",action="store_true",help="Run all globular clusters from Messier and Caldwell catalogues")
    parser.add_argument("--OpCl",action="store_true",help="Run all open clusters from Messier and Caldwell catalogues")
    parser.add_argument("--G",'-g',action="store_true",help="Run all galaxies from Messier and Caldwell catalogues")
    parser.add_argument("--PN",action="store_true",help="Run all planatary nebulae from Messier and Caldwell catalogues")
    parser.add_argument("--Other",action="store_true",help="Run everything else from Messier and Caldwell catalogues")
    parser.add_argument("--HCG",action="store_true",help="Run all of Hickson's Compact Groups of galaxies")
    args = parser.parse_args()

    observers = [
            Observer(name="NM Skies",latitude=32.903308333333335*u.deg,longitude=-106.96066666666667*u.deg,elevation=2225.*u.meter,timezone='US/Mountain'),
            Observer(name="Sierra Remote Obs., CA",latitude=37.0703*u.deg,longitude=-119.4128*u.deg,elevation=1405.*u.meter,timezone='US/Pacific'),
            Observer(name="AstroCamp, Spain",latitude=38.15*u.deg,longitude=-2.31*u.deg,elevation=1650.*u.meter,timezone='Europe/Madrid'),
            Observer(name="Siding Spring, AUS",latitude=-31.27333*u.deg,longitude=-149.064444*u.deg,elevation=1165.*u.meter,timezone='Australia/Melbourne'),
    ]

    messierAndCaldwellNames = ["M"+str(i) for i in range(1,111)]+["C"+str(i) for i in range(1,110)]
    messierAndCaldwellTypes = [lookuptargettype(name) for name in messierAndCaldwellNames]
    messierAndCaldwellGlClNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "GlCl" in t] # globular clusters
    messierAndCaldwellOpClNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "OpCl" == t[0]] # main type open cluster
    messierAndCaldwellGNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "G" in t and not ("GlCl" == t[0]) and not ("OpCl" == t[0]) and not ("PN" == t[0]) and not ("SNR" == t[0]) and not ("HII" == t[0])] # galaxies
    messierAndCaldwellPNNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if "PN" in t] # planetary nebulae
    messierAndCaldwellNotGNorGlClNorOpClNorPNNames = [n for n,t in zip(messierAndCaldwellNames,messierAndCaldwellTypes) if not (("G" in t) or ("GlCl" in t) or ("OpCl" == t[0]) or ("PN" in t))] # not galaxies nor globular clusters nor main type open cluster nor planetary nebula

    HCGNames = ["HCG"+str(i) for i in range(1,101)] # Hickson's Compact Groups of galaxies
    
    if args.printObjectLists:
        print(f"GlCl: {len(messierAndCaldwellGlClNames)}")
        for name in messierAndCaldwellGlClNames:
            print(f"  {name}: {lookuptargettype(name)}")
        print(f"OpCl: {len(messierAndCaldwellOpClNames)}")
        for name in messierAndCaldwellOpClNames:
            print(f"  {name}: {lookuptargettype(name)}")
        print(f"G: {len(messierAndCaldwellGNames)}")
        for name in messierAndCaldwellGNames:
            print(f"  {name}: {lookuptargettype(name)}")
        print(f"PN: {len(messierAndCaldwellPNNames)}")
        for name in messierAndCaldwellPNNames:
            print(f"  {name}: {lookuptargettype(name)}")
        print(f"Not G nor GlCl nor OpCl nor PN: {len(messierAndCaldwellNotGNorGlClNorOpClNorPNNames)}")
        for name in messierAndCaldwellNotGNorGlClNorOpClNorPNNames:
            print(f"  {name}: {lookuptargettype(name)}")
        print(f"Hickson's Compact Groups of galaxies:")
        for name in HCGNames:
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
    if args.HCG:
        nameList += HCGNames
    
    if args.monthly:
        run_months(observers, nameList, args)
    run_nights(observers, nameList, args)
