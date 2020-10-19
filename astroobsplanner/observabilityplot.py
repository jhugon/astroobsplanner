#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import sys
import datetime
import pytz
import numpy
from matplotlib import pyplot as mpl
import matplotlib.colors
import matplotlib.cm
import ephem

class ObservabilityPlot(object):
  def __init__(self,location,ephemCoordList,beginDate,endDate,minAlt=45.,minAltSun=-18.,minAltMoon=-5.,samplingPeriodDays=7):
    self.location = location
    self.beginDate = beginDate
    self.endDate = endDate
    self.minAlt = minAlt
    self.minAltSun = minAltSun
    self.ephemCoordList = ephemCoordList
    self.initObserver()
    self.tz = pytz.timezone(self.location['tz'])
    self.initDateArrays(samplingPeriodDays)

    self.sunData = [self.getRiseSetTransit(ephem.Sun(),day,minAltSun) for day in self.datesEphem]
    self.moonData = [self.getRiseSetTransit(ephem.Moon(),day,minAltMoon) for day in self.datesEphem]

    self.data = []
    for coord in self.ephemCoordList:
      coordData = [self.getRiseSetTransit(coord,day,minAlt) for day in self.datesEphem]
      self.data.append(coordData)

    self.shiftAllTimes()

  def shiftAllTimes(self,shift=12.):
    for iDate in range(len(self.dates)):
      point = self.sunData[iDate]
      p0 = point[0]
      p1 = point[1]
      p2 = point[2]
      if type(p0) != bool:
        p0 += shift
        if p0 > 24.:
          p0 -=24.
      if type(p1) != bool:
        p1 += shift
        if p1 > 24.:
          p1 -=24.
      p2 += shift
      if p2 > 24.:
        p2 -=24.
      self.sunData[iDate] = (p0,p1,p2)

      for iCoord in range(len(self.data)):
        point = self.data[iCoord][iDate]
        p0 = point[0]
        p1 = point[1]
        p2 = point[2]
        if type(p0) != bool:
          p0 += shift
          if p0 > 24.:
            p0 -=24.
        if type(p1) != bool:
          p1 += shift
          if p1 > 24.:
            p1 -=24.
        p2 += shift
        if p2 > 24.:
          p2 -=24.
        self.data[iCoord][iDate] = (p0,p1,p2)

      point = self.moonData[iDate]
      p0 = point[0]
      p1 = point[1]
      p2 = point[2]
      if type(p0) != bool:
        p0 += shift
        if p0 > 24.:
          p0 -=24.
      if type(p1) != bool:
        p1 += shift
        if p1 > 24.:
          p1 -=24.
      p2 += shift
      if p2 > 24.:
        p2 -=24.
      self.moonData[iDate] = (p0,p1,p2)

  def initObserver(self):
    observer = ephem.Observer()
    observer.lat = str(self.location['latitude'])
    observer.lon = str(self.location['longitude'])
    observer.elev = self.location['elevation']
    observer.compute_pressure()
    self.observer = observer

  def skyCoordToXEphemStr(self,coord,name="name"):
    # "name,f,h:m:s,d:m:s,mag,epoch_year"
    newcoord = coord
    if coord.name != "icrs":
      newcoord = coord.transform_to('icrs')
    result = name+",f,"
    result += newcoord.to_string("hmsdms",sep=":").replace(' ',',')
    result += ",-1,2000"
    return result

  def initDateArrays(self,daySpacing=7):
    firstDay = float(ephem.Date(self.beginDate))
    lastDay = float(ephem.Date(self.endDate))
    thisDay = firstDay
    days = []
    while thisDay <= lastDay:
        days.append(thisDay)
        thisDay += daySpacing
    days = [ephem.Date(x) for x in days]
    self.datesEphem = days
    self.dates = [self.convertEphemToLocalDate(x) for x in days]

  def getRiseSetTransit(self,coord,refDate,horizon):
    """
        horizon is the alt to consider viewable. It should be in integer degrees
        returns tuple of rise,set,transit times in local decimal hour of the day (0-24)
    """
    self.observer.date = refDate
    self.observer.horizon = str(int(horizon))
    coord.compute(self.observer)
    transitTime = self.observer.next_transit(coord)
    #print transitTime, coord.circumpolar,coord.neverup
    transitTimeHours = self.convertEphemToLocalDecimalHours(transitTime)
    if coord.circumpolar:
      return (True,True,transitTimeHours)
    if coord.neverup:
      return (False,False,transitTimeHours)
    riseTime = self.observer.next_rising(coord)
    setTime = self.observer.next_setting(coord)
    riseTimeHours = self.convertEphemToLocalDecimalHours(riseTime)
    setTimeHours = self.convertEphemToLocalDecimalHours(setTime)
    return (riseTimeHours,setTimeHours,transitTimeHours)

  def convertEphemToLocalDecimalHours(self,timeEphem):
    timeTuple = ephem.Date(timeEphem).tuple()
    timeUTC = datetime.datetime(*[int(x) for x in timeTuple],tzinfo=pytz.utc)
    timeLocal = timeUTC.astimezone(self.tz)
    time0 = timeLocal.replace(hour=0,minute=0,second=0,microsecond=0)
    timeDelta = timeLocal-time0
    result = timeDelta.total_seconds()/3600.
    return result

  def convertEphemToLocalDate(self,timeEphem):
    timeTuple = ephem.Date(timeEphem).tuple()
    timeUTC = datetime.datetime(*[int(x) for x in timeTuple],tzinfo=pytz.utc)
    timeLocal = timeUTC.astimezone(self.tz)
    return timeLocal.date()

  def getMoonIllumination(self,dt):
    """
    Input datetime object (in UTC), and uses ephem and interpolation
    to get fraction of moon illuminated.  Returns float in [0,1]
  
    Usually absolute accuracy 10%, sometimes up to 20%
    """
    dtEphem = ephem.Date(dt)
    nextFull = ephem.next_full_moon(dt)
    followingNew = ephem.next_new_moon(nextFull)
    period = 2.*(followingNew-nextFull)
    #print "dtEphem: {:f}".format(dtEphem)
    #print "nextFull: {:f}".format(nextFull)
    #print "followingNew: {:f}".format(followingNew)
    #print "period {:f}".format(period)
    return 0.5*numpy.cos(2*numpy.pi*(dtEphem-nextFull)/period)+0.5

  def plot(self,outfilename,title=None,labels=None,show_all_times=False,colorList = ['b','g','r','c','m'],sunColor='y',showMoon=False,hatchList=None,sunHatch=None):
    """
      outfilename should either be a string file name to create
      or an axes instances to be used for plotting
    """
    if labels:
      if len(labels)!=len(self.data):
        print("Error: ObservabilityPlot.plot: Length of labels arg must match length of coordinates. exiting.")
        sys.exit(1)

    fig, ax = None, None
    if type(outfilename) == str:
      fig, ax = mpl.subplots()
      fig.autofmt_xdate()
    else:
      ax = outfilename
    if title: ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Local Time")
    if show_all_times:
      ax.set_ylim(0,24)
      ax.set_yticks(list(range(0,25,3)))
      ax.set_yticklabels(["{0:02d}:00".format(x % 24) for x in range(12,37,3)])
    else:
      ax.set_ylim(4,20)
      ax.set_yticks(list(range(6,19,3)))
      ax.set_yticklabels(["{0:02d}:00".format(x % 24) for x in range(18,33,3)])

    for icoord, coorddata in enumerate(self.data):
      dateSets, riseSets, setSets = self.createDataSubsets(self.dates,coorddata)
      for tmpDates, tmpRises, tmpSets in zip(dateSets, riseSets, setSets):
        if hatchList:
          ax.fill_between(tmpDates,tmpRises,tmpSets,hatch=hatchList[icoord % len(hatchList)],
                            lw=0,
                            facecolor=matplotlib.colors.colorConverter.to_rgba('k',alpha=0.),
                            edgecolor=matplotlib.colors.colorConverter.to_rgba('k',alpha=1.)
                         )
        else:
          ax.fill_between(tmpDates,tmpRises,tmpSets,color=colorList[icoord % len(colorList)],alpha=0.5)

    if showMoon:
      dateSets, riseSets, setSets, ephemDateSets = self.createDataSubsets(self.dates,self.moonData,self.datesEphem)
      for tmpDates, tmpRises, tmpSets, tmpEphemDates in zip(dateSets, riseSets, setSets, ephemDateSets):
        illumFrac = [self.getMoonIllumination(dt) for dt in tmpEphemDates]
        illumFracColors = matplotlib.cm.binary(illumFrac) # illumFrac already normalized in [0,1]
        ax.vlines(tmpDates,tmpRises,tmpSets,colors=illumFracColors,lw=2)

    if hatchList:
      ax.fill_between(self.dates,0,[x[1] for x in self.sunData],color='0.5',hatch=sunHatch)
      ax.fill_between(self.dates,[x[0] for x in self.sunData],24,color='0.5',hatch=sunHatch)
    else:
      ax.fill_between(self.dates,0,[x[1] for x in self.sunData],color=sunColor)
      ax.fill_between(self.dates,[x[0] for x in self.sunData],24,color=sunColor)

    for label in ax.get_xticklabels():
      label.set_ha("right")
      label.set_rotation(30)

    ax.set_xlim(self.dates[0],self.dates[-1])

    if type(outfilename) == str:
      fig.savefig(outfilename)

  def createDataSubsets(self,dates,dataPoints,ephemDates=None):
    """
    If you also put in ephemDates, will return 
        dateSets, riseSets, setSets, ephemDateSets
    """
    lastPoint = dataPoints[-1]
    dateSets = [[]]
    riseSets = [[]]
    setSets = [[]]
    ephemDateSets = [[]]
    zipTuples = None
    if ephemDates:
      zipTuples = list(zip(dates,dataPoints,ephemDates))
    else:
      zipTuples = list(zip(dates,dataPoints))
    for tup in zipTuples:
      point = None
      day = None
      ephemDay = None
      if ephemDates:
        day, point, ephemDay = tup
      else:
        day, point = tup
      #print point[0],point[1]
      if type(point[0]) == bool and point[0] == False:
        continue
      if type(point[0]) == bool and point[0] == True:
        dateSets[-1].append(day)
        riseSets[-1].append(0.)
        setSets[-1].append(24.)
        if ephemDates:
          ephemDateSets[-1].append(ephemDay)
        continue
      riseChange = point[0] - lastPoint[0]
      setChange = point[1] - lastPoint[1]
      if abs(riseChange) > 10.:
        dateSets.append([])
        riseSets.append([])
        setSets.append([])
        if ephemDates:
          ephemDateSets.append([])
      if point[0] < point[1]: # rises before sets (normal)
        dateSets[-1].append(day)
        riseSets[-1].append(point[0])
        setSets[-1].append(point[1])
        if ephemDates:
          ephemDateSets[-1].append(ephemDay)
      else: # sets before rises (flipped)
        if len(dateSets)>1:
          dateSets[-2].append(day)
          riseSets[-2].append(0.)
          setSets[-2].append(point[1])
          if ephemDates:
            ephemDateSets[-2].append(ephemDay)
        dateSets[-1].append(day)
        riseSets[-1].append(point[0])
        setSets[-1].append(24.)
        if ephemDates:
          ephemDateSets[-1].append(ephemDay)
      #print point[0],point[1],riseChange,setChange
      lastPoint = point
    if ephemDates:
      return dateSets, riseSets, setSets, ephemDateSets
    else:
      return dateSets, riseSets, setSets

