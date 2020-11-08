import sys
import csv
import time
import ephem

from astropy.coordinates import get_icrs_coordinates, SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
from astroquery.simbad import Simbad

from .userdatafile import UserDataFileBase

CALDWELL_MAP = {
  "caldwell 1": "ngc188",
  "caldwell 2": "ngc40",
  "caldwell 3": "ngc4236",
  "caldwell 4": "ngc7023",
  "caldwell 5": "ic342",
  "caldwell 6": "ngc6543",
  "caldwell 7": "ngc2403",
  "caldwell 8": "ngc559",
  "caldwell 9": "sh2-155",
  "caldwell 10": "ngc663",
  "caldwell 11": "ngc7635",
  "caldwell 12": "ngc6946",
  "caldwell 13": "ngc457",
  "caldwell 14": "ngc869",
  "caldwell 15": "ngc6826",
  "caldwell 16": "ngc7243",
  "caldwell 17": "ngc147",
  "caldwell 18": "ngc185",
  "caldwell 19": "ic5146",
  "caldwell 20": "ngc7000",
  "caldwell 21": "ngc4449",
  "caldwell 22": "ngc7662",
  "caldwell 23": "ngc891",
  "caldwell 24": "ngc1275",
  "caldwell 25": "ngc2419",
  "caldwell 26": "ngc4244",
  "caldwell 27": "ngc6888",
  "caldwell 28": "ngc752",
  "caldwell 29": "ngc5005",
  "caldwell 30": "ngc7331",
  "caldwell 31": "ic405",
  "caldwell 32": "ngc4631",
  "caldwell 33": "ngc6992",
  "caldwell 34": "ngc6960",
  "caldwell 35": "ngc4889",
  "caldwell 36": "ngc4559",
  "caldwell 37": "ngc6885",
  "caldwell 38": "ngc4565",
  "caldwell 39": "ngc2392",
  "caldwell 40": "ngc3626",
  "caldwell 41": "mel 25",
  "caldwell 42": "ngc7006",
  "caldwell 43": "ngc7814",
  "caldwell 44": "ngc7479",
  "caldwell 45": "ngc5248",
  "caldwell 46": "ngc2261",
  "caldwell 47": "ngc6934",
  "caldwell 48": "ngc2775",
  "caldwell 49": "ngc2237",
  "caldwell 50": "ngc2244",
  "caldwell 51": "ic1613",
  "caldwell 52": "ngc4697",
  "caldwell 53": "ngc3115",
  "caldwell 54": "ngc2506",
  "caldwell 55": "ngc7009",
  "caldwell 56": "ngc246",
  "caldwell 57": "ngc6822",
  "caldwell 58": "ngc2360",
  "caldwell 59": "ngc3242",
  "caldwell 60": "ngc4038",
  "caldwell 61": "ngc4039",
  "caldwell 62": "ngc247",
  "caldwell 63": "ngc7293",
  "caldwell 64": "ngc2362",
  "caldwell 65": "ngc253",
  "caldwell 66": "ngc5694",
  "caldwell 67": "ngc1097",
  "caldwell 68": "ngc6729",
  "caldwell 69": "ngc6302",
  "caldwell 70": "ngc300",
  "caldwell 71": "ngc2477",
  "caldwell 72": "ngc55",
  "caldwell 73": "ngc1851",
  "caldwell 74": "ngc3132",
  "caldwell 75": "ngc6124",
  "caldwell 76": "ngc6231",
  "caldwell 77": "ngc5128",
  "caldwell 78": "ngc6541",
  "caldwell 79": "ngc3201",
  "caldwell 80": "ngc5139",
  "caldwell 81": "ngc6352",
  "caldwell 82": "ngc6193",
  "caldwell 83": "ngc4945",
  "caldwell 84": "ngc5286",
  "caldwell 85": "ic2391",
  "caldwell 86": "ngc6397",
  "caldwell 87": "ngc1261",
  "caldwell 88": "ngc5823",
  "caldwell 89": "ngc6067",
  "caldwell 90": "ngc2867",
  "caldwell 91": "ngc3532",
  "caldwell 92": "ngc3372",
  "caldwell 93": "ngc6752",
  "caldwell 94": "ngc4755",
  "caldwell 95": "ngc6025",
  "caldwell 96": "ngc2516",
  "caldwell 97": "ngc3766",
  "caldwell 98": "ngc4609",
  "caldwell 99": "coalsack",
  "caldwell 100": "ic2944",
  "caldwell 101": "ngc6744",
  "caldwell 102": "ic2602",
  "caldwell 103": "ngc2070",
  "caldwell 104": "ngc362",
  "caldwell 105": "ngc4833",
  "caldwell 106": "ngc104",
  "caldwell 107": "ngc6101",
  "caldwell 108": "ngc4372",
  "caldwell 109": "ngc3195",
  "c1": "ngc188",
  "c2": "ngc40",
  "c3": "ngc4236",
  "c4": "ngc7023",
  "c5": "ic342",
  "c6": "ngc6543",
  "c7": "ngc2403",
  "c8": "ngc559",
  "c9": "sh2-155",
  "c10": "ngc663",
  "c11": "ngc7635",
  "c12": "ngc6946",
  "c13": "ngc457",
  "c14": "ngc869",
  "c15": "ngc6826",
  "c16": "ngc7243",
  "c17": "ngc147",
  "c18": "ngc185",
  "c19": "ic5146",
  "c20": "ngc7000",
  "c21": "ngc4449",
  "c22": "ngc7662",
  "c23": "ngc891",
  "c24": "ngc1275",
  "c25": "ngc2419",
  "c26": "ngc4244",
  "c27": "ngc6888",
  "c28": "ngc752",
  "c29": "ngc5005",
  "c30": "ngc7331",
  "c31": "ic405",
  "c32": "ngc4631",
  "c33": "ngc6992",
  "c34": "ngc6960",
  "c35": "ngc4889",
  "c36": "ngc4559",
  "c37": "ngc6885",
  "c38": "ngc4565",
  "c39": "ngc2392",
  "c40": "ngc3626",
  "c41": "mel 25",
  "c42": "ngc7006",
  "c43": "ngc7814",
  "c44": "ngc7479",
  "c45": "ngc5248",
  "c46": "ngc2261",
  "c47": "ngc6934",
  "c48": "ngc2775",
  "c49": "ngc2237",
  "c50": "ngc2244",
  "c51": "ic1613",
  "c52": "ngc4697",
  "c53": "ngc3115",
  "c54": "ngc2506",
  "c55": "ngc7009",
  "c56": "ngc246",
  "c57": "ngc6822",
  "c58": "ngc2360",
  "c59": "ngc3242",
  "c60": "ngc4038",
  "c61": "ngc4039",
  "c62": "ngc247",
  "c63": "ngc7293",
  "c64": "ngc2362",
  "c65": "ngc253",
  "c66": "ngc5694",
  "c67": "ngc1097",
  "c68": "ngc6729",
  "c69": "ngc6302",
  "c70": "ngc300",
  "c71": "ngc2477",
  "c72": "ngc55",
  "c73": "ngc1851",
  "c74": "ngc3132",
  "c75": "ngc6124",
  "c76": "ngc6231",
  "c77": "ngc5128",
  "c78": "ngc6541",
  "c79": "ngc3201",
  "c80": "ngc5139",
  "c81": "ngc6352",
  "c82": "ngc6193",
  "c83": "ngc4945",
  "c84": "ngc5286",
  "c85": "ic2391",
  "c86": "ngc6397",
  "c87": "ngc1261",
  "c88": "ngc5823",
  "c89": "ngc6067",
  "c90": "ngc2867",
  "c91": "ngc3532",
  "c92": "ngc3372",
  "c93": "ngc6752",
  "c94": "ngc4755",
  "c95": "ngc6025",
  "c96": "ngc2516",
  "c97": "ngc3766",
  "c98": "ngc4609",
  "c99": "coalsack",
  "c100": "ic2944",
  "c101": "ngc6744",
  "c102": "ic2602",
  "c103": "ngc2070",
  "c104": "ngc362",
  "c105": "ngc4833",
  "c106": "ngc104",
  "c107": "ngc6101",
  "c108": "ngc4372",
  "c109": "ngc3195",
}

def lookuptarget(name):
  """
    Wraps get_icrs_coordinates, but caches values 
    in .coordCache.txt to reduce internet lookups.
    Returns astropy SkyCoord
  """
  result = None
  filename = UserDataFileBase("astro-observability-planner","targetcoordcache.txt").getFileName()
  with open(filename,"a+") as coordCacheFile:
    coordCacheFile.seek(0)
    coordCacheReader = csv.reader(coordCacheFile, dialect='excel')
    for entry in coordCacheReader:
      if name.lower() == entry[0]:
        result = SkyCoord(entry[1])
    if not result:
      try:
        mapname = CALDWELL_MAP[name.lower()]
        result = get_icrs_coordinates(mapname)
      except KeyError:
        result = get_icrs_coordinates(name)
      finally:
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

def lookuptargettype(name):
  """
    Looks up target otype from SIMBAD
    returns list of types, with main type first
  """
  main_type = None
  extra_types = None
  filename = UserDataFileBase("astro-observability-planner","targettypecache.txt").getFileName()
  mysimbad = Simbad()
  mysimbad.remove_votable_fields('coordinates')
  mysimbad.add_votable_fields("otype","otypes")
  with open(filename,"a+") as typeCacheFile:
    typeCacheFile.seek(0)
    typeCacheReader = csv.reader(typeCacheFile, dialect='excel')
    for entry in typeCacheReader:
      if name.lower() == entry[0]:
        main_type = entry[1]
        extra_types = entry[2]
    if not main_type:
      try:
        lookupname = CALDWELL_MAP[name.lower()]
      except KeyError:
        lookupname = name
      finally:
        time.sleep(0.05)
        result_table = mysimbad.query_object(lookupname)
        main_type = result_table["OTYPE"][0].decode()
        extra_types = result_table["OTYPES"][0].decode()
        typeCacheWriter = csv.writer(typeCacheFile, dialect='excel')
        typeCacheWriter.writerow([name.lower(),main_type,extra_types])
        if lookupname != name:
            typeCacheWriter.writerow([lookupname.lower(),main_type,extra_types])
  result = [main_type] + extra_types.split("|")
  return result
