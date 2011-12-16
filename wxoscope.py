#!/usr/bin/env python
# encoding: utf-8
#===========================================================
#
# This file is part of PyOscope
#
# wxoscope.py
#
# 12-Sept-2011
# Copyright (c) 2011 Michael Hadmack (michael.hadmack@gmail.com)
#
# wxPython widget to display the data from a Scope object
#  A scope object is bound to the frame and Scope.update() calls
#  a listener ScopePlot.update() which will redraw when new data
#  becomes available.
#
# For now keep things simple (no autoscaling etc.)
#  one channel
#
# wx code comes from ws_scopegrab/MHStripChart.py
#===========================================================
import wx
import sys
import os
import numpy as np
try:
    import fel_pylib as utils
except:
    import utils
from wxPlotPanel import PlotPanel

DELAY = 100 #ms
DATA_ROOT = "/var/local/data"
COLOR1 = (1,1,0)
COLOR2 = (0,1,1)

class ScopePlot(PlotPanel):
    '''Display a matplotlib graph which automatically redraws when the data
        source calls its update method'''
    def __init__(self, parent, scope, **kwargs):
        self.parent = parent
        self.scope = scope
        self.tscale=1.0
        self.autoscaledata = True
        self.scope.grabData() # just to get things started
        self._updateflag = False
        
        PlotPanel.__init__(self, parent, **kwargs)
        
        # scope will run on_scope_update any time that its update() method is called
        self.scope.addListener(self.on_scope_update)
        self.Bind(wx.EVT_IDLE, self._onIdle)
    
    def _onIdle(self, e):
        PlotPanel._onIdle(self, e)
        if self._updateflag:
            self._updateflag = False
            self.draw()
        
    def draw(self):
        y1 = self.scope.getScaledWaveform(1)
        y2 = self.scope.getScaledWaveform(2)
        t_raw = self.scope.getTimeAxis()
        
        tdiv = t_raw[-1]-t_raw[0]/12 # assumes 12 division across scope
        if tdiv < 1e-6:
            xscale = 1e9
            xlabel = "Time (nsec)"
        elif tdiv < 1e-3:
            xscale = 1e6
            xlabel = "Time (usec)"
        elif tdiv < 1e1:
            xscale = 1e3
            xlabel = "Time (msec)"
        else:
            xscale = 1.0
            xlabel = "Time (sec)"
        
        self.tscale = xscale
        t = t_raw*self.tscale
        
        if not hasattr(self, 'ax1'):
            self.ax1 = self.figure.add_subplot(111)
            self.ax2 = self.ax1.twinx()
            self.figure.subplots_adjust(top=0.90, bottom=0.15, left=0.15, right=0.85, hspace=0.1)
            self.ax1.set_axis_bgcolor('black')
            self.ax1.grid(True, color='white')
            self.ax1.set_xlabel(xlabel)
            self.plot1, = self.ax1.plot(t,y1, linewidth=1, color=COLOR1)
            self.plot2, = self.ax2.plot(t,y2, linewidth=1, color=COLOR2)
            self.ax1.set_ylabel("Channel 1 (V)", color=COLOR1)
            self.ax2.set_ylabel("Channel 2 (V)", color=COLOR2)
            self.ax1.set_xbound(lower=t[0],upper=t[-1])
        else:
            self.plot1.set_xdata(t)
            self.plot1.set_ydata(y1)
            self.plot2.set_xdata(t)
            self.plot2.set_ydata(y2)
            if self.autoscaledata:
                self.ax1.set_xbound(lower=t[0],upper=t[-1])
                self.ax2.set_xbound(lower=t[0],upper=t[-1])
                self.ax1.set_xlabel(xlabel)
                self.ax1.relim()
                self.ax1.autoscale_view(tight=None, scalex=False, scaley=True)
                self.ax2.relim()
                self.ax2.autoscale_view(tight=None, scalex=False, scaley=True)
            self.canvas.draw()
        
    def on_scope_update(self, data):
        ''' When the data changes do something '''
        self._updateflag = True
        #self.draw()
        
    def setAutoscaling(self, onff=True):
        self.autoscaledata = onff
        
class ScopePlotTestFrame(wx.Frame):
    def __init__(self, scope):
        wx.Frame.__init__(self, None, -1, "Scope Plot Test")
        self.scope = scope
        self.running = False
        panel = wx.Panel(self,-1)
        
        # Setup up control panel
        control_panel = wx.Panel(panel, -1)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.createButton(control_panel, hbox1, 'Force', self.on_force)
        self.createButton(control_panel, hbox1, 'Run', self.on_run)
        self.createButton(control_panel, hbox1, 'Save', self.on_save)
        self.createButton(control_panel, hbox1, 'Save As', self.on_saveas)
        control_panel.SetSizer(hbox1)
        
        plot_panel = wx.Panel(panel, -1)
        #plot_panel.SetSize( (500,300) )
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.plot = ScopePlot(plot_panel, self.scope)
        vbox1.Add(self.plot, 0, wx.EXPAND)
        plot_panel.SetSizer(vbox1)
        
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(plot_panel, 1, flag=wx.GROW)        
        vbox2.Add(control_panel, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        panel.SetSizer(vbox2)
        vbox2.Fit(panel)

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

    def createButton(self, parent, sizer, label, action):
        if not hasattr(self, 'buttons'):
            self.buttons = {}
        btn = wx.Button(parent, -1, label)
        sizer.Add(btn,0)
        self.Bind(wx.EVT_BUTTON, action, btn)
        self.buttons[label] = btn
            
    def on_timer(self, e):
        self.scope.grabData()

    def on_force(self, e):
        self.scope.grabData()
        
    def on_run(self, e):
        if self.running:
            self.running = False
            self.timer.Stop()
            self.buttons["Run"].SetLabel("Run")
        else:
            self.running = True
            self.timer.Start(DELAY)
            self.buttons["Run"].SetLabel("Stop")

    def on_save(self, e):
        filepath = utils.makeDataFilePath(DATA_ROOT, 'oscope')
        print "Saving: " + filepath
        self.save(filepath)
    
    def on_saveas(self, e):
        header = ''
        filename = utils.makeFileName()
        dialog = wx.FileDialog(None, message="Save data", defaultDir=os.getcwd(),
                                defaultFile=filename, style=wx.SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            self.scope.writeWaveformToFile(filepath, header)
        dialog.Destroy() 
   
    def save(self,filename):
        header = ''
        self.scope.writeWaveformToFile(filename, header)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    try:
        device = sys.argv[1]
    except:
        device = 'rigol'
    if device == 'rigol':
        from rigol import RigolScope
        scope = RigolScope('/dev/usbtmc-rigol')
    elif device == 'waverunner':
        from waverunner import Waverunner
        scope = Waverunner('127.0.0.1')
    elif device == 'dummy':
         from oscope import DummyScope
         scope = DummyScope()

    app.frame = ScopePlotTestFrame(scope)
    app.frame.Show()
    app.MainLoop()
    
