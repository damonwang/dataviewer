#!/usr/bin/python
"""
wx Printout class for MPlot
"""

import wx
from matplotlib.backends.backend_wx import RendererWx

class Printout(wx.Printout):
    def __init__(self, canvas, width=5,margin=0.25):
        wx.Printout.__init__(self,title='MPlot')
        self.canvas = canvas
        self.width  = width  # width, in inches of output figure (approximate)
        self.margin = margin
        
    def HasPage(self, page):
        return page == 1
    
    def GetPageInfo(self):
        return (1, 1, 1, 1)

    def OnPrintPage(self, page):
        dc        = self.GetDC()
        (ppw,pph) = self.GetPPIPrinter()  # printer's pixels per in
        (pgw,pgh) = self.GetPageSizePixels()  # page size in pixels
        (dcw,dch) = dc.GetSize()
        (grw,grh) = self.canvas.GetSizeTuple()
        
        # save current figure resolution, so we can reset it
        # to temporarily match the printers resolution
        
        bgcolor   = self.canvas.figure.get_facecolor()        
        fig_dpi   = self.canvas.figure.dpi.get()
        vscale    = ppw / fig_dpi

        # set figure resolution,bg color for printer
        self.canvas.figure.dpi.set(ppw)
        self.canvas.figure.set_facecolor('#FFFFFF')

        # draw bitmap scaled appropriately
        renderer  = RendererWx(self.canvas.bitmap, self.canvas.figure.dpi)
        self.canvas.figure.draw(renderer)
        self.canvas.bitmap.SetWidth( self.canvas.bitmap.GetWidth() * vscale)
        self.canvas.bitmap.SetHeight(self.canvas.bitmap.GetHeight()* vscale)
        self.canvas.draw()

        # page may need additional scaling on preview
        page_scale = 1.0
        if self.IsPreview():   page_scale = float(dcw)/pgw

        # print 'PrintPage: ', ppw, fig_dpi, vscale, page_scale

        # get margin in pixels = (margin in in) * (pixels/in)
        top_margin  = int(self.margin * pph * page_scale)
        left_margin = int(self.margin * ppw * page_scale)
        
        # set scale so that width of output is self.width inches
        # (assuming grw is size of graph in inches....)
        user_scale = (self.width * fig_dpi * page_scale)/float(grw)

        dc.SetDeviceOrigin(left_margin,top_margin)
        dc.SetUserScale(user_scale,user_scale)

        try:
            dc.DrawBitmap(self.canvas.bitmap, 0, 0)
        except:
            try:
                dc.DrawBitmap(self.canvas.bitmap, (0, 0))
            except:
                pass

        # restore original figure  resolution
        self.canvas.figure.set_facecolor(bgcolor)
        self.canvas.figure.dpi.set(fig_dpi)
        self.canvas.draw()

        return True
