#!/usr/bin/env python2
# vim: set fileencoding=utf-8

from .userdatafile import UserDataFileJson
import pytz

class LocationCache(object):
  def __init__(self):
    self.udfj = UserDataFileJson("astro-observability-planner","locations.json")

    if self.udfj.readDict() == {}:
        self.setDefaultLocations()
    
  def getLocNameList(self):
    return sorted(self.udfj.readDict().keys())

  def addLocEntry(self,name,lat,lon,elevation,tz):
    name = name.strip()
    if len(name)==0:
      raise LocationError("Location Name")
    try:
      lat = float(lat)
    except:
      raise LocationError("Latitude")
    try:
      lon = float(lon)
    except:
      raise LocationError("Longitude")
    try:
      elevation = float(elevation)
    except:
      raise LocationError("Elevation")
    try:
      tzTmp = tz.strip()
      #print "tzTmp: ",tzTmp
      if len(tz.strip())==0:
        raise
      tzTmp = pytz.timezone(tz)
    except Exception as e:
      print(e)
      raise LocationError("Time Zone")
    data = self.udfj.readDict()
    data[name] = {
                    'latitude':lat,
                    'longitude':lon,
                    'elevation':elevation,
                    'tz':tz,
                 }
    self.udfj.writeDict(data)

  def getLocEntry(self,name):
    return self.udfj.readDict()[name]

  def setDefaultLocations(self):

    data = {}
                #32° 54' 11.91" North, 105° 31' 43.32" West
    data["NM Skies"] = {
                      'latitude':  32.903308333333335,
                      'longitude': -106.96066666666667,
                      'elevation': 2225.,
                      'tz':        'US/Mountain',
                       }
                #38° 09' North, 002° 19' West
    data["Astro Camp Spain"] = {
                      'latitude':  38.15,
                      'longitude': -2.31,
                      'elevation': 1650,
                      'tz':        'Europe/Madrid',
                           }
                #31° 16' 24" South, 149° 03' 52" East
    data["Siding Spring Australia"] = {
                      'latitude':  -31.273333333333333,
                      'longitude': 149.06444444444446,
                      'elevation': 1165,
                      'tz':        'Australia/Melbourne',
                           }
    self.udfj.writeDict(data)

class LocationError(Exception):
  def __init__(self,field):
    self.field = field
  def __str__(self):
    return "LocationError: Couldn't parse "+str(self.field)
  def getField(self):
    return self.field
