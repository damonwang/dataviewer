#!/usr/bin/python
##
## MPlot ImagePanel: a wx.Panel for Image plotting, using matplotlib
##

import sys
import time
import os
import wx
import numpy

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

from ImageConfig import ImageConfig, ImageGUIConfig

# from Printout  import Printout
class ImagePanel(wx.Panel):
    """
    MatPlotlib Image on a wx.Panel, suitable for embedding
    in any wx.Frame.

    This does provide a right-click popup
    menu for configuration, zooming, saving an image of the
    figure, and Ctrl-C for copy-image-to-clipboard.

    For more features, see PlotFrame, which embeds a PlotPanel
    and also provides, a Menu, StatusBar, and Printing support.
    """

    help_msg =  """MPlot quick help:

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

    def __init__(self, parent, messenger=None,
                 size=(6.00,3.70), dpi=96, **kwds):

        self.is_macosx = False
        if os.name == 'posix':
            if os.uname()[0] == 'Darwin': self.is_macosx = True

        matplotlib.rc('axes', axisbelow=True)
        matplotlib.rc('lines', linewidth=2)
        matplotlib.rc('xtick',  labelsize=11, color='k')
        matplotlib.rc('ytick',  labelsize=11, color='k')
        matplotlib.rc('grid',  linewidth=0.5, linestyle='-')

        self.messenger = messenger
        if (messenger is None): self.messenger = self.__def_messenger

        self.conf = ImageConfig()
        self.cursor_mode='cursor'

        self.launch_dir  = os.getcwd()
        self.mouse_uptime= time.time()
        self.last_event_button = None

        self.view_lim  = (None,None,None,None)
        self.zoom_lims = [self.view_lim]
        self.old_zoomdc= (None,(0,0),(0,0))

        self.parent    = parent

        self._yfmt = '%.4f'
        self._xfmt = '%.4f'

        self.figsize = size
        self.dpi     = dpi
        self.__BuildPanel(**kwds)

    def display(self,data,**kw):
        """
        display (that is, create a new image display on the current frame
        """
        print 'display: '
        c = self.axes.imshow(data)
        print c.cmap
        
    def overlay(self,data,**kw):
        print ' overlay ? '
        self.axes.imshow(data)
        

    def clear(self):
        """ clear plot """
        print 'clear'

    def unzoom_all(self,event=None):
        """ zoom out full data range """
        print 'unzoom all'
        self.unzoom(event)
        
    def unzoom(self,event=None):
        """ zoom out 1 level, or to full data range """
        print 'unzoom '
        
    def set_title(self,s):
        "set plot title"
        self.conf.title = s
        self.conf.relabel()
        
    def set_xlabel(self,s):
        "set plot xlabel"
        self.conf.xlabel = s
        self.conf.relabel()

    def set_ylabel(self,s):
        "set plot ylabel"
        self.conf.ylabel = s
        self.conf.relabel()

    def write_message(self,s,panel=0):
        """ write message to message handler (possibly going to GUI statusbar)"""
        self.messenger(s, panel=panel)

    def save_figure(self,event=None):
        """ save figure image to file"""
        file_choices = "PNG (*.png)|*.png|EPS (*.eps)|*.eps" 
        
        dlg = wx.FileDialog(self, message='Save Plot Figure as...',
                            defaultDir = os.getcwd(),
                            defaultFile='plot.png',
                            wildcard=file_choices,
                            style=wx.SAVE|wx.CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path,dpi=300)
            if (path.find(self.launch_dir) ==  0):
                path = path[len(self.launch_dir)+1:]
            self.write_message('Saved plot to %s' % path)

    def configure(self,event=None):
        try:
            self.win_config.Raise()
        except:
            self.win_config = GUIImageConfig(self.conf)
    ####
    ## create GUI 
    ####
    def __BuildPanel(self, **kwds):
        """ builds basic GUI panel and popup menu"""
        wx.Panel.__init__(self, self.parent, -1, **kwds)

        self.fig   = Figure(self.figsize,dpi=self.dpi)
        self.axes  = self.fig.add_axes([0.15,0.15,0.75,0.75],
                                       axisbg='#FEFEFE')
                                      
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)
        self.fig.set_facecolor('#FBFBF8')

        self.conf.fig   = self.fig
        self.conf.canvas= self.canvas

        self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

        # This way of adding to sizer allows resizing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 2, wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND,0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.Fit()

        # define zoom box properties
        self.zoombrush = wx.Brush('#333333',  wx.TRANSPARENT)
        self.zoompen   = wx.Pen('#FFAA99', 2, wx.LONG_DASH)

        # use matplotlib events
        self.canvas.mpl_connect("motion_notify_event",  self.__onMouseMotionEvent)
        self.canvas.mpl_connect("button_press_event",   self.__onMouseButtonEvent)
        self.canvas.mpl_connect("button_release_event", self.__onMouseButtonEvent)
        self.canvas.mpl_connect("key_press_event",      self.__onKeyEvent)

        # build pop-up menu for right-click display
        self.popup_unzoom_all = wx.NewId()        
        self.popup_unzoom_one = wx.NewId()
        self.popup_config     = wx.NewId()
        self.popup_save   = wx.NewId()        
        self.popup_menu = wx.Menu()
        self.popup_menu.Append(self.popup_unzoom_one, 'Zoom out 1 level')
        self.popup_menu.Append(self.popup_unzoom_all, 'Zoom all the way out')
        self.popup_menu.AppendSeparator()
        self.popup_menu.Append(self.popup_config,'Configure Plot')
        self.popup_menu.Append(self.popup_save,  'Save Plot Image')
        
        self.Bind(wx.EVT_MENU, self.unzoom,     id=self.popup_unzoom_one)
        self.Bind(wx.EVT_MENU, self.unzoom_all, id=self.popup_unzoom_all)
        self.Bind(wx.EVT_MENU, self.save_figure,id=self.popup_save)
        self.Bind(wx.EVT_MENU, self.configure,  id=self.popup_config)

    ####
    ##
    ## GUI events
    ##
    ####
    def onLeftDown(self,event=None):
        """ left button down: report x,y coords, start zooming mode"""
        if event == None: return
        print 'Left Down', dir(event)
        # print dir(event.guiEvent)
        self.conf.zoom_x = event.x
        self.conf.zoom_y = event.y
        if (event.inaxes != None):
            self.conf.zoom_init = (event.xdata, event.ydata)
            fmt = "X,Y= %s, %s" % (self._xfmt, self._yfmt)
            self.write_message(fmt % (event.xdata,event.ydata), panel=1)
        else:
            self.conf.zoom_init = self.axes.transData.inverse_xy_tup((event.x, event.y))

        self.cursor_mode = 'zoom'
        self.__drawZoombox(self.old_zoomdc)
        self.old_zoomdc = (None, (0,0),(0,0))                                  

    def onLeftUp(self,event=None):
        """ left button up: zoom in on selected region?? """
        print ' left up ', event
        if event == None: return        
        dx = abs(self.conf.zoom_x - event.x)
        dy = abs(self.conf.zoom_y - event.y)
        t0 = time.time()
        if ((dx > 6) and (dy > 6) and (t0-self.mouse_uptime)>0.1 and
            self.cursor_mode == 'zoom'):
            self.mouse_uptime = t0
            if (event.inaxes != None):
                _end = (event.xdata,event.ydata)
            else: # allows zooming in to go slightly out of range....
                _end = self.axes.transData.inverse_xy_tup((event.x, event.y))
            try:
                _ini = self.conf.zoom_init
                _lim = (min(_ini[0],_end[0]),max(_ini[0],_end[0]),
                        min(_ini[1],_end[1]),max(_ini[1],_end[1]))

                self.set_xylims(_lim, autoscale=False)
                self.zoom_lims.append(self.view_lim)
                self.view_lim = _lim
                txt = 'zoom level %i ' % (len(self.zoom_lims)-1)
                
                self.write_message(txt)
            except:
                self.write_message("Cannot Zoom")
        self.old_zoomdc = (None,(0,0),(0,0))
        self.cursor_mode = 'cursor'
        self.canvas.draw()

    def onRightDown(self,event=None):
        """ right button down: show pop-up"""
        if event == None: return      
        self.cursor_mode = 'cursor'
        # note that the matplotlib event location have to be converted
        # back to the wxWindows event location...
        # this undoes what happens in FigureCanvasWx.wrapper(event)
        location = wx.Point(event.x, self.fig.bbox.height()-event.y)
        self.PopupMenu(self.popup_menu,location)

    def onRightUp(self,event=None):
        """ right button up: put back to cursor mode"""
        self.cursor_mode = 'cursor'
        

    ####
    ##
    ## private methods
    ##
    ####
    def __def_messenger(self,s,panel=0):
        """ default, generic messenger: write to stdout"""
        sys.stdout.write(s)


    def __date_format(self,x):
        """ formatter for date x-data. primitive, and probably needs
        improvement, following matplotlib's date methods.        

        """
        span = self.axes.xaxis.get_view_interval().span()
        ticks = self.axes.xaxis.get_major_locator()()
        fmt = "%m/%d "                        

        if   span < 1800:     fmt = "%I%p \n%M:%S"
        elif span < 86400*5:  fmt = "%m/%d \n%H:%M"
        elif span < 86400*20: fmt = "%m/%d"
        # print 'date formatter  span: ', span, fmt
        s = time.strftime(fmt,time.localtime(x))
        return s
        
    def __xformatter(self,x,pos):
        " x-axis formatter "
        if self.use_dates:
            return self.__date_format(x)
        else:
            return self.__format(x,type='x')
    
    def __yformatter(self,y,pos):
        " y-axis formatter "        
        return self.__format(y,type='y')

    def __format(self, x, type='x'):
        """ home built tick formatter to use with FuncFormatter():
        x     value to be formatted
        type  'x' or 'y' to set which list of ticks to get

        also sets self._yfmt/self._xfmt for statusbar
        """
        fmt,v = '%1.5g','%1.5g'
        if type == 'y':
            ax = self.axes.yaxis
        else:
            ax = self.axes.xaxis
            
        try:
            dtick = 0.1 * ax.get_view_interval().span()
        except:
            dtick = 0.2
        try:
            ticks = ax.get_major_locator()()
            dtick = abs(ticks[1] - ticks[0])
        except:
            pass
        # print ' tick ' , type, dtick, ' -> ', 
        if   dtick > 99999:     fmt,v = ('%1.6e', '%1.7g')
        elif dtick > 0.99:      fmt,v = ('%1.0f', '%1.2f')
        elif dtick > 0.099:     fmt,v = ('%1.1f', '%1.3f')
        elif dtick > 0.0099:    fmt,v = ('%1.2f', '%1.4f')
        elif dtick > 0.00099:   fmt,v = ('%1.3f', '%1.5f')
        elif dtick > 0.000099:  fmt,v = ('%1.4f', '%1.6e')
        elif dtick > 0.0000099: fmt,v = ('%1.5f', '%1.6e')


        s =  fmt % x
        s.strip()
        s = s.replace('+', '')
        while s.find('e0')>0: s = s.replace('e0','e')
        while s.find('-0')>0: s = s.replace('-0','-')
        if type == 'y': self._yfmt = v
        if type == 'x': self._xfmt = v
        return s

    def __drawZoombox(self,dc):
        """ system-dependent hack to call wx.ClientDC.DrawRectangle
        with the right arguments"""
        if dc[0] == None: return
        pos  = dc[1]
        size = dc[2]
        dc[0].DrawRectangle(pos[0],pos[1],size[0],size[1])

        return (None, (0,0),(0,0))

    def __onKeyEvent(self,event=None):
        """ handles key events on canvas
        """
        if event == None: return
        key = event.guiEvent.GetKeyCode()
        if (key < wx.WXK_SPACE or  key > 255):  return
        mod  = event.guiEvent.ControlDown()
        ckey = chr(key)
        if self.is_macosx: mod = event.guiEvent.MetaDown()
        if (mod and ckey=='C'): self.canvas.Copy_to_Clipboard(event)
        if (mod and ckey=='S'): self.save_figure(event)
        if (mod and ckey=='K'): self.configure(event)
        if (mod and ckey=='Z'): self.unzoom_all(event)
        if (mod and ckey=='P'): self.canvas.Printer_Print(event)
        
    def __onMouseButtonEvent(self,event=None):
        """ general mouse press/release events. Here, event is
        a MplEvent from matplotlib.  This routine just dispatches
        to the appropriate onLeftDown, onLeftUp, onRightDown, onRightUp....
        methods.
        """
        if event == None: return
        button = event.button or self.last_event_button
        if (button == None): button = 1

        if button == 1:
            if event.name  == 'button_press_event':
                self.onLeftDown(event)
            elif event.name  == 'button_release_event':
                self.onLeftUp(event)
        elif button == 3:
            if event.name  == 'button_press_event':
                self.onRightDown(event)
            elif event.name  == 'button_release_event':
                self.onRightUp(event)
        self.last_event_button = button

    def __onMouseMotionEvent(self, event=None):
        """Draw a cursor over the axes"""
        if event == None: return
        if (self.cursor_mode != 'zoom'): return            
        try:
            x, y  = event.x, event.y
        except:
            self.cursor_mode == 'cursor'
            retrun
        self.__drawZoombox(self.old_zoomdc)
        self.old_zoomdc = (None, (0,0),(0,0))            

        x0     = min(x, self.conf.zoom_x)
        ymax   = max(y, self.conf.zoom_y)
        width  = abs(x -self.conf.zoom_x)
        height = abs(y -self.conf.zoom_y)
        y0     = self.canvas.figure.bbox.height() - ymax

        zdc = wx.ClientDC(self.canvas)
        zdc.SetBrush(self.zoombrush)
        zdc.SetPen(self.zoompen)
        zdc.SetLogicalFunction(wx.XOR)
        self.old_zoomdc = (zdc, (x0, y0), (width, height))
        self.__drawZoombox(self.old_zoomdc)

