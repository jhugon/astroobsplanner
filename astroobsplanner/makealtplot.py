#!/usr/bin/env python2
# vim: set fileencoding=utf-8

from skyfield.api import load, Topos
from skyfield.starlib import Star
from matplotlib.dates import HourLocator, DateFormatter

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
    moon = planets["moon"]

    loc = earth+Topos(location["latitude"],location["longitude"],elevation_m=location["elevation"])

    moon_app_pos = loc.at(t).observe(moon).apparent()

    alt, _, _ = moon_app_pos.altaz()
    alt = alt.degrees # convert from skyfield.units.Angle to float degrees

    return alt

def plot(ax,t,alt,moondiff,name):
    if (alt < 0).all():
        ax.text(0.5,0.5,name+"\nNot\nVisible",transform=ax.transAxes,fontsize="x-large",ha="center",va="center")
    else:
        ax.plot(t,alt,"-b")
        if not (moondiff is None):
            ax.plot(t,moondiff/2.,":r")
        ax.axhline(45,ls="--",c="0.5")
    ax.set_ylim(0,90)

def main():
    import sys
    from matplotlib import pyplot as mpl
    from .lookuptarget import lookuptarget
    from .observabilityplot import ObservabilityPlot
    from .observabilitylegend import LegendForObservability
    import datetime
    import pytz
    
    import argparse
    parser = argparse.ArgumentParser(description="Makes graphs of the altitude (spherical coordinate) of an object versus time.")
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
        fig, axes = mpl.subplots(
            figsize=(8.5,11),
            nrows=len(coordList)+1,ncols=len(t_datetimes_nights_list),
            sharex="col",sharey="row",
            gridspec_kw={"hspace":0,"wspace":0},
            squeeze=False,constrained_layout=False
        )
        for iCoord, name, coord in zip(range(len(nameList)),nameList, coordList):
            for iNight, t_datetimes in enumerate(t_datetimes_nights_list):
                ax = axes[iCoord,iNight]
                t_datetimes_local = [tzLoc.localize(x) for x in t_datetimes_nights_list[iNight]]
                t = ts.from_datetimes(t_datetimes_local)
                alt, moondiff= run(loc,t,coord)
                plot(ax,t_datetimes_local,alt,moondiff,name)
                if iNight == 0:
                    ax.set_ylabel(name+" Alt [$^\circ$]")
        # last row is the moon
        for iNight, t_datetimes in enumerate(t_datetimes_nights_list):
            ax = axes[-1,iNight]
            t_datetimes_local = [tzLoc.localize(x) for x in t_datetimes_nights_list[iNight]]
            t = ts.from_datetimes(t_datetimes_local)
            moon_alt = run_moon(loc,t)
            plot(ax,t_datetimes_local,moon_alt,None,"Moon")
            if iNight == 0:
                ax.set_ylabel("Moon Alt [$^\circ$]")
            ax.xaxis.set_major_formatter(DateFormatter("%Hh",tz=tzLoc))
            ax.xaxis.set_major_locator(HourLocator(range(0,24,6),tz=tzLoc))
            ax.xaxis.set_minor_locator(HourLocator(range(0,24,2),tz=tzLoc))
            ax.set_xlabel(t_datetimes_local[0].strftime("N of %a %b %d"))
        fig.suptitle(locName+" (Moondiff is /2)")
        fig.savefig(args.outFileNames[0])
        break
        
