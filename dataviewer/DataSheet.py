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

    def getCtrls(self, wanted=None):
        '''collects the values of all controls
        
        Args:
            wanted: a ctrl.var or a list of them

        Returns: 
            a dictionary of values indexed by ctrl.var if wanted is a list
            the single value if wanted is a single string (e.g., "Plot")

        Throws:
            KeyError: if no such ctrl exists
            AttributeError: if ctrl exists but is not set'''

        if wanted is None:
            wanted = self.ctrls.keys()

        # Cannot try to iterate and catch the error. Strings are iterable.
        if isinstance(wanted, list):
            return dict([ (key, self.ctrls[key].selection) for key in wanted ])
        else:
            return self.ctrls[wanted].selection

    def mkNewFrame(self, name="New Frame"):
        rv = MPlot.ImageFrame(parent=self, name=name)
        self.plotframes.append(rv)
        rv.Bind(event=wx.EVT_CLOSE, handler=self.onPlotFrameClose)
        rv.Show()
        self.updatePlotCtrl()
        return rv

    def getPlotDest(self):
        '''returns the object on which to call plot/oplot/etc.
        
        Throws:
            AttributeError: if no plotting destination is chosen yet
            IndexError: if chosen destination does not exist'''

        destChoice = self.getCtrls("Plot")
        print("destChoice = %s" % destChoice)

        if self.isPanel(destChoice):
            dest = self.plot
        elif self.isNewFrame(destChoice):
            dest = self.mkNewFrame(name=self.getPlotName())
        elif self.isExistingFrame(destChoice):
            dest = [ p for p in self.plotframes 
                    if "Plot %s" % p.GetName() == destChoice ][0]
        else:
            raise IndexError(destChoice)

        return dest

    def onPlot(self, event, **kwargs):
        '''reads ctrls and plots
        
        Args:
            kwargs passed in get passed to doPlot. Use a closure to set these.'''

        try: # what data should we plot?
            dataSrc = self.getDataChoice()
        except KeyError, e:
            wx.MessageBox("Please choose your %s" % e.message)
            return
        
        try: # where should we plot it?
            dest = self.getPlotDest()
        except (IndexError, AttributeError), e:
            wx.MessageBox('''Please choose a valid plotting destination
                    given: %s''' % e.message)
            return

        self.doPlot(dataSrc, dest, **kwargs)

        # TODO: cruft to refactor
        destChoice = self.getCtrls("Plot")
        if self.isExistingFrame(destChoice):
            dest.SetName("%s" % dataSrc)
            self.updatePlotCtrl()
        elif self.isPanel(destChoice):
            print("twiddling")
            self.GetParent().Layout()
            self.sizer.Fit(self)
            self.sizer.SetSizeHints(self)
            self.Parent.Parent.Layout()
            self.Refresh()
            twiddleSize(self.Parent.Parent)
        else: dest.Raise()


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
    def getDataChoice(self):
        raise NotImplementedError("getDataChoice")
    def doPlot(self, dataSrc, dest):
        raise NotImplementedError("plot")
    def getPlotName(self):
        raise NotImplementedError("getPlotName")

