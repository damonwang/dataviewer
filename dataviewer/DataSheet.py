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

    inPanelOpt, inNewFrameOpt = "In Panel", "New Plot"

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

        defaults = dict(filename=None, parent=None, treeItem=None, plotframes=[],
            writeOut=lambda s: self._def_writeOut,
            writeErr=lambda s: self._def_writeErr)

        for attr in ["filename", "parent", "treeItem", "writeOut", "writeErr", "plotframes"]:
            self.__setattr__(attr, kwargs.get(attr, defaults[attr]))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.data = self.readData(file=self.filename)
        self.mkCtrls()
        self.mkPanelPlot()

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
            destChoice = ctrls["Plot"]
        except KeyError, e:
            wx.MessageBox("Please choose your %s axis" % e.args[0])
            return None

        if self.isPanel(destChoice):
            dest = self.plot
        elif self.isNewFrame(destChoice):
            dest = MPlot.PlotFrame(parent=self, 
                    name="%s v. %s" % (ctrls["Y"], ctrls["X"]))
            self.plotframes.append(dest)
            dest.Bind(event=wx.EVT_CLOSE, handler=self.onPlotFrameClose)
            dest.Show()
            self.updatePlotCtrl()
        elif self.isExistingFrame(destChoice):
            try:
                dest = [ p for p in self.plotframes 
                        if "Plot %s" % p.GetName() == destChoice ][0]
            except IndexError:
                wx.MessageBox("could not find existing plot '%s'" % destChoice)
                return
        else: 
            wx.MessageBox("cannot plot to '%s'---no such destination" % destChoice)
            return

        self.writeOut("%s %s vs %s" % (("Plotting", "Overplotting")[overplot], 
            ctrls["Y"], ctrls["X"]))

        if overplot and not self.isNewFrame(ctrls["Plot"]):
            dest.oplot(data["X"], data["Y"])
        else: 
            dest.plot(data["X"], data["Y"])
            if self.isExistingFrame(destChoice):
                dest.SetName("%s v. %s" % (ctrls["Y"], ctrls["X"]))
                self.updatePlotCtrl()

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

    @staticmethod
    def isNewFrame(dest):
        return dest == DataSheet.inNewFrameOpt

    @staticmethod
    def isPanel(dest):
        return dest == DataSheet.inPanelOpt

    @staticmethod
    def isExistingFrame(dest):
        return "Plot " in dest

    def onPlotFrameClose(self, event):
        pf = event.GetEventObject()
        try:
            self.plotframes.remove(pf)
        except ValueError:
            pass

        self.updatePlotCtrl()
        pf.Destroy()

    def updatePlotCtrl(self):
        '''discovers possible plotting destinations and updates the control.'''

        opts = ["Plot %s" % p.GetName() for p in self.plotframes]
        opts += [ DataSheet.inPanelOpt, DataSheet.inNewFrameOpt ]

        self.plotctrl.setOptions(opts, defchoice=-1)

    def readData(self, file):
        raise NotImplementedError("readData")
