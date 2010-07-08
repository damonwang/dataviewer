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

        self.ctrls = [ 
            VarSelPanel(parent=self, var="Data", sizer=self.ctrlsizer,
                options=self.getDataNames(), defchoice=-1),
            VarSelPanel(parent=self, var="Plot", sizer=self.ctrlsizer,
                options=[], defchoicelabel="in")]

        self.plotctrl = self.ctrls[-1] 
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

    def onPlot(self, event):
        '''reads ctrls and plots'''

        ctrls = self._getCtrls()
        try:
            data = self.getData(name=ctrls["Data"]) 
            destChoice = ctrls["Plot"]
        except KeyError, e:
            wx.MessageBox("Please choose your %s axis" % e.args[0])
            return None

        if self.isPanel(destChoice):
            print("plotting to panel")
            dest = self.plot
        elif self.isNewFrame(destChoice):
            dest = MPlot.ImageFrame(parent=self, name="%s" % ctrls["Data"])
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

        self.writeOut("Plotting %s" % ctrls["Data"])

        dest.display(data)
        if self.isExistingFrame(destChoice):
            dest.SetName("%s" % ctrls["Data"])
            self.updatePlotCtrl()

        if self.isPanel(ctrls["Plot"]):
            print("twiddling")
            self.sizer.Fit(self)
            self.sizer.SetSizeHints(self)
            self.Parent.Parent.Layout()
            self.Refresh()
            twiddleSize(self.Parent.Parent)
        elif self.isNewFrame(ctrls["Plot"]) or self.isExistingFrame(ctrls["Plot"]):
            dest.Raise()

    def getDataNames(self):
        raise NotImplementedError("getDataNames")

    def getData(self, name):
        raise NotImplementedError("getData")

