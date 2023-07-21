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

from .lookuptarget import lookuptarget

def run_nightlist(observers, nameList, args):
    assert(len(observers)>0)
    assert(len(nameList)>0)
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
            currTime += datetime.timedelta(minutes=30)
        t_datetimes_nights_list.append(t_datetime)

    targets = [FixedTarget(coord=lookuptarget(name),name=name) for name in nameList]

    constraints = [
        AltitudeConstraint(min=args.minAlt*u.deg),
        AtNightConstraint.twilight_astronomical(),
        MoonSeparationConstraint(min=args.minMoonSep*u.deg),
        MoonIlluminationConstraint(max=args.maxMoonIllum),
    ]

    for observer in observers:
        print(observer.name)
        observable_ranges = {}
        for target in targets:
            observable_ranges[target.name] = []
        for iNight in range(args.nNights):
            t_datetime = t_datetimes_nights_list[iNight]
            time_grid = [Time(observer.timezone.localize(t)) for t in t_datetime]
            
            observability_grid = numpy.zeros((len(targets),len(time_grid)-1))
            for i in range(len(time_grid)-1):
                tmp = is_always_observable(constraints, observer, targets, times=[time_grid[i],time_grid[i+1]])
                observability_grid[:, i] = tmp
            observability_grid = numpy.isclose(observability_grid,1.)
            observable_at_all_this_night = numpy.any(observability_grid,axis=1)
            for iTarget, target in enumerate(targets):
                if observable_at_all_this_night[iTarget]:
                    observable_blocks = [(t_datetime[i],t_datetime[i+1]) for i in range(len(time_grid)-1) if observability_grid[iTarget,i]]
                    nBlocks = len(observable_blocks)
                    time_ranges = [[observable_blocks[0][0],None]]
                    for iBlock in range(nBlocks):
                        if iBlock + 1 < nBlocks:
                            if observable_blocks[iBlock][1] != observable_blocks[iBlock+1][0]:
                                time_ranges[-1][1] = observable_blocks[iBlock][1]
                                time_ranges.append([observable_blocks[iBlock+1][0],None])
                        else:
                                time_ranges[-1][1] = observable_blocks[iBlock][1]
                    observable_ranges[target.name].append((t_datetime[0],time_ranges))
        for target in targets:
            print(f"{target.name}")
            for obs_range in observable_ranges[target.name]:
                line = obs_range[0].date().isoformat() + ":"
                for t_range in obs_range[1]:
                    line += f" {t_range[0].time().isoformat('minutes')} - {t_range[1].time().isoformat('minutes')}"
                print(line)

def main():
    parser = argparse.ArgumentParser(description="Lists nights when the object(s) are observable, and the times in those nights.")
    parser.add_argument("objectNames",nargs='*',help='Object name (e.g. "M42" "Polaris" "Gam Cru" "Orion Nebula")')
    parser.add_argument("--textFileObjNames",'-t',help="A newline seperated list of object names is in the text file. Funcions just like extra objectNames")
    parser.add_argument("--startDate",'-s',default=str(datetime.date.today()),help=f"Start date in ISO format YYYY-MM-DD (default: today, {datetime.date.today()})")
    parser.add_argument("--nNights",'-n',type=int,default=5,help=f"Number of nights to show including STARTDATE (default: 5)")
    parser.add_argument("--minAlt",'-a',type=float,default=45,help=f"Minimum altitude constraint, in degrees (default: 45)")
    parser.add_argument("--minMoonSep",type=float,default=60,help=f"Minimum angular seperation between target and moon constraint, in degrees (default: 60)")
    parser.add_argument("--maxMoonIllum",type=float,default=0.05,help=f"Maximum fractional moon illumination constraint: a float between 0.0 and 1.0. Also satisfied if moon has set. (default: 0.05)")
    args = parser.parse_args()

    observers = [
            Observer(name="NM Skies",latitude=32.9033*u.deg,longitude=-106.9606*u.deg,elevation=2225.*u.meter,timezone='US/Mountain'),
            Observer(name="Sierra Remote Obs., CA",latitude=37.0703*u.deg,longitude=-119.4128*u.deg,elevation=1405.*u.meter,timezone='US/Pacific'),
            Observer(name="Utah Desert Remote Obs.",latitude=37.7378*u.deg,longitude=-113.6975*u.deg,elevation=1570.*u.meter,timezone='US/Mountain'),
            Observer(name="AstroCamp, Spain",latitude=38.15*u.deg,longitude=-2.31*u.deg,elevation=1650.*u.meter,timezone='Europe/Madrid'),
            Observer(name="EEyE, Spain",latitude=38.1284*u.deg,longitude=-6.6303*u.deg,elevation=560.*u.meter,timezone='Europe/Madrid'),
            Observer(name="Siding Spring, AUS",latitude=-31.2733*u.deg,longitude=149.0644*u.deg,elevation=1165.*u.meter,timezone='Australia/Melbourne'),
            Observer(name="Deep Sky Chile",latitude=-30.5263*u.deg,longitude=-70.8533*u.deg,elevation=1710.*u.meter,timezone='America/Santiago'),
    ]

    nameList = args.objectNames
    if args.textFileObjNames:
        print(f"Reading object names from: '{args.textFileObjNames}'")
        try:
            with open(args.textFileObjNames) as infile:
                for line in infile.readlines():
                    nameList.append(line.strip("\n"))
        except FileNotFoundError as e:
            print(f"Error: {e}, exiting.")
            sys.exit(1)
    
    run_nightlist(observers, nameList, args)
