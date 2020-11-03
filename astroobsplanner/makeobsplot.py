#!/usr/bin/env python2
# vim: set fileencoding=utf-8

def main():
    from matplotlib import pyplot as mpl
    from .lookuptarget import lookuptargetxephem
    from .observabilityplot import ObservabilityPlot
    from .observabilitylegend import LegendForObservability
    import datetime
    
    import argparse
    parser = argparse.ArgumentParser(description="Creates an observability report of the objects listed as arguments.")
    parser.add_argument("outFileNames",metavar="out",nargs=1,help="Output file name (e.g. report1.png)")
    parser.add_argument("objectNames",metavar="object",nargs='+',help='Object name (e.g. "M42" "Polaris" "Gam Cru" "Orion Nebula")')
    parser.add_argument("--minAlt",type=float,default=45.0,help="Minimum object Alt to be considered observable, in degrees (default: 45.0)")
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
    
    colors = ['b','g','r','c','m']
    colors *= 10
    hatches = None
    if args.bw:
      #hatches = ['/','\\','|','-','+','x','o','O','.','*']
      hatches = ['///','\\\\\\','||','--','O','.']
      hatches *= 10
    nameList = args.objectNames
    
    thisyear = datetime.date.today().year
    beginDate = datetime.date(thisyear,1,1)
    endDate = datetime.date(thisyear,12,21)

    coordList = [lookuptargetxephem(x) for x in nameList]
    fig, ((ax1, ax2), (ax3, ax4)) = mpl.subplots(figsize=(11,8.5),nrows=2, ncols=2)
    op1 = ObservabilityPlot(locationDict["NMSkies"],coordList,beginDate,endDate,minAlt=args.minAlt,minAltSun=args.minAltSun)
    op1.plot(ax1,"NM Skies Observatory",colorList=colors,hatchList=hatches)
    op2 = ObservabilityPlot(locationDict["AstroCampSpain"],coordList,beginDate,endDate,minAlt=args.minAlt,minAltSun=args.minAltSun)
    op2.plot(ax2,"Astro Camp Observatory, Spain",colorList=colors,hatchList=hatches)
    op3 = ObservabilityPlot(locationDict["SidingSpringAustralia"],coordList,beginDate,endDate,minAlt=args.minAlt,minAltSun=args.minAltSun)
    op3.plot(ax3,"Siding Spring Observatory, Australia",colorList=colors,hatchList=hatches)
    
    colorsToShow = colors[:len(coordList)]
    hatchesToShow = None
    if hatches:
      hatchesToShow = hatches[:len(coordList)]
    lfo = LegendForObservability(ax4,colorsToShow,nameList,op1,hatchList=hatchesToShow)
    
    mpl.tight_layout()
    fig.savefig(args.outFileNames[0])
