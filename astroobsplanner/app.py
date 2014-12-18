#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import Tkinter
import gui

def main(*arglist,**argkeys):
  root = Tkinter.Tk()
  root.title("Astro Observability Planner")
  
  myGui = gui.Gui(root)
  
  root.mainloop()

if __name__ == "__main__":
  main()
