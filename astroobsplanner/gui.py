#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.gridspec
from .mplsetup import *

from tkinter import *
import tkinter.filedialog
import tkinter.ttk

from .locationcache import LocationCache, LocationError
from .lookuptarget import lookuptargetxephem, NameResolveError
from .observabilityplot import ObservabilityPlot
from .observabilitylegend import LegendForObservability

class Gui(object):

    def __init__(self, master):

        self.master = master

        self.menu = Menu(master)
        self.master.config(menu=self.menu)
        self.fileMenu = Menu(self.menu)
        self.menu.add_cascade(label="File",menu=self.fileMenu)

        self.fileMenu.add_command(label="Save",command=self.saveFile)
        self.fileMenu.add_command(label="Save As",command=self.saveFileAs)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Exit",command=self.master.destroy)

        self.fileMenu.entryconfig("Save",state="disabled")

        self.configFrame = Frame(master,bd=2,relief=RAISED,padx=5,pady=5)
        self.configFrame.pack(side=LEFT,fill=Y)

        self.plotFrame = Frame(master)
        self.plotFrame.pack(side=LEFT)

        self.runButton = Button(self.configFrame, text="Run", command=self.run)
        self.runButton.pack()

        self.locationConfigFrame = Frame(self.configFrame)
        self.locationConfigFrame.pack()
        self.locationEntryFrame = Frame(self.locationConfigFrame)
        self.locationEntryFrame.pack(side=LEFT)
        self.addLocationFrame = Frame(self.locationConfigFrame)
        self.addLocationFrame.pack(side=LEFT)
        self.addLocationVar = StringVar()
        self.addLocationVar.set("More Locations")
        self.addLocationButton = Button(self.addLocationFrame, width = 14,
                                        textvar = self.addLocationVar, 
                                        command=self.onAddLocation
                                       )
        self.addLocationButton.pack()

        self.locationConfigs=[]
        self.locationConfigs.append(LocationConfig(self))

        self.targetsLabel = Label(self.configFrame, text="List of Targets:")
        self.targetsLabel.pack()

        self.targetConfigFrame = Frame(self.configFrame)
        self.targetConfigFrame.pack()

        self.targetConfigs=[]
        self.targetConfigs.append(TargetConfig(self))

        self.miscConfigFrame = Frame(self.configFrame)
        self.miscConfigFrame.pack(side=BOTTOM)

        self.beginDateConfigFrame = Frame(self.miscConfigFrame)
        self.beginDateConfigFrame.pack()
        self.beginDateLabel = Label(self.beginDateConfigFrame,text="Begin Date:")
        self.beginDateLabel.pack()
        self.beginYearEntry = tkinter.ttk.Combobox(self.beginDateConfigFrame,width=4)
        self.beginYearEntry.pack(side=LEFT)
        self.beginMonthEntry = tkinter.ttk.Combobox(self.beginDateConfigFrame,width=2)
        self.beginMonthEntry.pack(side=LEFT)
        self.beginDayEntry = tkinter.ttk.Combobox(self.beginDateConfigFrame,width=2)
        self.beginDayEntry.pack(side=LEFT)
        thisYear = datetime.date.today().year
        self.beginYearEntry['values'] = list(range(thisYear,thisYear+11))
        self.beginMonthEntry['values'] = list(range(1,13))
        self.beginDayEntry['values'] = list(range(1,32))
        self.beginYearEntry.current(0)
        self.beginMonthEntry.current(0)
        self.beginDayEntry.current(0)
        self.beginDateStatusVar = StringVar()
        self.beginDateStatusLabel = Label(self.beginDateConfigFrame,width=3,textvariable=self.beginDateStatusVar,fg="red")
        self.beginDateStatusLabel.pack(side=LEFT)

        self.endDateConfigFrame = Frame(self.miscConfigFrame)
        self.endDateConfigFrame.pack()
        self.endDateLabel = Label(self.endDateConfigFrame,text="Begin Date:")
        self.endDateLabel.pack()
        self.endYearEntry = tkinter.ttk.Combobox(self.endDateConfigFrame,width=4)
        self.endYearEntry.pack(side=LEFT)
        self.endMonthEntry = tkinter.ttk.Combobox(self.endDateConfigFrame,width=2)
        self.endMonthEntry.pack(side=LEFT)
        self.endDayEntry = tkinter.ttk.Combobox(self.endDateConfigFrame,width=2)
        self.endDayEntry.pack(side=LEFT)
        thisYear = datetime.date.today().year
        self.endYearEntry['values'] = list(range(thisYear,thisYear+11))
        self.endMonthEntry['values'] = list(range(1,13))
        self.endDayEntry['values'] = list(range(1,32))
        self.endYearEntry.current(0)
        self.endMonthEntry.current(11)
        self.endDayEntry.current(30)
        self.endDateStatusVar = StringVar()
        self.endDateStatusLabel = Label(self.endDateConfigFrame,width=3,textvariable=self.endDateStatusVar,fg="red")
        self.endDateStatusLabel.pack(side=LEFT)

        self.samplingPeriodLabel = Label(self.miscConfigFrame,text="Sampling Period (Days):")
        self.samplingPeriodLabel.pack()
        self.samplingPeriodEntry = Spinbox(self.miscConfigFrame,from_=1,to=90,increment=1)
        self.samplingPeriodEntry.pack()
        self.samplingPeriodEntry.delete(0,"end")
        self.samplingPeriodEntry.insert(0,"7")
        self.minAltLabel = Label(self.miscConfigFrame,text="Minimum Alt:")
        self.minAltLabel.pack()
        self.minAltEntry = Spinbox(self.miscConfigFrame,from_=-90,to=90,increment=1)
        self.minAltEntry.pack()
        self.minAltSunLabel = Label(self.miscConfigFrame,text="Sun Minimum Alt:")
        self.minAltSunLabel.pack()
        self.minAltSunEntry = Spinbox(self.miscConfigFrame,from_=-90,to=90,increment=1)
        self.minAltSunEntry.pack()
        self.minAltEntry.delete(0,"end")
        self.minAltSunEntry.delete(0,"end")
        self.minAltEntry.insert(0,"45")
        self.minAltSunEntry.insert(0,"-18")
        self.moonConfigFrame = Frame(self.miscConfigFrame)
        self.moonConfigFrame.pack()
        self.moonConfigActiveFrame = Frame(self.moonConfigFrame)
        self.moonConfigActiveFrame.pack(side=LEFT)
        self.moonConfigAltFrame = Frame(self.moonConfigFrame)
        self.moonConfigAltFrame.pack(side=LEFT)
        self.moonActiveLabel = Label(self.moonConfigActiveFrame,text="Show Moon:")
        self.moonActiveLabel.pack()
        self.moonActiveChecked = BooleanVar()
        self.moonActiveChecked.set(False)
        self.moonActiveCheckbox = Checkbutton(self.moonConfigActiveFrame,variable=self.moonActiveChecked)
        self.moonActiveCheckbox.pack()
        self.minAltMoonLabel = Label(self.moonConfigAltFrame,text="Moon Minimum Alt:")
        self.minAltMoonLabel.pack()
        self.minAltMoonEntry = Spinbox(self.moonConfigAltFrame,from_=-90,to=90,increment=1)
        self.minAltMoonEntry.pack()
        self.minAltMoonEntry.delete(0,"end")
        self.minAltMoonEntry.insert(0,"0")

        self.fig = Figure()
        #self.ax = self.fig.add_subplot(111)
        #self.ax.plot([x for x in range(10)],[x**2 for x in range(10)])
        self.gridspec = matplotlib.gridspec.GridSpec(2,1,height_ratios=[4,1])
        self.gridspec3 = matplotlib.gridspec.GridSpec(2,2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plotFrame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        self.obsplot = None
        self.obsleg = None
        self.saveFileName = None

        self.targetColorList = ['b','g','r','c','m']*10

    def run(self):
        self.fig.clf()

        beginDate,endDate = self.getDates()
        if not beginDate or not endDate:
          self.canvas.show()
          return

        locations = self.getLocationData()
        #print locations
        assert(len(locations)>0 and len(locations)<4)
        locations = [l for l in locations if l]
        if len(locations) < 1:
          self.canvas.show()
          return

        targetValids = self.validTargets()
        for t in targetValids:
          if not t:
            self.canvas.show()
            return
        targetData = self.getTargetData()
        targetDataToShow = [i for i in targetData if i['enabled']]
        colorsToShow = self.targetColorList[:len(targetDataToShow)]
        showMoon = bool(self.moonActiveChecked.get())
        axLeg = None
        if len(locations) == 1:
          mplSetupStandard()
          ax = self.fig.add_subplot(self.gridspec[0])
          axLeg = self.fig.add_subplot(self.gridspec[1])
          self.obsplot = ObservabilityPlot(
                    locations[0],
                    [i['ephem'] for i in targetDataToShow],
                    beginDate,
                    endDate,
                    minAlt=float(self.minAltEntry.get()),
                    minAltSun=float(self.minAltSunEntry.get()),
                    minAltMoon=float(self.minAltMoonEntry.get()),
                    samplingPeriodDays=int(self.samplingPeriodEntry.get()),
                              )
          #  def __init__(self,location,skyCoordList,year,minAlt=45.,minAltSun=-18.,minAltMoon=-5.,samplingPeriodDays=7):

          ax.set_title("Astro Observability Plan for "+locations[0]['name'])
          self.obsplot.plot(ax,colorList=colorsToShow,showMoon=showMoon)
    #def plot(self,outfilename,title=None,labels=None,show_all_times=False,colorList = ['b','g','r','c','m'],sunColor='y',showMoon=False,hatchList=None,sunHatch=None):

        else:
          mplSetupSmall()
          axLeg = self.fig.add_subplot(self.gridspec3[1,1])
          for iLoc, location in enumerate(locations):
            iGridSpecLoc = (iLoc / 2,iLoc % 2)
            ax = self.fig.add_subplot(self.gridspec3[iGridSpecLoc])
            self.obsplot = ObservabilityPlot(
                      location,
                      [i['ephem'] for i in targetDataToShow],
                      beginDate,
                      endDate,
                      minAlt=float(self.minAltEntry.get()),
                      minAltSun=float(self.minAltSunEntry.get()),
                      minAltMoon=float(self.minAltMoonEntry.get()),
                      samplingPeriodDays=int(self.samplingPeriodEntry.get()),
                                )
            ax.set_title(location['name'])
            self.obsplot.plot(ax,colorList=colorsToShow,showMoon=showMoon)
            xticks = ax.get_xticks()
            if len(xticks)>7:
              ax.set_xticks(xticks[1::2])

        self.obsleg = LegendForObservability(
                                        axLeg,
                                        colorsToShow,
                                        [i['name'] for i in targetDataToShow],
                                        self.obsplot,
                                        showMoon=showMoon,
                                        horizontal = len(locations)==1
                              )

        self.canvas.show()

    def validTargets(self):
        return [conf.status() for conf in self.targetConfigs if conf.isAlive() and not conf.nameEmpty()]

    def getTargetData(self):
        return [conf.get() for conf in self.targetConfigs if conf.isAlive() and not conf.nameEmpty()]

    def getLocationData(self):
        return [loc.get() for loc in self.locationConfigs]

    def makeEmptyTargetConfig(self):
        emptyTargetConfigs = [True for conf in self.targetConfigs if conf.isAlive() and conf.nameEmpty()]
        if len(emptyTargetConfigs) == 0:
          self.targetConfigs.append(TargetConfig(self))

    def saveFile(self):
        assert(self.saveFileName)
        self.fig.savefig(self.saveFileName)

    def saveFileAs(self):
        self.saveFileName = tkinter.filedialog.asksaveasfilename(defaultextension=".png",filetypes=[('PNG Image','.png'),('Portable Document Format','.pdf'),("Scalable Vector Graphics Image",'.svg')],title="Save Astro Observability Plan As")
        #print "filename: ",self.saveFileName
        if self.saveFileName:
          self.fig.savefig(self.saveFileName)
          self.fileMenu.entryconfig("Save",state="normal")

    def getDates(self):
        """
            returns beginDate, endDate
            They are each python datetime.date objects.
        """
        beginDate = None
        endDate = None
        try:
          beginYear  = int(self.beginYearEntry.get())
          beginMonth = int(self.beginMonthEntry.get())
          beginDay   = int(self.beginDayEntry.get())
          #print beginYear,beginMonth,beginDay
          beginDate = datetime.date(beginYear,beginMonth,beginDay)
        except Exception as e:
          print("Error getting begin date: ",e)
        try:
          endYear    = int(self.endYearEntry.get())
          endMonth   = int(self.endMonthEntry.get())
          endDay     = int(self.endDayEntry.get())
          #print endYear,endMonth,endDay
          endDate = datetime.date(endYear,endMonth,endDay)
        except Exception as e:
          print("Error getting end date: ",e)
        #print beginDate,endDate
        self.beginDateStatusVar.set("")
        if not beginDate or not endDate:
          self.beginDateStatusVar.set(":-(")
        self.endDateStatusVar.set("")
        if not endDate:
          self.endDateStatusVar.set(":-(")
        return beginDate,endDate

    def onAddLocation(self):
        if len(self.locationConfigs)==1:
          self.addLocationVar.set("One Location")
          self.locationConfigs.append(LocationConfig(self))
          self.locationConfigs.append(LocationConfig(self))
        else:
          self.addLocationVar.set("More Locations")
          for i in range(len(self.locationConfigs)-1):
            oldLoc =  self.locationConfigs.pop()
            oldLoc.delete()

class TargetConfig(object):

    def __init__(self, gui):
        self.gui = gui
        self.master = self.gui.targetConfigFrame
        self.frame = Frame(self.master,pady=5)
        self.frame.pack()
        
        self.targetChecked = BooleanVar()
        self.targetChecked.set(True)
        self.targetCheckbox = Checkbutton(self.frame, variable=self.targetChecked)
        self.targetCheckbox.pack(side=LEFT)

        self.targetNameVar = StringVar()
        self.targetNameVar.set("")
        self.targetNameVar.trace('w', self.onNameModified) # callback on write
        self.targetNameBox = Entry(self.frame,width=20,textvariable=self.targetNameVar)
        self.targetNameBox.pack(side=LEFT)

        self.targetDelButton = Button(self.frame,fg="red",text="Delete",command=self.delSelf)
        self.targetDelButton.pack(side=LEFT)

        self.targetStatusLabelTextVar = StringVar()
        self.targetStatusLabelTextVar.set("")
        self.targetStatusLabel = Label(self.frame,width=3,textvariable=self.targetStatusLabelTextVar)
        self.targetStatusLabel.pack(side=LEFT)

        self.alive = True
        self.targetEphem=None

    def isAlive(self):
        return self.alive

    def delSelf(self):
        self.frame.pack_forget()
        self.frame.destroy()
        self.alive = False
        self.gui.makeEmptyTargetConfig()

    def status(self):
        if self.nameEmpty():
          return False
        targetName = self.targetNameVar.get()
        targetName = targetName.strip()
        try:
          self.targetEphem = lookuptargetxephem(targetName)
          self.targetStatusLabelTextVar.set(":-)")
          self.targetStatusLabel.configure(fg="green")
          return True
        except NameResolveError as e:
          print("lookuptarget exception: ",e)
          self.targetStatusLabelTextVar.set(":-(")
          self.targetStatusLabel.configure(fg="red")
          return False
    def get(self):
        result = {
                    "enabled":self.targetChecked.get(),
                    "name":self.targetNameVar.get().strip(),
                    "ephem":self.targetEphem,
                 }
        return result

    def nameEmpty(self):
        text = self.targetNameVar.get()
        if len(text.strip())>0:
          return False
        return True

    def onNameModified(self,*argv):
        text = self.targetNameVar.get()
        #print text
        if not self.nameEmpty():
          self.gui.makeEmptyTargetConfig()

class LocationConfig(object):

    def __init__(self, gui):
        self.gui = gui
        self.master = self.gui.locationEntryFrame
        self.selectedLocName = StringVar()
        self.widget = tkinter.ttk.Combobox(self.master,textvariable=self.selectedLocName,state='readonly')
        self.widget.pack()

        self.locationCache = LocationCache()

        self.defaultStr = "Select Location"
        self.createStr = "Create New Location"
        self.widget['values'] = [self.defaultStr]+self.locationCache.getLocNameList()+[self.createStr]
        self.widget.current(0)
        self.selectedLocName.trace('w',self.onSelectedLocNameChange)

    def delete(self):
        self.widget.destroy()

    def onSelectedLocNameChange(self,*argv):
        if self.selectedLocName.get() == self.createStr:
            LocationCreateDialog(self.master,self.updateLocation)

    def get(self):
        locName = self.selectedLocName.get()
        if locName == self.defaultStr or locName == self.createStr:
            return None
        else:
            result =  self.locationCache.getLocEntry(locName)
            result['name'] = locName
            return result

    def updateLocation(self,locData):
        #print "running updateLocation with: ",locData
        if locData:
          try:
            locName = locData['name']
            self.locationCache.addLocEntry(locName,locData['latitude'],locData['longitude'],locData['elevation'],locData['tz'])
            newLocList = list(self.widget['values'])
            newLocList.insert(1,locName)
            self.widget['values'] = tuple(newLocList)
            #print self.widget['values']
            self.widget.current(1)
          except LocationError as e:
            print(e)

class LocationCreateDialog(object):
  def __init__(self,creatorWindow,doneCallback):
    """
      Will grey out creatorWindow and give new data dict to doneCallback
    """
    self.creatorWindow = creatorWindow
    self.doneCallback = doneCallback
    self.top = Toplevel()
    self.top.title("Create New Location")

    self.frame = Frame(self.top)
    self.frame.pack()

    self.nameLabel = Label(self.frame,text="Location Name")
    self.nameLabel.pack()
    self.nameEntry = Entry(self.frame,width=20)
    self.nameEntry.pack()
    self.latLabel = Label(self.frame,text="Latitude")
    self.latLabel.pack()
    self.latEntry = Entry(self.frame,width=20)
    self.latEntry.pack()
    self.lonLabel = Label(self.frame,text="Longitude")
    self.lonLabel.pack()
    self.lonEntry = Entry(self.frame,width=20)
    self.lonEntry.pack()
    self.elevationLabel = Label(self.frame,text="Elavation (meters)")
    self.elevationLabel.pack()
    self.elevationEntry = Entry(self.frame,width=10)
    self.elevationEntry.pack()
    self.tzLabel = Label(self.frame,text="Time Zone")
    self.tzLabel.pack()
    self.tzEntry = Entry(self.frame,width=10)
    self.tzEntry.pack()
    self.create = Button(self.top,text="Create",command=self.onCreate)
    self.create.pack()

    self.top.grab_set()
    self.top.protocol("WM_DELETE_WINDOW", self.onCloseWindow)

  def onCreate(self,*argv):
    name = self.nameEntry.get()
    lat = self.latEntry.get()
    lon = self.lonEntry.get()
    elevation = self.elevationEntry.get()
    tz = self.tzEntry.get()
    data = {
                'name':name,
                'latitude':lat,
                'longitude':lon,
                'elevation':elevation,
                'tz':tz,
           }
    self.destroyWindow()
    self.doneCallback(data)
    
  def onCloseWindow(self,*argv):
    self.destroyWindow()
    self.doneCallback(None)

  def destroyWindow(self):
    #print "releasing grab"
    self.top.grab_release()
    self.top.destroy()
    
