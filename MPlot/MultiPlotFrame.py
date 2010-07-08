#!/usr/bin/python
##
## MPlot PlotFrame: a wx.Frame for 2D line plotting, using matplotlib
##

import os
import time
import wx
import matplotlib

from PlotPanel import PlotPanel

class MultiPlotFrame(wx.Frame):
    """
    MatPlotlib 2D plot as a wx.Frame, using PlotPanel
    """

    help_msg =  """MPlot PlotFrame quick help:

 Left-Click:   to display X,Y coordinates
 Left-Drag:    to zoom in on plot region
 Right-Click:  display popup menu with choices:
                Zoom out 1 level       (that is, to previous view)
                Zoom all the way out   (to full data range)
                --------------------
                Configure Plot
                Save Plot Image

Also, these key bindings can be used
(For Mac OSX, replace 'Ctrl' with 'Apple'):

  Ctrl-S:     save plot image to file
  Ctrl-C:     copy plot image to clipboard
  Ctrl-K:     Configure Plot 
  Ctrl-Q:     quit
"""

    about_msg =  """MPlot  version 0.7 
Matt Newville <newville@cars.uchicago.edu>"""

    def __init__(self, parent=None, rows=1,cols=1,
                 framesize=(600,350),
                 panelsize=(4.0,3.20),dpi=96,
                 exit_callback=None, **kwds):
        self.exit_callback = exit_callback
        self.title  = 'MPlot'
        self.parent = parent
        self.rows   = rows
        self.cols   = cols
        self.panelsize = panelsize
        self.dpi    = dpi
        self.panels = {}
        self.set_panel(0,0)
        self.__BuildFrame(size=framesize, **kwds)

    def write_message(self,s,panel=0):
        """write a message to the Status Bar"""
        self.SetStatusText(s, panel)

    def set_panel(self,ix,iy):
        self.current_panel = (ix,iy)
        
    def plot(self,x,y,panel=None,**kw):
        """plot after clearing current plot """
        if panel is None: panel = self.current_panel
        self.panels[panel].plot(x,y,**kw)
        
    def oplot(self,x,y,panel=None,**kw):
        """generic plotting method, overplotting any existing plot """
        if panel is None: panel = self.current_panel        
        self.panels[panel].oplot(x,y,**kw)

    def update_line(self,t,x,y,panel=None,**kw):
        """overwrite data for trace t """
        if panel is None: panel = self.current_panel        
        self.panels[panel].update_line(t,x,y,**kw)

    def set_xylims(self,xylims,panel=None,**kw):
        """overwrite data for trace t """
        if panel is None: panel = self.current_panel                
        self.panels[panel].set_xylims(xylims,**kw)

    def get_xylims(self,panel=None):
        """overwrite data for trace t """
        if panel is None: panel = self.current_panel                        
        return self.panels[panel].get_xylims()

    def clear(self,panel=None):
        """clear plot """
        if panel is None: panel = self.current_panel
        self.panels[panel].clear()

    def unzoom_all(self,event=None,panel=None):
        """zoom out full data range """
        if panel is None: panel = self.current_panel        
        self.panels[panel].unzoom_all(event=event)

    def unzoom(self,event=None,panel=None):
        """zoom out 1 level, or to full data range """
        if panel is None: panel = self.current_panel                
        self.panels[panel].unzoom(event=event)
        
    def set_title(self,s,panel=None):
        "set plot title"
        if panel is None: panel = self.current_panel
        self.panels[panel].set_title(s)
        
    def set_xlabel(self,s,panel=None):
        "set plot xlabel"
        if panel is None: panel = self.current_panel        
        self.panels[panel].set_xlabel(s)

    def set_ylabel(self,s,panel=None):
        "set plot xlabel"
        if panel is None: panel = self.current_panel        
        self.panels[panel].set_ylabel(s)        

    def save_figure(self,event=None,panel=None):
        """ save figure image to file"""
        if panel is None: panel = self.current_panel        
        self.panels[panel].save_figure(event=event)

    def configure(self,event=None,panel=None):
        if panel is None: panel = self.current_panel        
        self.panels[panel].configure(event=event)

    ####
    ##
    ## create GUI 
    ##
    ####
    def __BuildFrame(self, size=(500,350), **kwds):
        
        kwds['style'] = wx.DEFAULT_FRAME_STYLE
        kwds['size']  = size
        wx.Frame.__init__(self, self.parent, -1, self.title, **kwds)

        sbar = self.CreateStatusBar(2,wx.CAPTION|wx.THICK_FRAME)
        sfont = sbar.GetFont()
        sfont.SetWeight(wx.BOLD)
        sfont.SetPointSize(10)
        sbar.SetFont(sfont)

        self.SetStatusWidths([-3,-1])
        self.SetStatusText('',0)

        for i in range(self.rows):
            for j in range(self.cols):
                self.panels[(i,j)] = PlotPanel(self, self.parent,
                                               size=self.panelsize,
                                               dpi=self.dpi)
                self.panels[(i,j)].messenger = self.write_message

        self.__BuildMenu()
        self.Bind(wx.EVT_CLOSE,self.onExit)

        sizer = wx.GridBagSizer(self.rows,self.cols)
        for key,panel in self.panels.items():
            sizer.Add(panel,key,(1,1),flag=wx.EXPAND|wx.ALIGN_CENTER)

        for i in range(self.rows): sizer.AddGrowableRow(i)
        for i in range(self.cols): sizer.AddGrowableCol(i)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)
        
    def __BuildMenu(self):
        MENU_EXIT   = wx.NewId()        
        MENU_SAVE   = wx.NewId()
        MENU_CONFIG = wx.NewId()
        MENU_UNZOOM = wx.NewId()                
        MENU_HELP   = wx.NewId()
        MENU_ABOUT  = wx.NewId()
        MENU_PRINT  = wx.NewId()
        MENU_PSETUP = wx.NewId()
        MENU_PREVIEW= wx.NewId()
        MENU_CLIPB  = wx.NewId()

        menuBar = wx.MenuBar()
        
        f0 = wx.Menu()
        f0.Append(MENU_SAVE, "&Save\tCtrl+S",   "Save PNG Image of Plot")
        f0.Append(MENU_CLIPB, "&Copy\tCtrl+C",  "Copy Plot Image to Clipboard")
        f0.AppendSeparator()
        f0.Append(MENU_PSETUP, 'Page Setup...', 'Printer Setup')
        f0.Append(MENU_PREVIEW, 'Print Preview...', 'Print Preview')
        f0.Append(MENU_PRINT, "&Print\tCtrl+P", "Print Plot")
        f0.AppendSeparator()
        f0.Append(MENU_EXIT, "E&xit\tCtrl+Q", "Exit the MPlot Window")
        menuBar.Append(f0, "File")

        f1 = wx.Menu()
        f1.Append(MENU_CONFIG, "Configure Plot\tCtrl+K",
                  "Configure Plot styles, colors, labels, etc")
        f1.AppendSeparator()
        f1.Append(MENU_UNZOOM, "Zoom Out\tCtrl+Z",
                  "Zoom out to full data range")

        menuBar.Append(f1, "&Options")

        f2 = wx.Menu()
        f2.Append(MENU_HELP, "Quick Reference",  "Quick Reference for MPlot")
        f2.Append(MENU_ABOUT, "About", "About MPlot")

        menuBar.Append(f2, "&Help")

        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.onHelp,            id=MENU_HELP)
        self.Bind(wx.EVT_MENU, self.onAbout,           id=MENU_ABOUT)
        self.Bind(wx.EVT_MENU, self.onExit ,           id=MENU_EXIT)

        self.Bind(wx.EVT_MENU, self.configure,       id=MENU_CONFIG)
        self.Bind(wx.EVT_MENU, self.save_figure,     id=MENU_SAVE)
        self.Bind(wx.EVT_MENU, self.unzoom_all,      id=MENU_UNZOOM)
        self.Bind(wx.EVT_MENU, self.Printer_Print,   id=MENU_PRINT)        
        self.Bind(wx.EVT_MENU, self.Printer_Setup,   id=MENU_PSETUP)
        self.Bind(wx.EVT_MENU, self.Printer_Preview, id=MENU_PREVIEW)
        self.Bind(wx.EVT_MENU, self.Copy_to_Clipboard,  id=MENU_CLIPB)

    def configure(self,event=None):
        print  '  MENU_CONFIG '
        
    def save_figure(self,event=None):
        print  '  MENU_SAVE '
        
    def unzoom_all(self,event=None):
        print  '  MENU_UNZOOM '
        
    def Printer_Print(self,event=None):
        print  '  _PRINT)        '
        
    def Printer_Setup(self,event=None):
        print  '  _PSETUP '
        
    def Printer_Preview(self,event=None):
        print  '  PREVIEW '
        
    def Copy_to_Clipboard(self,event=None):
        print  '  CLIPB '
        
    def onAbout(self, event=None):
        dlg = wx.MessageDialog(self, self.about_msg, "About MPlot",
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def onHelp(self, event=None):
        dlg = wx.MessageDialog(self, self.help_msg, "MPlot Quick Reference",
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def onExit(self, event=None):
        try:
            if (callable(self.exit_callback)):  self.exit_callback()
        except:
            pass
        try:
            for p in self.panels.values():
                p.win_config.Close(True)
                p.win_config.Destroy()            
        except:
            pass

        try:
            self.Destroy()
        except:
            pass
        
