import wx
import MPlot
from WxUtil import *
from VarSelPanel import VarSelPanel
from DataSheet import DataSheet

class Data2DSheet(DataSheet):

    def mkCtrls(self):
        '''creates the controls.

        put them into your own sizer and put that one object into self.sizer

        put a list of controls into self.ctrls

        put the control which picks the plotting destination into self.plotctrl
        
        '''

        self.ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.PrependF(item=self.ctrlsizer, flags=wx.SizerFlags())

        self.ctrls = dict( 
            Data=VarSelPanel(parent=self, var="Data", sizer=self.ctrlsizer,
                options=self.getDataNames(), defchoice=-1),
            Plot=VarSelPanel(parent=self, var="Plot", sizer=self.ctrlsizer,
                options=[], defchoicelabel="in"))

        self.plotctrl = self.ctrls["Plot"] 
        self.updatePlotCtrl()

        self.plotbtn = createButton(parent=self, label="Plot", 
            handler=self.onPlot, sizer=self.ctrlsizer)

    def mkPanelPlot(self):
        '''creates the initial panel plot, before user can choose anything.

        assign the plot into self.plot
        add it into self.sizer
        '''
        print(" mkPanelPlot ")
        self.plot = MPlot.ImagePanel(parent=self)
        self.plot.SetMinSize((400,300))
        self.plot.SetSize(self.plot.GetMinSize())
        self.sizer.AddF(item=self.plot, 
                flags=wx.SizerFlags(1).Expand().Center().Border())
    
    def doPlot(self, dataSrc, dest):
        '''plots the named data to destination

        Args:
            dataSrc: name suitable for putting into getData
            dest: something with a plot or display method
        '''

        self.writeOut("Plotting %s" % dataSrc)
        data = self.getData(name=dataSrc)
        dest.display(data)

    def getDataChoice(self):
        '''returns something that can be passed as dataSrc argument to doPlot'''

        return self.getCtrls("Data")

    def getPlotName(self):

        return "Plot %s" % self.getCtrls("Data")

    def getDataNames(self):
        raise NotImplementedError("getDataNames")

    def getData(self, name):
        raise NotImplementedError("getData")

