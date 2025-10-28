#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : quickviewer.py
# Description : Segmentation Version Handler - Quick viewer.  
#
# Authors     : William A. Romero R.  <contact@waromero.com>,
#               Daniel Restrepo Q. <drones9182@gmail.com>,
#               Pablo Mesa H. <pablomesa08@gmail.com>
#-------------------------------------------------------------------------------
import wx
import numpy as np

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap, BoundaryNorm


from kernel import (
    SegVerTListManager,
    SegVerParser
)


default_cmap_colours = ["red", "green", "magenta", "yellow"]  
default_cmap = ListedColormap(default_cmap_colours)

#default_cmap.set_bad(color="black")

class NotificationCentre:
    """
    Register and respond notifications.
    Custom implementation of the Objective-C's NSNotificationCenter 
    by waromero.
    """

    _instance = None

    def __new__(cls):
        """
        Default class constructor.
        """
        if cls._instance is None:
            cls._instance = super(NotificationCentre, cls).__new__(cls)
            cls._instance._observers = {}
        return cls._instance


    def addObserver(self, observer, callback, aName):
        """
        Register an observer callback for a specific notification name.

        :param observer: A unique object identifying the observer, typically the instance itself (self).
        :param callback: A function handler that is called when the notification is posted.
        :param aName: A string representing the name of the notification to register for delivery to the observer.
        """
        if aName not in self._observers:
            self._observers[aName] = []
        if (observer, callback) not in self._observers[aName]:
            self._observers[aName].append((observer, callback))


    def removeObserver(self, observer, aName=None):
        """
        Remove observer for a specific notification or all notifications.

        :param observer: Observer object to remove.
        :param aName: Specific notification name.
        """
        if aName:
            self._observers[aName] = [
                (obs, cb) for (obs, cb) in self._observers.get(aName, []) if obs != observer
            ]
        else:
            for name in list(self._observers):
                self._observers[name] = [
                    (obs, cb) for (obs, cb) in self._observers[name] if obs != observer
                ]


    def postNotification(self, aName, data=None):
        """
        Post a notification to all registered observers.

        :param aName: Name of the notification.
        :param data: Optional object(data) to send with the notification.
        """
        for observer, callback in self._observers.get(aName, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Error notifying {observer}: {e}")


class VolumeListPanel(wx.Panel):
    """
    Displays a list of volumes.
    """
    def __init__(self, parent):
        """
        Default constructor.
        """
        super().__init__(parent)
        self.volumeListBox = wx.ListBox(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.volumeListBox, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        self.notificationCentre = NotificationCentre()
        self.volumeListBox.Bind(wx.EVT_LISTBOX, self.OnItemSelected)


    def UpdateVolumeList(self, volumeList):
        """
        Update the list box with a list of items.
        """
        if not isinstance(volumeList, list):
            raise ValueError("update expects a list of strings")
        
        self.volumeListBox.Set(volumeList)


    def OnItemSelected(self, event):
        """
        Return the currently selected item as a string.
        """
        selectionIndex = self.volumeListBox.GetSelection()

        if selectionIndex == wx.NOT_FOUND:
            return None
        
        selectionStr = self.volumeListBox.GetString(selectionIndex)

        self.notificationCentre.postNotification( "VOLUME_SELECTED", 
                                                  data=selectionIndex )


class MatplotlibPanel(wx.Panel):
    """
    Matplotlib instance to display volume+segmentation.
    """
    def __init__(self, parent):
        """
        Default constructor.
        """
        super().__init__(parent)

        self.figure = Figure()
        self.figure.set_facecolor("black")
        self.axes = self.figure.add_subplot()
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.axes.set_xticks( [] )
        self.axes.set_yticks( [] )

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)


    def AddVolume(self, volume):
        """
        Display a volume.
        """
        if not isinstance(volume, np.ndarray):
            raise ValueError("Volume must be a NumPy ndarray")
        
        self.axes.imshow( volume, 
                          cmap = "gray", 
                          interpolation = "bicubic",
                          origin = "upper")
        
        self.axes.set_xticks( [] )
        self.axes.set_yticks( [] )
        
        self.canvas.draw()


    def AddSegmentation(self, segmentation):
        """
        Overlay segmentation.
        """
        if not isinstance(segmentation, np.ndarray):
            raise ValueError("Segmentation must be a NumPy ndarray")
        
        segmentation = segmentation.astype(float)
        segmentation[segmentation == 0] = np.nan

        self.axes.imshow( segmentation, 
                        #   cmap = 'hsv',
                          cmap = default_cmap,
                          vmin=1, vmax=4,
                          alpha = 0.27,
                          origin = "upper")
        
        self.axes.set_xticks( [] )
        self.axes.set_yticks( [] )
        
        self.canvas.draw()


    def ResetDisplay(self):
        """
        Clear the current display.
        """
        self.axes.clear()
        self.canvas.draw()


class ViewerPanel(wx.Panel):
    """
    Panel that holds a slider and a MatplotlibPanel.
    """
    def __init__(self, parent):
        """
        Default constructor.
        """
        super().__init__(parent)

        self.cmin = 1
        self.cmax = 20
        self.slice_idx = 10

        self.volume = np.zeros([self.cmax,128,128])
        self.segmentation = np.zeros([self.cmax,128,128])

        self.slider = wx.Slider( self, style = wx.SL_HORIZONTAL | wx.SL_LABELS,
                                 minValue = self.cmin, 
                                 maxValue = self.cmax, 
                                 value = self.slice_idx )
        
        self.slider.Bind(wx.EVT_SLIDER, self.OnSliderChanged)

        self.plot_panel = MatplotlibPanel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.slider, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.plot_panel, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        self.Fit()

        self.__volSegTListManager = SegVerTListManager()

        self.notificationCentre = NotificationCentre()
        self.notificationCentre.addObserver(self, self.OnVolumeSelected, "VOLUME_SELECTED")

        self.UpdateSlider()
        self.UpdateVolSegViewer()


    def SetSegVerTListManager(self, vsTListManager:SegVerTListManager):
        """
        Default.
        """
        self.__volSegTListManager = vsTListManager


    def UpdateSlider(self):
        """
        Update maxValue and current slice value.
        """
        self.slider.SetMax(self.cmax)
        self.slider.SetValue(self.slice_idx)
        self.slider.Update()


    def UpdateVolSegViewer(self):
        """
        Update Volume+Segmentation visualisation.
        """
        self.plot_panel.axes.clear()
        self.plot_panel.AddVolume(self.volume[self.slice_idx-1,:,:])
        self.plot_panel.AddSegmentation(self.segmentation[self.slice_idx-1,:,:])    


    def OnVolumeSelected(self, itemIndex):
        """
        Default.
        """
        self.volume = self.__volSegTListManager.get_volume_array(itemIndex)
        self.segmentation = self.__volSegTListManager.get_segmentation_array(itemIndex)

        slices = self.volume.shape[0]

        central_slice = int(slices/2)

        self.cmax = slices
        self.slice_idx = central_slice

        self.UpdateSlider()
        self.UpdateVolSegViewer()


    def OnSliderChanged(self, event):
        """
        Handle slider change event.
        """
        self.slice_idx = self.slider.GetValue()
        self.UpdateVolSegViewer()


class QuickViewerFrame(wx.Frame):
    """
    Main application window containing VolumeListPanel and ViewerPanel.
    """

    def __init__(self):
        """
        Default constructor.
        """
        super().__init__(None, title="Volumen-Segmentation Sync :: Quick viewer", size=(900, 600))

        splitter = wx.SplitterWindow(self)

        self.volume_list_panel = VolumeListPanel(splitter)
        self.viewer_panel = ViewerPanel(splitter)

        splitter.SplitVertically(self.volume_list_panel, self.viewer_panel, sashPosition=300)
        splitter.SetMinimumPaneSize(100)

        self.Centre()
        self.Show()


    def SetSegVerTListManager(self, vsTListManager:SegVerTListManager):
        """
        Set/Update volume list.
        """
        self.viewer_panel.SetSegVerTListManager(vsTListManager)
        self.volume_list_panel.UpdateVolumeList(vsTListManager.get_vol_name_list())


class QuickViewer(wx.App):
    """
    Volumen-Segmentation - Quick viewer.
    """
    def __init__(self, INPUT_SEGVERSYNC_DIRECTORY_PATH):
        """
        Default constructor.
        """
        self.directoryPath = INPUT_SEGVERSYNC_DIRECTORY_PATH
        super(QuickViewer, self).__init__()


    def OnInit(self):
        """
        Start me up!
        """
        frame = QuickViewerFrame()

        volsegParser = SegVerParser(self.directoryPath)

        volSegTListManager = volsegParser.get_SegVerTListManager()

        frame.SetSegVerTListManager(volSegTListManager)

        frame.Centre()
        frame.Show(True)

        return True


#-------------------------------------------------------------------------------


if __name__ == '__main__':
    INPUT_DIRECTORY = "C:\\Users\\walbe\\WORKSPACE\\CARIM_CENTRE02"
    app = QuickViewer(INPUT_DIRECTORY)
    app.MainLoop()
