#!/usr/bin/env python

'''a clone of data viewer by Matt Newville, as a wxPython learning project by Damon Wang. 22 June 2010

17:00 22 Jun 2010: File menu with Open command, opens one file in a StyledTextCtrl
10:12 24 Jun 2010: opens multiple files from each Open command, in AuiNotebook'''

from __future__ import with_statement
import wx
from wx import stc
from wx import aui
import os
import sys

class Frame(wx.Frame):
    '''straight inherited from wx.Frame, but created in case I need to
    customize it later.'''
    pass

class MainFrame(Frame):
    '''The main viewer frame.

    Attributes:
        panel: main panel
        sizer: sizer for panel, holding nb
        nb: holds one data file per page
        statusbar
        menubar
    
    '''

    def __init__(self, *args, **kwargs):
        '''Arguments get passed directly to Frame.__init__(). Creates
        statusbar, menubar, and a single full-size panel.'''

        Frame.__init__(self, *args, **kwargs)

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
             self.openDataFile(dlg.GetPaths())
        dlg.Destroy()


    def openDataFile(self, paths):
        '''Displays a data file.

        Args:

            paths = list of filename strings

        Returns:
            None'''

        if not os.path.isfile(paths[0]):
            print >> sys.stderr, "file doesn't exist!"
            return None
        for path in paths:
            with open(path, "r") as inf:
                data = inf.read()
                print >> sys.stderr, "opened %s and read %s" % (path, data[:80])

                self.editwindow = stc.StyledTextCtrl(self.panel, -1)
                self.editwindow.SetText(data)
                self.nb.AddPage(self.editwindow, caption=paths[0], select=True)
                self.panel.Layout()

class App(wx.App):
    def OnInit(self):
        self.mainframe = MainFrame(parent=None, id=-1, title='Data Viewer Clone')
        self.SetTopWindow(self.mainframe)
        self.mainframe.Show()
        return True


if __name__ == "__main__":
    app = App(redirect=False)
    app.MainLoop()
 
