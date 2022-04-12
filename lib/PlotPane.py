'''
    PlotPane:

    This pane is a ttk.Notebook with a matplotlib plot on each page. SimPages plot() function is passed this object,
    and can add tabs to the notebook to make additional figures.
'''

import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import matplotlib.figure as figure
import matplotlib.style as plotstyle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
import mplcursors
from orhelper import FlightDataType, FlightEvent
from .orhelperhelper import DataTypeMap, EventTypeMap, ExtendedDataType
import matplotlib.transforms as transforms
from .units import units

linestyle_tuple = [
     'solid',
     'dotted',    # Same as (0, (1, 1)) or ':'
     'dashed',    # Same as '--'
     'dashdot',  # Same as '-.'
     (0, (1, 10)),
     (0, (1, 1)),
     (0, (1, 1)),
     (0, (5, 10)),
     (0, (5, 5)),
     (0, (5, 1)),
     (0, (3, 10, 1, 10)),
     (0, (3, 5, 1, 5)),
     (0, (3, 1, 1, 1)),
     (0, (3, 5, 1, 5, 1, 5)),
     (0, (3, 10, 1, 10, 1, 10)),
     (0, (3, 1, 1, 1, 1, 1))]

class PlotPane(ttk.Notebook):
    def __init__(self, root):
        super().__init__(root)

        self.current_tab = 0
        self.figs = []
        self.canvases = []
        self.toolbars= []
        self.names = []
        self.axes = []
        self.legends = []
        self.datatypes = []

        self.sim = None

        self.image = plt.imread("lib/ssi-logo.png")

        self.selectors = []

        self.event_names = [EventTypeMap[key] for key in EventTypeMap]
        self.event_keys = list(EventTypeMap.keys())

        plt.style.use('classic')

        ## Add a default page with empty plot
        self.make_default()

    def make_default(self):
        self.add_page('Altitude/Velocity',[FlightDataType.TYPE_ALTITUDE],[FlightDataType.TYPE_VELOCITY_Z])
        self.add_page('Static Margin/Damping',[FlightDataType.TYPE_STABILITY],[ExtendedDataType.TYPE_DAMPING_RATIO])
        self.add_page('AOA/Natural Frequency',[FlightDataType.TYPE_AOA],[ExtendedDataType.TYPE_NATURAL_FREQUENCY])
        self.add_page('Fin Flutter/Char Oscillation',[FlightDataType.TYPE_VELOCITY_TOTAL,ExtendedDataType.TYPE_FLUTTER_VELOCITY_FG,ExtendedDataType.TYPE_FLUTTER_VELOCITY_CF],[ExtendedDataType.TYPE_CHAR_OSCILLATION_DISTANCE])
        # for ax_pair in self.axes:
        #     ax_pair[0].imshow(self.image,cmap='gray')
        self.draw_all()

    def set_page(self, index = 0):
        ''' Set which page to look at. '''
        self.select(index)
    
    def add_page(self, page_title,leftkeys,rightkeys):
        ''' Make a new plotting page. Returns the figure.Figure() object on that page.'''
        frame = ttk.Frame(self) # make frame to hold canvas
        canvasframe = ttk.Frame(frame)
        self.figs.append(figure.Figure())
        ax1 = self.figs[-1].add_subplot(1,1,1)
        self.figs[-1].subplots_adjust(right=0.8)
        ax2 = ax1.twinx()
        self.axes.append([ax1, ax2])
        self.names.append(page_title)
        self.datatypes.append([leftkeys, rightkeys])
        self.legends.append(None)

        my_ind = len(self.names)-1
        leftunit = units.get_preferred_unit(DataTypeMap[leftkeys[0]].unit)
        leftselvar = tk.StringVar(frame,value=leftunit)
        leftselector = ttk.OptionMenu(frame,leftselvar,leftunit,*tuple(units.get_compatible_units(leftunit)))
        rightunit = units.get_preferred_unit(DataTypeMap[rightkeys[0]].unit)
        rightselvar = tk.StringVar(frame)
        rightselector = ttk.OptionMenu(frame,rightselvar,rightunit,*tuple(units.get_compatible_units(rightunit)))
        eventselector = tk.Listbox(frame,selectmode='multiple',exportselection=False)
        update_listbox(eventselector,[EventTypeMap[key] for key in EventTypeMap])
        events_to_plot = [FlightEvent.APOGEE, FlightEvent.BURNOUT, FlightEvent.LAUNCHROD]
        for event in events_to_plot:
            eventselector.select_set(list(EventTypeMap.keys()).index(event))
        eventselector.bind('<<ListboxSelect>>',lambda *args: self.update(my_ind,True))
        rightselvar.trace_add(mode='write',callback=lambda *args : self.update(my_ind))
        leftselvar.trace_add(mode='write',callback=lambda *args : self.update(my_ind))
        self.selectors.append([leftselvar, rightselvar, eventselector])

        self.canvases.append(FigureCanvasTkAgg(self.figs[-1], master = canvasframe))
        self.canvases[-1].get_tk_widget().pack(expand=True, fill=tk.BOTH)
        self.toolbars.append( NavigationToolbar2Tk(self.canvases[-1], canvasframe) )
        self.toolbars[-1].update()

        ttk.Label(frame,text='Left Axis Unit').grid(row=0,column=0,sticky='nsew')
        leftselector.grid(row=0,column=1,sticky='nsew')
        ttk.Label(frame,text='Right Axis Unit').grid(row=0,column=2,sticky='nsew')
        rightselector.grid(row=0,column=3,sticky='nsew')
        eventselector.grid(row=0,column=4,sticky='nsew')
        canvasframe.grid(row=1,column=0,columnspan=5,sticky='nsew')
        frame.columnconfigure(4,weight=1)
        frame.rowconfigure(1,weight=1)
        self.add(frame, text = page_title)

    def update_sim(self,newsim):
        self.sim = newsim

    def update_all(self):
        for i in range(len(self.names)):
            self.update(i)

    def update(self, index = None, keep_lims=False):
        def plot_events(ax):
            events = self.sim.events[0]
            names = [EventTypeMap[key] for key in events]
            events_to_plot = [self.selectors[index][2].get(x) for x in self.selectors[index][2].curselection()]
            trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
            for plotevent in events_to_plot:
                if plotevent in names:
                    etime = events[self.event_keys[self.event_names.index(plotevent)]]
                    for etime_i in etime:
                        vl = ax.axvline(etime_i,linestyle='-.',color='g')
                        vl.set_alpha(0.5)
                        vt = ax.text(etime_i,1,plotevent,rotation='vertical',va = 'top',ha='left',color=vl.get_color(),fontsize=10,transform=trans)
                        vt.set_alpha(0.5)

        if not index:
            index = self.current_tab
        if self.sim is None or len(self.sim.data)<1:
            return
        if self.legends[index] is not None:
            self.legends[index].remove()

        ax1_color = 'r'
        ax2_color = 'b'

        ax = self.axes[index]
        if keep_lims:
            ylim_hold = [ax[0].get_ylim(),ax[1].get_ylim()]
            xlim_hold = [ax[0].get_xlim(),ax[1].get_xlim()]
        ax[0].clear()
        ax[1].clear()
        plot_events(ax[0])
        ylabs = [[], []]
        data = self.sim.data[0]
        colors = [ax1_color, ax2_color]
        for i in [0, 1]:
            from_unit = DataTypeMap[self.datatypes[index][i][0]].unit
            to_unit = self.selectors[index][i].get()
            for j in range(len(self.datatypes[index][i])):
                datatype = self.datatypes[index][i][j]
                plotdata = units.convert(data[datatype], from_unit, to_unit)
                ax[i].plot(data[FlightDataType.TYPE_TIME], plotdata,color=colors[i],label=DataTypeMap[datatype].name,linestyle=linestyle_tuple[j])
                ylabs[i].append(DataTypeMap[datatype].name)
            ax[i].set_ylabel(','.join(ylabs[i])+', '+to_unit,color=colors[i])
            ax[i].tick_params(axis='y',color=colors[i])
            [t.set_color(colors[i]) for t in ax[i].yaxis.get_ticklabels()]
            if keep_lims:
                ax[i].set_ylim(ylim_hold[i])
                ax[i].set_xlim(xlim_hold[i])
        
        handles, labels = [(a + b) for a, b in zip(ax[0].get_legend_handles_labels(), ax[1].get_legend_handles_labels())]
        self.legends[index] = self.figs[index].legend(handles,labels,prop={'size': 10})

        self.draw(index)

    def draw(self, canvas_index = None):
        ''' Draw the current (or indicated) canvas. '''

        if not canvas_index:
            canvas_index = self.current_tab

        self.canvases[canvas_index].draw()
        ax = self.figs[canvas_index].axes
        mplcursors.cursor(ax, hover=2) # set plots so that hovering over generates a pop-up annotation, but goes away when mouse leaves
        on_key_press = lambda event, canvas=self.canvases[canvas_index], tbar = self.toolbars[canvas_index]: key_press_handler(event, canvas, tbar)
        self.canvases[canvas_index].mpl_connect("key_press_event", on_key_press)
    
    def draw_all(self):
        ''' Draw all canvases. '''
        for i in self.tabs():
            i = self.index(i) # get index number
            self.draw(i)

    def gcf(self):
        ''' Return the current (or indicated) canvas. '''
        return self.figs[self.current_tab]

    def clear_fig(self, fig_index = None):
        ''' Clear the current (or indicated) figure. '''
        if fig_index:
            self.figs[fig_index].clear()
        else:
            self.figs[self.current_tab].clear()

    def clear(self):
        ''' Clear all tabs and associated plots. '''
        for i in range(len(self.names)):
            plt.close(self.figs[i])
            self.canvases[i].get_tk_widget().destroy() # delete canvas associated with plot

        for item in self.winfo_children():
                item.destroy()
        self.figs = []
        self.canvases = []
        self.toolbars= []
        self.names = []
        self.axes = []
        self.legends = []
        self.datatypes = []

    def save_plots(self):
        return (self.canvases, self.figs, self.toolbars, self.names)



def update_listbox(lb,new_options):
    lb.delete(0,'end')
    for string in new_options:
        lb.insert('end',string)