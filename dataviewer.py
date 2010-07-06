#!/usr/bin/env python

'''a clone of data viewer by Matt Newville, as a wxPython learning project by Damon Wang. 22 June 2010 '''

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
        m = createMenu(menu=menu, container=setInto)
        rv.Append(menu=m, title=menu[0])

    if setInto is not None:
        setInto.SetMenuBar(rv)

    return rv

def createMenu(menu, container, setInto=None):
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

    rv = wx.Menu()
    for item in menu[1]:
        if isinstance(item, tuple):
            rv.AppendMenu(text=item[0], submenu=createMenu(item))
        elif isinstance(item, dict):
            handler = item["handler"]
            del item["handler"]
            m = rv.Append(**item)
            container.Bind(event=wx.EVT_MENU, handler=handler, source=m)
        else:
            raise TypeError(item)
    
    if setInto is not None:
        setInto.Append(menu=rv, title=menu[0])

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

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("statusbar", 0)

        self.menubar = createMenuBar(setInto=self, menubar=self.configMenuBar())


        self.tree = wx.TreeCtrl(parent=self.splitW, 
                style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        self.tree.AddRoot(text="root")
        self.tree.Bind(event=wx.EVT_TREE_ITEM_ACTIVATED, handler=self.onTreeItemActivated)

        self.visibleDS = self.blankPanel = wx.Panel(self.splitW)
        self.splitW.SplitVertically(window1=self.tree, window2=self.visibleDS) 
        self.tree.SetMinSize(self.tree.GetSize())

        self.sizer.SetSizeHints(self)
        self.panel.Layout()


    def OnClickFileOpen(self, event):
        '''Event handler that asks for a file, creates an edit window
        (StyledTextCtrl), and reads the file into that window.'''

        dlg = wx.FileDialog(parent=self, message="Choose a data file",
            defaultDir=os.getcwd(), style=wx.OPEN | wx.CHANGE_DIR | wx.MULTIPLE)

        ds = None
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                ds = self.openDataSheet(path)
        dlg.Destroy()

        if ds is not None and ds != self.splitW.GetWindow2():
            self.showRightPane(ds)

        #print("\n".join(_reportPedigree(self)), file=sys.stderr)

        self.sizer.SetSizeHints(self)
        self.sizer.Layout()

    def configMenuBar(self):
        '''returns suitable createMenuBar input for the desired menu bar'''

        filemenu = ("&File", [])
        filemenu[1].append(dict(id=-1, text="&Open", help="Open a data file",
            handler=self.OnClickFileOpen))

        return [filemenu]

    def showRightPane(self, pane):
        '''sets pane as the right-hand window of the SplitterWindow. Does not
        destroy the current right-hand pane, just removes it.'''

        print("entered showRightPane, showing %s" % pane)
        old, self.visibleDS = self.splitW.GetWindow2(), pane
        self.splitW.ReplaceWindow(winNew=self.visibleDS, winOld=old)
        old.Hide()
        pane.Show()
        self.Layout()

    def onTreeItemActivated(self, event):
        '''when user clicks on a DataSheet's item in the tree, show that DataSheet.'''

        print("entered onTreeItemActivated, item is %s" % event.GetItem())

        self.showRightPane(self.tree.GetItemPyData(event.GetItem()))

    def openDataSheet(self, path):
        '''identifies the filetype, creates the DataSheet, adds it to the tree, and shows it.'''

        # TODO this should be pushed down into the DataSheet constructor
        if not os.path.isfile(path):
            wx.MessageBox(caption="File not found", 
                    message="file %s not found, not opened." % path)
            return

        item=self.tree.AppendItem(parent=self.tree.GetRootItem(), 
                text=os.path.basename(path))
        self.tree.Fit()

        ds = None
        for filetype in [EpicsSheet]:
            try:
                ds = filetype(parent=self.splitW, filename=path, treeItem=item,
                        writeOut=lambda s: self.statusbar.SetStatusText(s, 0),
                        writeErr=lambda s: self.statusbar.SetStatusText(s, 0))
                break;
            except FileTypeError:
                continue
        if ds is not None:
            self.datasheets.append(ds)
            self.tree.SetItemPyData(item=item, obj=ds)
        else:
            self.tree.Delete(item)
            wx.MessageBox("could not recognize filetype")

        return ds

#------------------------------------------------------------------------------
# Exceptions

class FileTypeError(Exception):
    def __init__(self, filename): 
        self.filename = filename
    
    def __str__(self):
        return "FileTypeError: %s of unrecognized type" % self.filename

class CtrlError(Exception):
    def __init__(self, ctrl, value):
        self.ctrl = ctrl
        self.value = value

    def __str__(self):
        return "CtrlError: %s set to %s (invalid)" % (self.ctrl, self.value)

#------------------------------------------------------------------------------


class VarSelPanel(wx.Panel):
    '''Lets user set a variable from allowed options via dropdown-menu.

    At least one option must be provided to constructor!

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

        self.var = var

        print(options, file=sys.stderr)

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
                choices=options)
        if 'defchoice' in kwargs:
            self.dropdown.SetValue(self.selection)
        self.Bind(event=wx.EVT_COMBOBOX, handler=self.onEvtComboBox, 
                source=self.dropdown)
        self.sizer.AddF(item=self.dropdown, flags=wx.SizerFlags(1).Center())

        self.sizer.SetSizeHints(self)

        if 'sizer' in kwargs:
            dk['sizer'].AddF(item=self, flags=dk['sizerFlags'])

    def onEvtComboBox(self, event):
        '''sets attribute selection when user makes a choice'''

        self.selection = event.GetString()

    def setOptions(self, options, defchoice=None):

        self.dropdown.SetItems(options)
        oldoptions = self.dropdown.GetItems()

        if defchoice is None:
            if self.selection not in oldoptions:
                self.selection = self.options[0]
                self.dropdown.Select(0)
        elif defchoice in options:
            dk['defchoice'] = self.selection = defchoice
            self.dropdown.Select(self.dropdown.GetItems().index(defchoice))
        else:
            dk['defchoice'] = self.selection = self.options[0]
            self.Select(0)

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

    def __init__(self, parent, **kwargs):
        '''Reads in the file and displays it.
        
        Args:
            parent: parent window
            filename: name of data file
            treeitem: wx.TreeItemId of this sheet's entry in the left-hand nav
            writeOut: function that writes normal output to the right place
            writeErr: same for errors
            
        Throws:
            IOError(errno=2) if file not found'''

        wx.Panel.__init__(self, parent=parent)

        defaults = dict(filename=None, parent=None, treeItem=None, 
            writeOut=lambda s: self._def_writeOut,
            writeErr=lambda s: self._def_writeErr)

        for attr in ["filename", "parent", "treeItem", "writeOut", "writeErr"]:
            self.__setattr__(attr, kwargs.get(attr, defaults[attr]))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.AddF(item=self.ctrlsizer, flags=wx.SizerFlags())

        self.plot = MPlot.PlotPanel(parent=self)
        self.plot.SetMinSize((400,300))
        self.plot.SetSize(self.plot.GetMinSize())
        self.sizer.AddF(item=self.plot, 
                flags=wx.SizerFlags(1).Expand().Center().Border())

        self.plotframes = []

        self.data = self.getData(file=self.filename)

        self.ctrls = [ 
            VarSelPanel(parent=self, var="X", sizer=self.ctrlsizer,
                options=self.getXDataNames(), defchoice=-1),
            VarSelPanel(parent=self, var="Y", sizer=self.ctrlsizer,
                options=self.getYDataNames(), defchoice=-1),
            VarSelPanel(parent=self, var="Plot", sizer=self.ctrlsizer,
                options=[], defchoicelabel="in")]

        self.plotctrl = self.ctrls[-1] 
        self.updatePlotCtrl()

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

        self.onPlot(event, overplot=True)

    def onPlot(self, event, overplot=False):
        '''Reads ctrls and plots'''

        ctrls = self._getCtrls()
        try:
            data = { "X" : self.getXData(name=ctrls["X"]), 
                    "Y" : self.getYData(name=ctrls["Y"]) }
            dest = ctrls["Plot"]
        except KeyError, e:
            wx.MessageBox("Please choose your %s axis" % e.args[0])
            return None

        if dest == "In Panel":
            dest = self.plot
        elif dest == "New Plot":
            dest = MPlot.PlotFrame(parent=self)
            self.plotframes.append(dest)
            dest.Show()
            self.updatePlotCtrl()
        else:
            dest = self.plotframes[int(dest.split()[1])]

        self.writeOut("%s %s vs %s" % (("Plotting", "Overplotting")[overplot], 
            ctrls["Y"], ctrls["X"]))

        if overplot:
            dest.oplot(xdata=data["X"], ydata=data["Y"])
        else: dest.plot(xdata=data["X"], ydata=data["Y"])

        self.sizer.SetSizeHints(self)
        self.Layout()
        _twiddleSize(self.Parent)

    def _def_writeOut(self, s):
        '''default output goes to sys.stdout'''

        print(s)

    def _def_writeErr(self, s):
        '''default error goes to sys.stderr'''

        print(s, file=sys.stderr)

    def updatePlotCtrl(self):

        self.plotctrl.setOptions(sum([ 
            [ "Plot %d" % i for i in range(len(self.plotframes))], 
            ["In Panel", "New Plot" ] ], []), defchoice=-1)

#------------------------------------------------------------------------------

class EpicsSheet(DataSheet):

    def getXData(self, name):
        '''returns a 1D iterable of positioning data for X axis

        Args:
            name: a name from self.data.pos_names'''

        return [ self.data.pos[i] 
                for i in range(len(self.data.pos)) 
                if self.data.pos_names[i][0] == name][0]

    def getXDataNames(self):

        return [ x[0] for x in self.data.pos_names]

    def getYDataNames(self):

        return self.data.sums_names

    def getYData(self, name):
        '''returns a 1D iterable of intensity(?) data for Y axis
        
        Args:
            name: a name from self.data.sums_names'''

        return self.data.get_data(name=name)

    def getData(self, file):

        if not os.path.isfile(file):
            raise IOError(2, "no such file", file)

        rv = ED.escan_data(file=file)
        # escan_data returns successfully regardless of whether it actually
        # opens the file or not, so we have to guess based on what comes back
        if rv.det_names != []:
            return rv
        else: raise FileTypeError(file)

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
 
