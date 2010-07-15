import wx

padding = 5
axes = ["X", "Y"]

def twiddleSize(dest):
    '''sends dest a useless wx.SizeEvent, to fix some bugs I don't understand.'''
    size = dest.GetSize()
    anotherSize = (size[0]+1,size[1])
    dest.GetEventHandler().ProcessEvent(event=wx.SizeEvent(sz=anotherSize))
    dest.GetEventHandler().ProcessEvent(event=wx.SizeEvent(sz=size))

def createButton(handler, parent, label, sizer, flags=wx.SizerFlags().Border(), **kwargs):
    '''creates a button with parent and label, binds to handler, and adds to
    sizer with flags. Additional args go to Button constructor.
    
    Returns: a wx.Button'''

    rv = wx.Button(parent=parent, label=label, **kwargs)
    rv.Bind(event=wx.EVT_BUTTON, handler=handler)
    sizer.AddF(item=rv, flags=flags)
    return rv

def createMenuBar(menubar, setInto=None):
    '''creates a menubar and optionally attaches it to something

    a menubar is a list of menus.

    Args:
        setInto: something with a SetMenuBar method
        menubar: see above

    Returns: a wx.Menubar'''

    rv = wx.MenuBar()
    for menu in menubar:
        m = createMenu(menu=menu, container=setInto)
        rv.Append(menu=m, title=menu[0])

    if setInto is not None:
        setInto.SetMenuBar(rv)

    return rv

def createMenu(menu, container, setInto=None):
    '''creates a menu and optionally attaches it to a wx.MenuBar

    a menu is described by a 2-tuple whose
        first element is a title suitable for wx.Menu()
        second element is a list of tuples and dicts:
            lists represent submenus
            dicts represent menu items

    a menu item is represented by a dict suitable for **kwargs expansion into
    wx.Menu.Append().

    Args:
        menu: see above
        setInto: a wx.MenuBar to attach the result to

    Returns: a wx.Menu'''

    rv = wx.Menu()
    for item in menu[1]:
        if isinstance(item, tuple):
            rv.AppendMenu(text=item[0], submenu=createMenu(item))
        elif isinstance(item, dict):
            handler = item["handler"]
            del item["handler"]
            m = rv.Append(**item)
            container.Bind(event=wx.EVT_MENU, handler=handler, source=m)
        else:
            raise TypeError(item)
    
    if setInto is not None:
        setInto.Append(menu=rv, title=menu[0])

    return rv

def reportPedigree(self):
    '''returns tree-like output describing parent-child relationships below the given window.
    
    Args: 
        self: window to start reporting at
        
    Returns:
        string with tree-like pedigree'''


    return ["%s%s" % (("(hidden) ", "")[self.IsShown()], self)] + sum( 
            [ map(lambda s: "  " + s, reportPedigree(child))
                    for child in self.Children if "Children" in dir(child)
            ], [])
        

