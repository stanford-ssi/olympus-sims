'''
    PlotPane:

    This pane is a ttk.Notebook with a matplotlib plot on each page. SimPages plot() function is passed this object,
    and can add tabs to the notebook to make additional figures.
'''

from email import iterators
import tkinter as tk
import tkinter.ttk as ttk
from turtle import left
from weakref import ref
import numpy as np
import matplotlib.figure as figure
import matplotlib.style as plotstyle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
import mplcursors
from .units import units
from orhelper import FlightDataType
from .orhelperhelper import DataTypeMap, EventTypeMap
import matplotlib.transforms as transforms

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

class FreePlotPane(ttk.Notebook):
    def __init__(self, root):
        super().__init__(root)

        self.current_tab = 0
        self.figs = []
        self.axes = []
        self.iteratorsels = []
        self.selectors  = []
        self.canvases = []
        self.toolbars= []
        self.names = []
        self.legends = []

        self.sim = None

        plt.style.use('classic')

        self.event_names = [EventTypeMap[key] for key in EventTypeMap]
        self.event_keys = list(EventTypeMap.keys())

        self.make_default()

    def update_sim(self,newsim):
        self.sim = newsim

    def update(self,index = None,keep_lims=False):
        def plot_events(ax):
            events = self.sim.events[int(self.iteratorsels[index].get())-1]
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
        # re-plot the data for this figure
        ax1_color = 'r'
        ax2_color = 'b'
        ax = self.axes[index]
        if self.legends[index] is not None:
            self.legends[index].remove()
        if keep_lims:
            ylim_hold = [ax[0].get_ylim(),ax[1].get_ylim()]
            xlim_hold = [ax[0].get_xlim(),ax[1].get_xlim()]
        ax[0].clear()
        ax[1].clear()
        if self.sim is None:
            return
        data = self.sim.data[int(self.iteratorsels[index].get())-1]
        
        if len(data) == 0:
            return
        leftseltypes, leftselnames = self.selectors[index][0].get_datatypes()
        rightseltypes, rightselnames = self.selectors[index][1].get_datatypes()
        ax[0].set_xlabel('time, s')
        ax[0].set_ylabel('/'.join(leftselnames)+ ', ' +self.selectors[index][0].get_unit(),color=ax1_color)
        ax[1].set_ylabel('/'.join(rightselnames)+ ', '+self.selectors[index][1].get_unit(),color=ax2_color)
        ax[0].tick_params(axis='y',color=ax1_color)
        ax[1].tick_params(axis='y',color=ax2_color)
        [t.set_color(ax1_color) for t in ax[0].yaxis.get_ticklabels()]
        [t.set_color(ax2_color) for t in ax[1].yaxis.get_ticklabels()]
        plot_events(ax[0])
        for i in range(len(leftseltypes)):
            datatype = leftseltypes[i]
            plotdata = units.convert(data[datatype],DataTypeMap[datatype].unit,self.selectors[index][0].get_unit())
            ax[0].plot(data[FlightDataType.TYPE_TIME],plotdata,color=ax1_color,linestyle=linestyle_tuple[i],label=DataTypeMap[datatype].name)
        
        for i in range(len(rightseltypes)):
            datatype = rightseltypes[i]
            plotdata = units.convert(data[datatype],DataTypeMap[datatype].unit,self.selectors[index][1].get_unit())
            ax[1].plot(data[FlightDataType.TYPE_TIME],plotdata,color=ax2_color,linestyle=linestyle_tuple[i],label=DataTypeMap[datatype].name)
        
        handles, labels = [(a + b) for a, b in zip(ax[0].get_legend_handles_labels(), ax[1].get_legend_handles_labels())]
        self.legends[index] = self.figs[index].legend(handles,labels,prop={'size': 10})
        if keep_lims:
            ax[0].set_ylim(ylim_hold[0])
            ax[1].set_ylim(ylim_hold[1])
            ax[0].set_xlim(xlim_hold[0])
            ax[1].set_xlim(xlim_hold[1])
        self.draw(index)


    def update_all(self):
        for i in range(len(self.names)):
            self.update(i)
            
    def make_default(self):
        self.add_page("FreePlot")

    def set_page(self, index = 0):
        ''' Set which page to look at. '''
        self.select(index)
    
    def add_page(self, page_title):
        ''' Make a new plotting page. Returns the figure.Figure() object on that page.'''
        frame = ttk.Frame(self) 
        canvasframe = ttk.Frame(frame)
        
        self.figs.append(figure.Figure())
        ax = self.figs[-1].add_subplot(1,1,1)
        self.figs[-1].subplots_adjust(right=0.8)
        self.axes.append([ax, ax.twinx()])
        self.names.append(page_title)
        self.legends.append(None)

        my_ind = len(self.names)-1
        leftselector = DataSelector(frame,self,my_ind,'Left')
        rightselector = DataSelector(frame,self,my_ind,'Right')
        eventselector = tk.Listbox(frame,selectmode='multiple',exportselection=False)
        update_listbox(eventselector,[EventTypeMap[key] for key in EventTypeMap])
        eventselector.bind('<<ListboxSelect>>',lambda *args: self.update(my_ind,True))
        self.selectors.append([leftselector, rightselector, eventselector])

        itervar = tk.IntVar(self,value=1)
        if self.sim is not None:
            iterselector = ttk.Scale(frame,from_=1,to_=len(self.sim.num_iters),orient='horizontal',variable=itervar)
        else:
            iterselector = ttk.Scale(frame,from_=1,to_=1,orient='horizontal',variable=itervar)
        itervar.trace_add(mode='write',callback=lambda *args:self.update(my_ind))
        self.iteratorsels.append(iterselector)

        self.canvases.append(FigureCanvasTkAgg(self.figs[-1], master = canvasframe))
        self.toolbars.append( NavigationToolbar2Tk(self.canvases[-1], canvasframe) )
        self.toolbars[-1].update()
        self.canvases[-1].get_tk_widget().pack(fill='both',expand=True,side='top')

        ttk.Label(frame,text="Iteration ").grid(row=0,column=3,sticky='nsew')
        ttk.Label(frame,textvariable=itervar).grid(row=0,column=4,sticky='nsew')
        iterselector.grid(row=0,column=5,columnspan=2,sticky='nsew')
        leftselector.grid(row=1,column=0,columnspan=3,sticky='nsew')
        rightselector.grid(row=1,column=3,columnspan=3,sticky='nsew')
        eventselector.grid(row=1,column=6,sticky='nsew')
        canvasframe.grid(row=2,column=0,columnspan=7,sticky='nsew')
        
        
        frame.columnconfigure(1,weight=1)
        frame.columnconfigure(4,weight=1)
        frame.rowconfigure(2,weight=1)
        
        self.add(frame, text = page_title)
        
        if self.sim is not None:
            self.update(my_ind)

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
        for i in self.tabs():
            i = self.index(i) # get index number
            plt.close(self.figs[i])
            self.canvases[i].get_tk_widget().destroy() # delete canvas associated with plot

        for item in self.winfo_children():
                item.destroy()
        self.canvases = []
        self.figs = []
        self.toolbars = []
        self.names = []

    def save_plots(self):
        return (self.canvases, self.figs, self.toolbars, self.names)


class DataSelector(ttk.Frame):
    first = True
    data_names = [DataTypeMap[key].name for key in DataTypeMap.keys()]
    data_units = [DataTypeMap[key].unit for key in DataTypeMap.keys()]
    data_keys = list(DataTypeMap.keys())
    compatible_datanames = []
    def __init__(self, master, freeplotpane, idx, modifier):
        if DataSelector.first:
            DataSelector.first = False
            DataSelector.compatible_datanames = []
            datatypes = DataTypeMap.copy()
            while(len(datatypes.keys())):
                base_type = datatypes.pop(list(datatypes.keys())[0])
                compatible_names = [base_type.name]
                for key in list(datatypes.keys()):
                    ref_type = datatypes[key]
                    if units.validate_units(base_type.unit,ref_type.unit):
                        compatible_names.append(ref_type.name)
                        datatypes.pop(key)
                DataSelector.compatible_datanames.append(compatible_names)

        self.idx = idx
        self.freeplotpane = freeplotpane
        super().__init__(master)
        self.otherdatasel = tk.Listbox(self,selectmode='multiple',exportselection=False)
        self.otherdatasel.bind('<<ListboxSelect>>',self.changed_other_data)
        self.datavar = tk.StringVar(self,value='-')
        self.unitvar = tk.StringVar(self,value='-')
        self.unitsel = ttk.OptionMenu(self,self.unitvar,'-','-')
        self.datavar.trace_add(mode='write', callback = self.update)
        self.unitvar.trace_add(mode='write', callback=lambda *args:self.update(idx))
        if modifier == 'Left':
            self.datasel = ttk.OptionMenu(self,self.datavar,DataTypeMap[list(DataTypeMap.keys())[1]].name,*tuple(DataSelector.data_names))
            self.unitvar.set(DataTypeMap[list(DataTypeMap.keys())[1]].unit)
        else:
            self.datasel = ttk.OptionMenu(self,self.datavar,DataTypeMap[list(DataTypeMap.keys())[2]].name,*tuple(DataSelector.data_names))
            self.unitvar.set(DataTypeMap[list(DataTypeMap.keys())[2]].unit)
 
        ttk.Label(self,text=modifier + ' Axis Data: ').grid(row=0,column=0,sticky='nsew')
        self.datasel.grid(row=0,column=1,sticky='nsew')
        self.unitsel.grid(row=0,column=2,sticky='nsew')
        self.otherdatasel.grid(row=1,column=1,sticky='nsew')
        self.columnconfigure(1,weight=1)

    def get_unit(self):
        return self.unitvar.get()


    def get_datatypes(self):
        types_to_plot = []
        names_to_plot = [self.datavar.get()] + [self.otherdatasel.get(i) for i in self.otherdatasel.curselection()]
        for name in names_to_plot:
            types_to_plot.append(self.data_keys[self.data_names.index(name)])
        return types_to_plot, names_to_plot

    def changed_other_data(self, *args):
        self.freeplotpane.update(self.idx)

    def update(self, *args):
        new_dataname = self.datavar.get()
        compat_units = units.get_compatible_units(self.data_units[self.data_names.index(new_dataname)])
        update_optionmenu(self.unitsel,self.unitvar,compat_units)
        for i in range(len(DataSelector.compatible_datanames)):
            if new_dataname in DataSelector.compatible_datanames[i]:
                hold_sel = [self.otherdatasel.get(i) for i in self.otherdatasel.curselection()]
                cut_list = [dataname for dataname in DataSelector.compatible_datanames[i] if dataname != new_dataname]
                update_listbox(self.otherdatasel,cut_list)
                for sel in hold_sel:
                    if sel in cut_list:
                        self.otherdatasel.select_set( cut_list.index(sel) )
                break
        self.freeplotpane.update(self.idx)


def update_listbox(lb,new_options):
    lb.delete(0,'end')
    for string in new_options:
        lb.insert('end',string)

def update_optionmenu(om, om_var, new_options):
        menu = om["menu"]
        menu.delete(0, "end")
        for string in new_options:
            menu.add_command(label=string, 
                                command=lambda value=string: om_var.set(value))
        if om_var.get() not in new_options:
            om_var.set(new_options[0])
        else:
            om_var.set(om_var.get())

