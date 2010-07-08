from __future__ import print_function
import wx
import sys

class VarSelPanel(wx.Panel):
    '''Lets user set a variable from allowed options via dropdown-menu.

    At least one option must be provided to constructor!

    Attributes:
        var: variable controlled by this VarSelPanel
        options: options for this variable
        label: label to display to user
        dropdown: dropdown menu to display to user
        selection: choice made by user (None if user has not done anything)
        defchoice:  None means no default
                    non-None in options means use that option
                    non-None not in options means use first option
        sizer
    '''

    def __init__(self, parent, var, options, **kwargs):
        wx.Panel.__init__(self, parent=parent)

        self.var = var

        print(options, file=sys.stderr)

        dk = dict(sizerFlags=wx.SizerFlags().Border(), label="%s =" % var)
        dk.update(**kwargs)

        if 'defchoice' in kwargs:
            if dk['defchoice'] in options:
                self.selection = dk['defchoice']
            else:
                dk['defchoice'] = self.selection = options[0]

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.label = wx.StaticText(parent=self, label=dk['label'])
        self.sizer.AddF(item=self.label, flags=wx.SizerFlags().Center().Border())

        self.dropdown = wx.ComboBox(parent=self, style=wx.CB_READONLY,
                choices=options)
        if 'defchoice' in kwargs:
            self.dropdown.SetValue(self.selection)
        self.Bind(event=wx.EVT_COMBOBOX, handler=self.onEvtComboBox, 
                source=self.dropdown)
        self.sizer.AddF(item=self.dropdown, flags=wx.SizerFlags(1).Center())

        self.sizer.SetSizeHints(self)

        if 'sizer' in kwargs:
            dk['sizer'].AddF(item=self, flags=dk['sizerFlags'])

    def onEvtComboBox(self, event):
        '''sets attribute selection when user makes a choice'''

        self.selection = event.GetString()

    def setOptions(self, options, defchoice=None):

        self.dropdown.SetItems(options)
        oldoptions = self.dropdown.GetItems()

        if defchoice is None:
            if self.selection not in oldoptions:
                self.selection = options[0]
                self.dropdown.Select(0)
        elif defchoice in options:
            self.selection = defchoice
            self.dropdown.Select(self.dropdown.GetItems().index(defchoice))
        else:
            self.selection = options[0]
            self.dropdown.Select(0)

