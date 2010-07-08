import wx
import MPlot
from WxUtil import *
from VarSelPanel import VarSelPanel
from DataSheet import DataSheet

class Data1DSheet(DataSheet):

    def mkCtrls(self):
        '''creates the controls.

        put them into your own sizer and put that one object into self.sizer

        put a list of controls into self.ctrls

        put the control which picks the plotting destination into self.plotctrl
        
        '''

        self.ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.PrependF(item=self.ctrlsizer, flags=wx.SizerFlags())

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

    def mkPanelPlot(self):
        '''creates the initial panel plot, before user can choose anything.

        assign the plot into self.plot
        add it into self.sizer
        '''

        self.plot = MPlot.PlotPanel(parent=self)
        self.plot.SetMinSize((400,300))
        self.plot.SetSize(self.plot.GetMinSize())
        self.sizer.AddF(item=self.plot, 
                flags=wx.SizerFlags(1).Expand().Center().Border())

    def getXData(self, name):
        raise NotImplementedError("getXData")
    def getXDatanames(self):
        raise NotImplementedError("getXDataNames")
    def getYData(self, name):
        raise NotImplementedError("getYData")
    def getXDataNames(self):
        raise NotImplementedError("getYDataNames")
