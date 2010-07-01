#!/usr/bin/env python

'''a clone of data viewer by Matt Newville, as a wxPython learning project by Damon Wang. 22 June 2010

11:25 24 Jun 2010: refactored data display into DataSheet object (subclass of Panel)
10:12 24 Jun 2010: opens multiple files from each Open command, in AuiNotebook
17:00 22 Jun 2010: File menu with Open command, opens one file in a StyledTextCtrl'''

from __future__ import with_statement
import wx
from wx import stc
from wx import aui
import os
import sys

#------------------------------------------------------------------------------

class Frame(wx.Frame):
    '''straight inherited from wx.Frame, but created in case I need to
    customize it later.'''
    pass

#------------------------------------------------------------------------------

class MainFrame(Frame):
    '''The main viewer frame.

    Attributes:
        panel: main panel
        sizer: sizer for panel, holding nb
        nb: holds one data file per page
        datasheets: holds open DataSheets
        statusbar
        menubar
    
    '''

    def __init__(self, *args, **kwargs):
        '''Arguments get passed directly to Frame.__init__(). Creates
        statusbar, menubar, and a single full-size panel.'''

        Frame.__init__(self, *args, **kwargs)

        self.datasheets = []

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)
        self.nb = aui.AuiNotebook(parent=self.panel)
        self.sizer.AddF(item=self.nb, flags=wx.SizerFlags(1).Expand())

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("statusbar", 0)

        self.menubar = wx.MenuBar()
        filemenu = wx.Menu()
        filemenu_open = filemenu.Append(-1, "&Open", "Open a data file")
        self.menubar.Append(filemenu, "&File")
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU, self.OnClickFileOpen, filemenu_open)

        self.panel.Layout()

    def OnClickFileOpen(self, event):
        '''Event handler that asks for a file, creates an edit window
        (StyledTextCtrl), and reads the file into that window.'''

        dlg = wx.FileDialog(
            parent=self, 
            message="Choose a data file",
            defaultDir=os.getcwd(),
            style=wx.OPEN | wx.CHANGE_DIR | wx.MULTIPLE
            )

        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                try:
                    ds = DataSheet(parent=self, filename=path)
                    self.datasheets.append(ds)
                    self.nb.AddPage(ds, caption=path, select=True)
                    self.panel.Layout()
                except IOError as e:
                    wx.MessageBox(caption="File not found", 
                            message="file %s not found, not opened." % e.filename)
        dlg.Destroy()
#------------------------------------------------------------------------------

class DataSheet(wx.Panel):
    '''Holds one data set

    Attributes:
        filename: name of file data came from
        editwindow: StyledTextCtrl for editing data 
        sizer
        no panel because it IS a panel!
    '''

    def __init__(self, parent, filename=None):
        '''Reads in the file and displays it.
        
        Args:
            parent: parent window
            filename: name of data file
            
        Throws:
            IOError(errno=2) if file not found'''

        if not os.path.isfile(filename):
            raise IOError(2, "no such file", filename)

        wx.Panel.__init__(self, parent=parent)

        self.filename = filename

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        with open(filename, "r") as inf:
            data = inf.read()
            print >> sys.stderr, "opened %s and read %s" % (filename, data[:80])

            self.editwindow = stc.StyledTextCtrl(self, -1)
            self.editwindow.SetText(data)
            self.sizer.AddF(item=self.editwindow, flags=wx.SizerFlags(1).Expand())
            self.Layout()

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
 
