#!/usr/bin/env python

'''a clone of data viewer by Matt Newville, as a wxPython learning project by Damon Wang. 22 June 2010


15:00 24 Jun 2010: added VarSelCtrl to choose x, y variables
11:25 24 Jun 2010: refactored data display into DataSheet object (subclass of Panel)
10:12 24 Jun 2010: opens multiple files from each Open command, in AuiNotebook
17:00 22 Jun 2010: File menu with Open command, opens one file in a StyledTextCtrl'''

#------------------------------------------------------------------------------
# IMPORTS

from __future__ import with_statement
import wx
from wx import stc
from wx import aui
import os
import sys
import escan_data as ED
import MPlot

#------------------------------------------------------------------------------
# GLOBALS

padding = 5
axes = ["X", "Y"]

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
        self.nb = aui.AuiNotebook(parent=self.panel, 
                style=wx.aui.AUI_NB_DEFAULT_STYLE | 
                    wx.aui.AUI_NB_TAB_EXTERNAL_MOVE | 
                    wx.aui.AUI_NB_MIDDLE_CLICK_CLOSE)
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

class VarSelPanel(wx.Panel):
    '''Lets user set a variable from allowed options via dropdown-menu.

    Attributes:
        var: variable controlled by this VarSelPanel
        options: options for this variable
        label: label to display to user
        dropdown: dropdown menu to display to user
        selection: choice made by user (None if user has not done anything)
        sizer
    '''

    def __init__(self, parent, var, options=[], label=None):
        wx.Panel.__init__(self, parent=parent)

        self.var = var
        self.options = options

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        if label is None:
            label = "%s =" % var
        self.label = wx.StaticText(parent=self, label=label)
        self.sizer.AddF(item=self.label, flags=wx.SizerFlags().Center().Border())

        self.dropdown = wx.Choice(parent=self, id=wx.NewId(), 
                choices=self.options)
        self.Bind(event=wx.EVT_CHOICE, handler=self.OnEvtChoice, 
                source=self.dropdown)
        self.sizer.AddF(item=self.dropdown, flags=wx.SizerFlags(1).Center())

        self.Layout()

    def OnEvtChoice(self, event):
        '''sets attribute selection when user makes a choice'''

        self.selection = event.GetString()

#------------------------------------------------------------------------------

class DataSheet(wx.Panel):
    '''Holds one data set

    Attributes:
        filename: name of file data came from
        ctrlsizer: horizontal BoxSizer holding ctrlx, ctrly
        ctrls: list of VarSelPanel controlling x axis data  source
        plotbtn: button to make a plot
        plot: Mplot window with plot
        parent: parent window
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
        self.parent = parent

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.AddF(item=self.ctrlsizer, flags=wx.SizerFlags())

        self.data = ED.escan_data(file=filename)

        self.ctrls = []
        for var in axes:
            self.ctrls.append(VarSelPanel(parent=self, var=var, 
                options=self.data.sums_names))
            self.ctrlsizer.AddF(item=self.ctrls[-1], flags=wx.SizerFlags().Border())

        self.plotbtn = wx.Button(self, label="Plot")
        self.ctrlsizer.AddF(item=self.plotbtn, flags=wx.SizerFlags().Right().Border())
        self.Bind(event=wx.EVT_BUTTON, handler=self.plot, source=self.plotbtn)

        self.Layout()

    def plot(self, event):
        '''Reads ctrls and plots'''

        srcs = [0] * len(axes)
        data = [0] * len(axes)

        for i in range(len(axes)):
            try:
                srcs[i] = self.ctrls[i].selection
            except AttributeError:
                wx.MessageBox("Please choose your %s axis" % axes[i])
                return None
            data[i] = self.data.get_data(name=axes[i])


        self.plot = MPlot.PlotFrame(parent=self)
        self.sizer.AddF(item=self.plot, flags=wx.SizerFlags(1).Expand().Center())

        self.plot.plot(data[0], data[1])

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
 
