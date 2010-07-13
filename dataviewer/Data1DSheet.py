import wx
import MPlot
from WxUtil import *
from VarSelPanel import VarSelPanel
from DataSheet import DataSheet

class Data1DSheet(DataSheet):

    def onOverPlot(self, event):
        '''adds a trace to the existing plot'''

        self.onPlot(event, overplot=True)

    def doPlot(self, dataSrc, dest, **kwargs):
        '''plots the named data to destination

        Args:
            dataSrc: dict { var : name }, name suitable for passing to getData
            dest: something with a plot method
        '''

        X = self.getXData(name=dataSrc["X"])
        Y = self.getYData(name=dataSrc["Y"])
        name = self.getPlotName(x=dataSrc["X"], y=dataSrc["Y"])

        if kwargs.get("overplot", False):
            self.writeOut("Overplotting %s" % name)
            try:
                dest.oplot(X, Y)
            except AttributeError, e:
                if e.message == "'PlotPanel' object has no attribute 'data_range'":
                    wx.MessageBox("cannot overplot before plotting. Will plot instead.")
                    self.doPlot(dataSrc, dest, overplot=False)
                else:
                    raise e
        else:
            self.writeOut("Plotting %s" % name)
            dest.plot(X, Y)

    def getDataChoice(self):
        '''returns something that can be passed as dataSrc argument to doPlot'''

        return self.getCtrls("X", "Y")

    def mkCtrls(self):
        '''creates the controls.

        put them into your own sizer and put that one object into self.sizer

        put a dict { var : ctrl } of controls into self.ctrls

        put the control which picks the plotting destination into self.plotctrl
        
        '''

        self.ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.PrependF(item=self.ctrlsizer, flags=wx.SizerFlags())

        self.ctrls = dict( 
            X=VarSelPanel(parent=self, var="X", sizer=self.ctrlsizer,
                options=self.getXDataNames(), defchoice=-1),
            Y=VarSelPanel(parent=self, var="Y", sizer=self.ctrlsizer,
                options=self.getYDataNames(), defchoice=-1),
            Plot=VarSelPanel(parent=self, var="Plot", sizer=self.ctrlsizer,
                options=[], defchoicelabel="in"))

        self.plotctrl = self.ctrls["Plot"] 
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

    def mkNewFrame(self, name="New Frame"):
        rv = MPlot.PlotFrame(parent=self, name=name)
        self.plotframes.append(rv)
        rv.Bind(event=wx.EVT_CLOSE, handler=self.onPlotFrameClose)
        rv.Show()
        self.updatePlotCtrl()
        return rv

    def getPlotName(self, x=None, y=None):
        '''returns a string following this plot's naming convention.

        Args:
            (optional) x, y: given the axes, formats them
            If none given, queries the controls
            Note that if just one axis is passed, it is ignored and the
            controls are queried anyway

        Returns:
            "Plot %{x}s v. %{y}s"
        '''
            
        if x is None or y is None:
            srcs = self.getDataChoice()
            x, y = srcs["X"], srcs["Y"]
        return "Plot %s v. %s" % (x, y)


    def getXData(self, name):
        raise NotImplementedError("getXData")
    def getXDataNames(self):
        raise NotImplementedError("getXDataNames")
    def getYData(self, name):
        raise NotImplementedError("getYData")
    def getXDataNames(self):
        raise NotImplementedError("getYDataNames")
