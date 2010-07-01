#!/usr/bin/env python

'''a clone of data viewer by Matt Newville, as a wxPython learning project by Damon Wang. 22 June 2010

22 June 2010: File menu with Open command, opens one file in a StyledTextCtrl'''

from __future__ import with_statement
import wx
import os
import sys
from wx import stc

class Frame(wx.Frame):
    '''straight inherited from wx.Frame, but created in case I need to
    customize it later.'''
    pass

class MainFrame(Frame):
    '''The main viewer frame.'''

    def __init__(self, *args, **kwargs):
        '''Arguments get passed directly to Frame.__init__(). Creates
        statusbar, menubar, and a single full-size panel.'''

        Frame.__init__(self, *args, **kwargs)
        self.panel = wx.Panel(self)
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("statusbar", 0)
        self.menubar = wx.MenuBar()
        filemenu = wx.Menu()
        filemenu_open = filemenu.Append(-1, "&Open", "Open a data file")
        self.menubar.Append(filemenu, "&File")
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU, self.OnClickFileOpen, filemenu_open)

    def OnClickFileOpen(self, event):
        '''Asks for a file, creates an edit window (StyledTextCtrl), and reads
        the file into that window.'''

        dlg = wx.FileDialog(
            parent=self, 
            message="Choose a data file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="All files (*.*)|*.*",
            style=wx.OPEN | wx.CHANGE_DIR
            )

        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            if len(paths) > 1:
                print >> sys.stderr, "selected multiple files, only opening first..."
            elif not os.path.isfile(paths[0]):
                print >> sys.stderr, "file doesn't exist!"
            else:
                with open(paths[0], "r") as inf:
                    data = inf.read()
                print >> sys.stderr, "opened %s and read %s" % (paths[0], data[:80])

            itemId = event.GetId()
            self.panel.sizer = wx.BoxSizer(wx.VERTICAL)
            self.editwindow = stc.StyledTextCtrl(self.panel, -1)

            self.editwindow.SetText(data)
            self.panel.sizer.Add(self.editwindow, -1, wx.EXPAND)
            self.panel.SetSizer(self.panel.sizer)
            self.panel.Layout()

        dlg.Destroy()

class App(wx.App):
    def OnInit(self):
        self.mainframe = MainFrame(parent=None, id=-1, title='Data Viewer Clone')
        self.SetTopWindow(self.mainframe)
        self.mainframe.Show()
        return True


if __name__ == "__main__":
    app = App(redirect=False)
    app.MainLoop()
 
