import sys
import csv
import ephem
from astropy.coordinates import get_icrs_coordinates, SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
from .userdatafile import UserDataFileBase

def lookuptarget(name):
  """
    Wraps get_icrs_coordinates, but caches values 
    in .coordCache.txt to reduce internet lookups.
    Returns astropy SkyCoord
  """
  result = None
  filename = UserDataFileBase("astro-observability-planner","targetcoordcache.txt").getFileName()
  with open(filename,"a+") as coordCacheFile:
    coordCacheReader = csv.reader(coordCacheFile, dialect='excel')
    for entry in coordCacheReader:
      if name.lower() == entry[0]:
        result = SkyCoord(entry[1])
        #print "Found cache entry for "+name
    if not result:
      #print "Didn't Found cache entry for "+name
      result = get_icrs_coordinates(name)
      #print "Looked up entry for "+name+" and writing to cache"
      coordCacheWriter = csv.writer(coordCacheFile, dialect='excel')
      coordCacheWriter.writerow([name.lower(),result.to_string("hmsdms")])
  return result

def skycoordtoephemStr(coord,name="name"):
  # "name,f,h:m:s,d:m:s,mag,epoch_year"
  newcoord = coord
  if coord.name != "icrs":
    newcoord = coord.transform_to('icrs')
  result = name+",f,"
  result += newcoord.to_string("hmsdms",sep=":").replace(' ',',')
  result += ",-1,2000"
  return result

def lookuptargetxephem(name):
  stripLowName = name.strip().lower()
  if stripLowName == "mercury":
    return ephem.Mercury()
  elif stripLowName == "venus":
    return ephem.Venus()
  elif stripLowName == "mars":
    return ephem.Mars()
  elif stripLowName == "jupiter":
    return ephem.Jupiter()
  elif stripLowName == "saturn":
    return ephem.Saturn()
  elif stripLowName == "neptune":
    return ephem.Neptune()
  elif stripLowName == "uranus":
    return ephem.Uranus()
  elif stripLowName == "pluto":
    return ephem.Pluto()
  else:
    return ephem.readdb(skycoordtoephemStr(lookuptarget(name)))
