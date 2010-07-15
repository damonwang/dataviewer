import wx
import sys
import os

from WxUtil import *
from Exceptions import *
from Epics1DSheet import Epics1DSheet
from Epics2DSheet import Epics2DSheet

class Frame(wx.Frame):
    '''straight inherited from wx.Frame, but created in case I need to
    customize it later.'''
    pass

#------------------------------------------------------------------------------

class MainFrame(Frame):
    '''The main viewer frame.

    Attributes:
        panel: main panel
        sizer: sizer for panel, holding nb
        nb: holds one data file per page
        datasheets: holds open DataSheets
        visibleDS: Datasheet shown in right pane
        statusbar
        menubar
    
    '''


    def __init__(self, *args, **kwargs):
        '''Arguments get passed directly to Frame.__init__(). Creates
        statusbar, menubar, and a single full-size panel.'''

        Frame.__init__(self, *args, **kwargs)

        self.datasheets = []

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.sizer)

        self.splitW = wx.SplitterWindow(parent=self.panel,
                style=wx.SP_3D)
        self.sizer.AddF(item=self.splitW, flags=wx.SizerFlags(1).Expand())

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("statusbar", 0)

        self.menubar = createMenuBar(setInto=self, menubar=self.configMenuBar())


        self.tree = wx.TreeCtrl(parent=self.splitW, 
                style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.BORDER_NONE)
        self.tree.AddRoot(text="root")
        self.tree.Bind(event=wx.EVT_TREE_SEL_CHANGED, handler=self.onTreeItemActivated)

        self.visibleDS = self.blankPanel = wx.Panel(self.splitW)
        self.splitW.SplitVertically(window1=self.tree, window2=self.visibleDS) 
        self.tree.SetMinSize(self.tree.GetSize())

        self.sizer.SetSizeHints(self)
        self.panel.Layout()


    def OnClickFileOpen(self, event):
        '''Event handler that asks for a file, creates an edit window
        (StyledTextCtrl), and reads the file into that window.'''

        dlg = wx.FileDialog(parent=self, message="Choose a data file",
            defaultDir=os.getcwd(), style=wx.OPEN | wx.CHANGE_DIR | wx.MULTIPLE)

        ds = None
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                ds = self.openDataSheet(path)
        dlg.Destroy()

        #if ds is not None and ds != self.splitW.GetWindow2():
        #    self.showRightPane(ds)

        #print("\n".join(_reportPedigree(self)), file=sys.stderr)

        self.sizer.SetSizeHints(self)
        self.sizer.Layout()

    def configMenuBar(self):
        '''returns suitable createMenuBar input for the desired menu bar'''

        filemenu = ("&File", [])
        filemenu[1].append(dict(id=-1, text="&Open", help="Open a data file",
            handler=self.OnClickFileOpen))

        return [filemenu]

    def showRightPane(self, pane):
        '''sets pane as the right-hand window of the SplitterWindow. Does not
        destroy the current right-hand pane, just removes it.'''

        old, self.visibleDS = self.splitW.GetWindow2(), pane
        self.splitW.ReplaceWindow(winNew=self.visibleDS, winOld=old)
        old.Hide()
        pane.Show()
        self.Layout()

    def onTreeItemActivated(self, event):
        '''when user clicks on a DataSheet's item in the tree, show that DataSheet.'''

        self.showRightPane(self.tree.GetItemPyData(event.GetItem()))
        self.sizer.SetSizeHints(self)
        self.Layout()

    def openDataSheet(self, path):
        '''identifies the filetype, creates the DataSheet, adds it to the tree, and shows it.'''

        # TODO this should be pushed down into the DataSheet constructor
        if not os.path.isfile(path):
            wx.MessageBox(caption="File not found", 
                    message="file %s not found, not opened." % path)
            return

        item=self.tree.AppendItem(parent=self.tree.GetRootItem(), 
                text=os.path.basename(path))
        self.tree.Fit()

        ds = None
        for filetype in [Epics1DSheet, Epics2DSheet]:
            try:
                ds = filetype(parent=self.splitW, filename=path, treeItem=item,
                        writeOut=lambda s: self.statusbar.SetStatusText(s, 0),
                        writeErr=lambda s: self.statusbar.SetStatusText(s, 0))
                break;
            except FileTypeError:
                pass
        if ds is not None:
            self.datasheets.append(ds)
            self.tree.SetItemPyData(item=item, obj=ds)
            self.tree.SelectItem(item=item)
        else:
            self.tree.Delete(item)
            wx.MessageBox("could not recognize filetype")

        return ds

