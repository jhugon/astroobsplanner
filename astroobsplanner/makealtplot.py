#!/usr/bin/env python2
# vim: set fileencoding=utf-8

from skyfield.api import load, Topos
from skyfield.starlib import Star
from skyfield import almanac
from matplotlib.dates import HourLocator, DateFormatter

def find_twilight(location,t_timescale_nights_local_list):
    planets = load("de421.bsp")
    topo = Topos(location["latitude"],location["longitude"],elevation_m=location["elevation"])
    result = []
    for  t_night in t_timescale_nights_local_list:
        t_start = t_night[0]
        t_end = t_night[-1]
        f = almanac.dark_twilight_day(planets,topo)
        ts, twilight_types = almanac.find_discrete(t_start,t_end,f)
        t_night_start = None
        t_night_end = None
        for t, twilight_type in zip(ts, twilight_types):
            #print(twilight_type, t, t.utc_iso(), ' Start of', almanac.TWILIGHTS[twilight_type])
            # exclude all twilight, just full dark night
            # relies on start of night, twilight, day, etc being in order
            if twilight_type == 0: # start of night
                t_night_start = t
            elif not (t_night_start is None) and twilight_type == 1: # start of astro twilight after start of night
                t_night_end = t
                break
        result.append((t_night_start,t_night_end))
    return result

def run(location,t,target):
    """
    Assumes location is dict with "latitude", "longitude" keys in decimal degres, and "elevation" key in meters
    Assumes t is datetime obj
    Assumes target is astropy SkyCoord with ICRS RA and DE
    """

    planets = load("de421.bsp")
    earth = planets["earth"]
    moon = planets["moon"]

    # convert from astropy SkyCoord to skyfield "Star"
    target = Star(ra_hours=target.ra.hour,dec_degrees=target.dec.degree)

    loc = earth+Topos(location["latitude"],location["longitude"],elevation_m=location["elevation"])

    moon_app_pos = loc.at(t).observe(moon).apparent()

    app_pos = loc.at(t).observe(target).apparent()

    alt, _, _ = app_pos.altaz()
    alt = alt.degrees # convert from skyfield.units.Angle to float degrees


    moondiff = moon_app_pos.separation_from(app_pos).degrees

    return alt, moondiff

def run_moon(location,t):
    """
    Assumes location is dict with "latitude", "longitude" keys in decimal degres, and "elevation" key in meters
    Assumes t is datetime obj
    """

    planets = load("de421.bsp")
    earth = planets["earth"]
    sun = planets["sun"]
    moon = planets["moon"]

    loc = earth+Topos(location["latitude"],location["longitude"],elevation_m=location["elevation"])

    moon_app_pos = loc.at(t).observe(moon).apparent()

    alt, _, _ = moon_app_pos.altaz()
    alt = alt.degrees # convert from skyfield.units.Angle to float degrees

    _, slon, _ = earth.at(t).observe(sun).apparent().ecliptic_latlon()
    _, mlon, _ = earth.at(t).observe(moon).apparent().ecliptic_latlon()
    moon_phases = (mlon.degrees- slon.degrees) % 360.
    return alt, moon_phases

def plot(ax,t,alt,moondiff,name):
    if (alt < 0).all():
        ax.text(0.5,0.5,name+"\nNot\nVisible",transform=ax.transAxes,fontsize="x-large",ha="center",va="center")
    else:
        ax.plot(t,alt,"-b")
        if not (moondiff is None):
            ax.text(0.99,0.99,"Moon $\\measuredangle$ $\\geq${:.0f}$^\\circ$".format(moondiff.min()),fontsize="small",transform=ax.transAxes,ha="right",va="top")
        ax.axhline(45,ls="--",c="0.5")
    ax.set_ylim(0,90)

def main():
    import sys
    from matplotlib import pyplot as mpl
    import matplotlib
    from .lookuptarget import lookuptarget
    from .observabilityplot import ObservabilityPlot
    from .observabilitylegend import LegendForObservability
    import datetime
    import pytz
    
    import argparse
    parser = argparse.ArgumentParser(description="Makes graphs of the altitude (spherical coordinate) of an astronomical object versus time. Only shows astronomical night, i.e. when astronomical twilight ends to when it starts again. Local time is displayed on the x-axis for the following 5 nights. The minimum seperation of an object with the moon is displayed for each day. The lunar phase is displayed in degrees with 0 deg being new moon and 180 deg being full moon.")
    parser.add_argument("outFileNames",metavar="out",nargs=1,help="Output file name (e.g. report1.png)")
    parser.add_argument("objectNames",metavar="object",nargs='+',help='Object name (e.g. "M42" "Polaris" "Gam Cru" "Orion Nebula")')
    parser.add_argument("--minAltSun",type=float,default=-18.0,help="Minimum sun Alt to be considered day or twilight, in degrees (default: -18.0, astronomical twilight)")
    parser.add_argument("--bw",action="store_true",help="Black and white mode.")
    args = parser.parse_args()
    assert(len(args.outFileNames)>0)
    assert(len(args.objectNames)>0)
    
    locationDict = {
                    #32° 54' 11.91" North, 105° 31' 43.32" West
      "NMSkies" : {"latitude":32.903308333333335,"longitude":-106.96066666666667,"elevation":2225.,"tz":'US/Mountain'},
                    #38° 09' North, 002° 19' West
      "AstroCampSpain" : {"latitude":38.15,"longitude":-2.31,"elevation":1650,"tz":'Europe/Madrid'},
                    #31° 16' 24" South, 149° 03' 52" East
      "SidingSpringAustralia" : {"latitude":-31.273333333333333,"longitude":149.06444444444446,"elevation":1165,"tz":'Australia/Melbourne'},
      "RandomAntarctica"  : {"latitude":-75.320077, "longitude":-75.548212,"elevation":0,"tz":'UTC'},
    
    }
    
    nameList = args.objectNames
    coordList = [lookuptarget(x) for x in nameList]
    
    # Do from 4 PM to 8 AM for the next 5 days
    now = datetime.datetime.now()
    beginTimeFirstNight = datetime.datetime(now.year,now.month,now.day,hour=16)
    endTimeFirstNight = beginTimeFirstNight + datetime.timedelta(hours=16)
    ts = load.timescale()
    t_datetimes_nights_list = []
    for iDay in range(5):
        t_datetime = []
        beginTime = beginTimeFirstNight + datetime.timedelta(days=iDay)
        endTime = endTimeFirstNight + datetime.timedelta(days=iDay)
        currTime = beginTime
        while currTime < endTime:
            t_datetime.append(currTime)
            currTime += datetime.timedelta(minutes=15)
        t_datetimes_nights_list.append(t_datetime)

    for locName in locationDict:
        loc = locationDict[locName]
        tzLoc = pytz.timezone(loc["tz"])
        t_datetimes_nights_local_list = []
        t_ts_nights_local_list = []
        for iNight, t_datetimes in enumerate(t_datetimes_nights_list):
            t_datetimes_local = [tzLoc.localize(x) for x in t_datetimes]
            t_datetimes_nights_local_list.append(t_datetimes_local)
            t_ts_local = ts.from_datetimes(t_datetimes_local)
            t_ts_nights_local_list.append(t_ts_local)

        twilight_times = find_twilight(loc,t_ts_nights_local_list)
        fig, axes = mpl.subplots(
            figsize=(8.5,11),
            nrows=len(coordList)+1,ncols=len(t_datetimes_nights_list),
            sharex="col",sharey="row",
            gridspec_kw={
                "top":0.95,
                "bottom":0.05,
                "left":0.07,
                "right":0.98,
                "hspace":0,
                "wspace":0
            },
            squeeze=False,
            tight_layout=False,constrained_layout=False
        )
        for iCoord, name, coord in zip(range(len(nameList)),nameList, coordList):
            for iNight, t in enumerate(t_ts_nights_local_list):
                ax = axes[iCoord,iNight]
                alt, moondiff= run(loc,t,coord)
                plot(ax,t.astimezone(tzLoc),alt,moondiff,name)
                if iNight == 0:
                    ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(range(0,90,45)))
                    ax.yaxis.set_minor_locator(matplotlib.ticker.FixedLocator(range(0,90,15)))
                    ax.set_ylabel(name)
        # last row is the moon
        for iNight, (t, (night_start, night_end)) in enumerate(zip(t_ts_nights_local_list,twilight_times)):
            ax = axes[-1,iNight]
            moon_alt, moon_phases = run_moon(loc,t)
            plot(ax,t.astimezone(tzLoc),moon_alt,None,"Moon")
            if iNight == 0:
                ax.set_ylabel("Moon")
            ax.xaxis.set_major_formatter(DateFormatter("%Hh",tz=tzLoc))
            ax.xaxis.set_major_locator(HourLocator(range(0,24,3),tz=tzLoc))
            ax.xaxis.set_minor_locator(HourLocator(range(0,24,1),tz=tzLoc))
            ax.set_xlabel(t[0].astimezone(tzLoc).strftime("N of %a %b %d"))
            ax.set_xlim(night_start.astimezone(tzLoc),night_end.astimezone(tzLoc))
            ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(range(0,90,45)))
            ax.yaxis.set_minor_locator(matplotlib.ticker.FixedLocator(range(0,90,15)))
            #print(night_start.astimezone(tzLoc),night_end.astimezone(tzLoc))
            ax.text(0.99,0.99,"Phase: {:.0f}$^\\circ$".format(moon_phases.mean()),fontsize="small",transform=ax.transAxes,ha="right",va="top")
        fig.suptitle("Astronomical Object Altitude in $^\circ$ at "+locName)
        fig.savefig(args.outFileNames[0])
        break
        
