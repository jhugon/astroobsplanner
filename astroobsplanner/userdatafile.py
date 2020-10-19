#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import sys
import os
import os.path
import errno
import json

class UserDataFileBase(object):
  """
  Abstract Base Class
 
  Cross-platform user-specific data object
  Loads and Stores files in cross-platform locations.
  """
  def __init__(self,appName,dataFileName):
    """
    The data file will be <Platform-dependent path>/<appName>/<dataFileName>
    """
    # to help with cross-platform filenames
    appName = appName.lower()
    dataFileName = dataFileName.lower()
    # from http://stackoverflow.com/a/1088459/3242539
    appDataDir = None
    if sys.platform == 'darwin':
        from AppKit import NSSearchPathForDirectoriesInDomains
        appDataDir = os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], appName)
    elif sys.platform == 'win32':
        appDataDir = os.path.join(os.environ['APPDATA'], appName)
    else: #LINUX/UNIX Freedesktop Spec
        appDataBaseDir = os.getenv('XDG_DATA_HOME')
        if not appDataBaseDir or appDataBaseDir == '':
          appDataBaseDir = os.path.join(os.environ['HOME'], ".local/share")
        appDataDir = os.path.join(appDataBaseDir, appName)
    try:
        os.makedirs(appDataDir)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(appDataDir):
            pass
        else: raise
    self.appDataDir = appDataDir
    self.dataFileName = os.path.join(self.appDataDir,dataFileName)

  def getFileName(self):
    return self.dataFileName

class UserDataFileJson(UserDataFileBase):
  """
  Cross-platform user-specific data object
  Loads and Stores python dicts as json text files
  """
  def __init__(self,appName,dataFileName):
    """
    The data file will be <Platform-dependent path>/<appName>/<dataFileName>
    Don't put the extention on the second argument.
    """
    super(UserDataFileJson,self).__init__(appName,dataFileName)

  def readDict(self):
    try:
      with open(self.getFileName(),'r') as f:
        return json.load(f)
    except IOError as e:
      if e.errno == 2:
        return {}
      print("Error opening json file",e)
      sys.exit(1)

  def writeDict(self,obj):
    with open(self.getFileName(),'w') as f:
      json.dump(obj,f)

if __name__ == "__main__":

  uco = UserDataFileJson("astro-observability-test","locations.json")
  print(uco.getFileName())
  data = {'location1':[12521.125,125125.125,1256.5]}
  uco.writeDict(data)
  print(uco.readDict())
