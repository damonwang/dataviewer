#!/usr/bin/env python

'''a clone of data viewer by Matt Newville, as a wxPython learning project by Damon Wang. 22 June 2010


15:00 01 Jul 2010: refactored controls into function to pull all selections into hash
10:00 01 Jul 2010: plotting works
15:00 24 Jun 2010: added VarSelCtrl to choose x, y variables
11:25 24 Jun 2010: refactored data display into DataSheet object (subclass of Panel)
10:12 24 Jun 2010: opens multiple files from each Open command, in AuiNotebook
17:00 22 Jun 2010: File menu with Open command, opens one file in a StyledTextCtrl'''

#------------------------------------------------------------------------------
# IMPORTS

from __future__ import with_statement
from __future__ import print_function

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

def _twiddleSize(dest):
    '''sends dest a useless wx.SizeEvent, to fix some bugs I don't understand.'''
    dest.GetEventHandler().ProcessEvent(event=wx.SizeEvent(sz=dest.GetSize()))

def createButton(handler, parent, label, sizer, flags=wx.SizerFlags().Border(), **kwargs):
    '''creates a button with parent and label, binds to handler, and adds to
    sizer with flags. Additional args go to Button constructor.
    
    Returns: a wx.Button'''

    rv = wx.Button(parent=parent, label=label, **kwargs)
    rv.Bind(event=wx.EVT_BUTTON, handler=handler)
    sizer.AddF(item=rv, flags=flags)
    return rv

def createMenuBar(menubar, setInto=None):
    '''creates a menubar and optionally attaches it to something

    a menubar is a list of menus.

    Args:
        setInto: something with a SetMenuBar method
        menubar: see above

    Returns: a wx.Menubar'''

    rv = wx.MenuBar()
    for menu in menubar:
        m = createMenu(menu=menu)
        rv.Append(menu=m, title=menu[0])

    if setInto is not None:
        setInto.SetMenuBar(rv)

    return rv

def createMenu(menu, setInto=None):
    '''creates a menu and optionally attaches it to a wx.MenuBar

    a menu is described by a 2-tuple whose
        first element is a title suitable for wx.Menu()
        second element is a list of tuples and dicts:
            lists represent submenus
            dicts represent menu items

    a menu item is represented by a dict suitable for **kwargs expansion into
    wx.Menu.Append().

    Args:
        menu: see above
        setInto: a wx.MenuBar to attach the result to

    Returns: a wx.Menu'''

    rv = wx.Menu(title=menu[0])
    for item in menu[1]:
        if isinstance(item, tuple):
            rv.AppendMenu(text=item[0], submenu=createMenu(item))
        elif isinstance(item, dict):
            handler = item["handler"]
            del item["handler"]
            m = rv.Append(**item)
            rv.Bind(event=wx.EVT_MENU, handler=handler, source=m)
        else:
            raise TypeError(item)
    
    if setInto is not None:
        setInto.Append(menu=rv, title=rv.title)

    return rv

def _reportPedigree(self):
    '''returns tree-like output describing parent-child relationships below the given window.
    
    Args: 
        self: window to start reporting at
        
    Returns:
        string with tree-like pedigree'''


    return [str(self)] + sum( 
            [ map(lambda s: "  " + s, _reportPedigree(child))
                    for child in self.Children if "Children" in dir(child)
            ], [])
        

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
        visibleDS: Datasheet shown in right pane
        statusbar
        menubar
    
    '''

    def __init__(self, *args, **kwargs):
        '''Arguments get passed directly to Frame.__init__(). Creates
        statusbar, menubar, and a single full-size panel.'''

        Frame.__init__(self, *args, **kwargs)

        self.datasheets = []

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.sizer)

        self.splitW = wx.SplitterWindow(parent=self.panel,
                style=wx.SP_BORDER)
        self.sizer.AddF(item=self.splitW, flags=wx.SizerFlags(1).Expand())

        self.tree = wx.TreeCtrl(parent=self.splitW, 
                style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        self.tree.AddRoot(text="root")

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("statusbar", 0)

        self.menubar = wx.MenuBar()
        filemenu = wx.Menu()
        filemenu_open = filemenu.Append(-1, "&Open", "Open a data file")
        self.menubar.Append(filemenu, "&File")
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU, self.OnClickFileOpen, filemenu_open)

        #self.menubar = createMenuBar(setInto=self, menubar=[
            #("&File", [dict(id=-1, text="&Open", help="Open a data file",
                #handler=self.OnClickFileOpen)])])

        self.visibleDS = wx.Panel(self.splitW)
        self.splitW.SplitVertically(window1=self.tree, window2=self.visibleDS) 
        self.tree.SetMinSize(self.tree.GetSize())

        self.sizer.SetSizeHints(self)
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

        ds = None
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                if not os.path.isfile(path):
                    wx.MessageBox(caption="File not found", 
                            message="file %s not found, not opened." % path)
                    continue
                item=self.tree.AppendItem(parent=self.tree.GetRootItem(), 
                        text=os.path.basename(path))
                self.tree.Fit()
                ds = DataSheet(parent=self.splitW, filename=path, treeItem=item,
                        writeOut=lambda s: self.statusbar.SetStatusText(s, 0),
                        writeErr=lambda s: self.statusbar.SetStatusText(s, 0))
                self.datasheets.append(ds)
                self.tree.SetItemPyData(item=item, obj=ds)
        dlg.Destroy()

        if ds != self.splitW.GetWindow2():
            old = self.splitW.GetWindow2()
            self.splitW.ReplaceWindow(winNew=ds, winOld=old)
            old.Destroy()
            self.visibleDS = ds

        print("\n".join(_reportPedigree(self)), file=sys.stderr)

        self.sizer.SetSizeHints(self)
        self.sizer.Layout()


#------------------------------------------------------------------------------

class VarSelPanel(wx.Panel):
    '''Lets user set a variable from allowed options via dropdown-menu.

    Attributes:
        var: variable controlled by this VarSelPanel
        options: options for this variable
        label: label to display to user
        dropdown: dropdown menu to display to user
        selection: choice made by user (None if user has not done anything)
        defchoice:  None means no default
                    non-None in options means use that option
                    non-None not in options means use first option
        sizer
    '''

    def __init__(self, parent, var, options, **kwargs):
        wx.Panel.__init__(self, parent=parent)

        self.var, self.options = var, options

        print(self.options, file=sys.stderr)

        dk = dict(sizerFlags=wx.SizerFlags().Border(), label="%s =" % var)
        dk.update(**kwargs)

        if 'defchoice' in kwargs:
            if dk['defchoice'] in options:
                self.selection = dk['defchoice']
            else:
                dk['defchoice'] = self.selection = options[0]

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.label = wx.StaticText(parent=self, label=dk['label'])
        self.sizer.AddF(item=self.label, flags=wx.SizerFlags().Center().Border())

        self.dropdown = wx.ComboBox(parent=self, style=wx.CB_READONLY,
                choices=self.options)
        if 'defchoice' in kwargs:
            self.dropdown.SetValue(self.selection)
        self.Bind(event=wx.EVT_COMBOBOX, handler=self.OnEvtComboBox, 
                source=self.dropdown)
        self.sizer.AddF(item=self.dropdown, flags=wx.SizerFlags(1).Center())

        self.sizer.SetSizeHints(self)

        if 'sizer' in kwargs:
            dk['sizer'].AddF(item=self, flags=dk['sizerFlags'])

    def OnEvtComboBox(self, event):
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
        writeOut: function that writes normal output to the right place
        writeErr: same for errors
        treeItem: its entry in the TreeCtrl nav bar
        sizer
        no panel because it IS a panel!
    '''

    def __init__(self, parent, filename=None, treeItem=None,
            writeOut=lambda s: self._def_writeOut,
            writeErr=lambda s: self._def_writeErr):
        '''Reads in the file and displays it.
        
        Args:
            parent: parent window
            filename: name of data file
            writeOut: function that writes normal output to the right place
            writeErr: same for errors
            
        Throws:
            IOError(errno=2) if file not found'''

        if not os.path.isfile(filename):
            raise IOError(2, "no such file", filename)

        wx.Panel.__init__(self, parent=parent)

        self.filename, self.parent, self.plot = filename, parent, None
        self.treeItem = treeItem
        self.writeOut, self.writeErr = writeOut, writeErr

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.AddF(item=self.ctrlsizer, flags=wx.SizerFlags())

        self.data = ED.escan_data(file=filename)

        self.ctrls = [ 
            VarSelPanel(parent=self, var="X", sizer=self.ctrlsizer,
                options=[ x[0] for x in self.data.pos_names]) ,
            VarSelPanel(parent=self, var="Y", sizer=self.ctrlsizer,
                options=self.data.sums_names) ]

        self.plotbtn = createButton(parent=self, label="Plot", 
            handler=self.onPlot, sizer=self.ctrlsizer)
        self.oplotbtn = createButton(parent=self, label="Overplot",
            handler=self.onOverPlot, sizer=self.ctrlsizer)

        self.sizer.SetSizeHints(self)
        self.Layout()
    
    def onEvent(self, event):
        '''just pops up a MesssageBox announcing the event'''
        pass

    def _getCtrls(self):
        '''collects the values of all controls

        Returns: a dictionary of values indexed by control name'''

        def iter():
            for ctrl in self.ctrls:
                try:
                    yield (ctrl.var, ctrl.selection)
                except AttributeError:
                    pass

        return dict([ i for i in iter() ])

    def onOverPlot(self, event):
        '''adds a trace to the existing plot'''

        ctrls = self._getCtrls()
        try:
            data = { "X" : self._getXData(name=ctrls["X"]), 
                    "Y" : self._getYData(name=ctrls["Y"]) }
        except KeyError, e:
            wx.MessageBox("Please choose your %s axis" % e.args[0])
            return None
        self.writeOut("overplotting %s vs %s" % (ctrls["Y"], ctrls["X"]))

        self.plot.oplot(xdata=data["X"], ydata=data["Y"])

        self.sizer.SetSizeHints(self)
        self.sizer.Layout()
        _twiddleSize(self.Parent)

    def onPlot(self, event):
        '''Reads ctrls and plots'''

        ctrls = self._getCtrls()
        try:
            data = { "X" : self._getXData(name=ctrls["X"]), 
                    "Y" : self._getYData(name=ctrls["Y"]) }
        except KeyError, e:
            wx.MessageBox("Please choose your %s axis" % e.args[0])
            return None

        self.writeOut("plotting %s vs %s" % (ctrls["Y"], ctrls["X"]))

        newplot = MPlot.PlotPanel(parent=self)
        newplot.plot(xdata=data["X"], ydata=data["Y"])
        newplot.SetMinSize((400,300))
        if self.plot is not None:
            self.sizer.Detach(self.plot)
            print("destroying old plot", file=sys.stderr)
            self.plot.Destroy()
        self.plot = newplot
        self.sizer.AddF(item=self.plot, 
                flags=wx.SizerFlags(1).Expand().Center().Border())

        if self.plotbtn.GetLabel() != "Replot":
            self.plotbtn.SetLabel("Replot")

        self.sizer.SetSizeHints(self)
        self.Layout()
        _twiddleSize(self.Parent)

    def _getXData(self, name):
        '''returns a 1D iterable of positioning data for X axis

        Args:
            name: a name from self.data.pos_names'''

        return [ self.data.pos[i] for i in range(len(self.data.pos)) if self.data.pos_names[i][0] == name][0]

    def _getYData(self, name):
        '''returns a 1D iterable of intensity(?) data for Y axis
        
        Args:
            name: a name from self.data.sums_names'''

        return self.data.get_data(name=name)

    def _def_writeOut(self, s):
        '''default output goes to sys.stdout'''

        print(s)

    def _def_writeErr(self, s):
        '''default error goes to sys.stderr'''

        print(s, file=sys.stderr)

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
 
