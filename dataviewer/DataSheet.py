from __future__ import print_function

import wx
import MPlot
from VarSelPanel import VarSelPanel
#VarSelPanel = VarSelPanel.VarSelPanel

from WxUtil import *

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

        if self.isPanel(dest):
            dest = self.plot
        elif self.isNewFrame(dest):
            dest = MPlot.PlotFrame(parent=self)
            self.plotframes.append(dest)
            dest.Show()
            self.updatePlotCtrl()
        else: # self.isExistingFrame(dest)
            dest = self.plotframes[int(dest.split()[1])]

        self.writeOut("%s %s vs %s" % (("Plotting", "Overplotting")[overplot], 
            ctrls["Y"], ctrls["X"]))

        if overplot and not self.isNewFrame(ctrls["Plot"]):
            dest.oplot(data["X"], data["Y"])
        else: dest.plot(data["X"], data["Y"])

        if self.isPanel(ctrls["Plot"]):
            self.sizer.SetSizeHints(self)
            self.Layout()
            twiddleSize(self.Parent)
        elif self.isNewFrame(ctrls["Plot"]) or self.isExistingFrame(ctrls["Plot"]):
            dest.Raise()

    def _def_writeOut(self, s):
        '''default output goes to sys.stdout'''

        print(s)

    def _def_writeErr(self, s):
        '''default error goes to sys.stderr'''

        print(s, file=sys.stderr)

    def isNewFrame(self, dest):
        return dest == "New Plot"
    def isPanel(self, dest):
        return dest == "In Panel"
    def isExistingFrame(self, dest):
        return "Plot " in dest

    def updatePlotCtrl(self):

        self.plotctrl.setOptions(sum([ 
            [ "Plot %d" % i for i in range(len(self.plotframes))], 
            ["In Panel", "New Plot" ] ], []), defchoice=-1)
