#!/usr/bin/env python

'''a clone of data viewer by Matt Newville, as a wxPython learning project by Damon Wang. 22 June 2010 '''

#------------------------------------------------------------------------------
# IMPORTS

from __future__ import print_function

import wx
import os
import sys

from MainFrame import MainFrame
from WxUtil import *
from EpicsSheet import EpicsSheet

#------------------------------------------------------------------------------

class App(wx.App):
    def OnInit(self):
        self.mainframe = MainFrame(parent=None, id=-1, title='Data Viewer Clone')
        self.SetTopWindow(self.mainframe)
        self.mainframe.Show()
        return True

#------------------------------------------------------------------------------

if __name__ == "__main__":
    app = App(redirect=False)
    app.MainLoop()
 
