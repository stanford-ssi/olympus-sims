from audioop import mul
from statistics import stdev
import tkinter as tk
from tkinter import ttk
import numpy as np
from random import gauss, uniform
from lib import orhelperhelper as orhh
import orhelper
from orhelper import FlightDataType, FlightEvent
from .orhelperhelper import ExtendedDataType, DataTypeMap, EventTypeMap
from .ORSimListener import ORSimListener
from .units import units

class SimOutput:
    def __init__(self,name,datatype,output_type='max',when='any'):
        ''' output_type can be 'max', 'min','avg', or 'at' (looks at when for an EventType).
            if when = 'ascent', only the flight data during ascent is considered for min/max/avg.
            if output_type= 'at', when should be a FlightEvent at which to get the value. '''

        self.name = name
        self.datatype = datatype
        self.unit = DataTypeMap[datatype].unit
        self.output_type = output_type
        self.when = when
        self.mean = 0
        self.stddev = 0

    def clear(self):
        self.mean = 0
        self.stddev = 0
    
    def update(self,data,events):
        vals = []
        for i in range(len(data)): # for each iteration
            if self.output_type == 'at':
                try:
                    time_ind = np.where(data[i][FlightDataType.TYPE_TIME] == events[i][self.when][0])[0]
                    if len(time_ind) > 1:
                        time_ind = time_ind[0]
                    elif len(time_ind) == 0:
                        time_ind = -1
                except:
                    time_ind = -1
            elif self.when == 'ascent':
                time_ind = np.where(data[i][FlightDataType.TYPE_TIME] < events[i][FlightEvent.APOGEE][0])
            else:
                time_ind = range(len(data[0][FlightDataType.TYPE_TIME]))
            if self.output_type == 'at':
                val = data[i][self.datatype][time_ind]
            elif self.output_type == 'min':
                val = np.nanmin(np.take(data[i][self.datatype],time_ind))
            elif self.output_type == 'avg':
                val = np.nanmean(np.take(data[i][self.datatype],time_ind))
            else:
                val = np.nanmax(np.take(data[i][self.datatype],time_ind))
            vals.append(val)
        self.mean = np.nanmean(vals)
        self.stddev = np.nanstd(vals)

class Sim:
    # sim outputs
    outputs = [
        SimOutput('Rail Speed',FlightDataType.TYPE_VELOCITY_Z,output_type='at',when=FlightEvent.LAUNCHROD),
        SimOutput('Max. Altitude',FlightDataType.TYPE_ALTITUDE,output_type='at',when=FlightEvent.APOGEE),
        SimOutput('Time to Apogee',FlightDataType.TYPE_TIME,output_type='at',when=FlightEvent.APOGEE),
        SimOutput('Lateral Distance',FlightDataType.TYPE_POSITION_XY,output_type='at',when=FlightEvent.GROUND_HIT),
        SimOutput('Max. Speed',FlightDataType.TYPE_VELOCITY_TOTAL,output_type='max',when='ascent'),
        SimOutput('Max. Mach',FlightDataType.TYPE_MACH_NUMBER,output_type='max',when='ascent'),
        SimOutput('Max. Accel.',FlightDataType.TYPE_ACCELERATION_TOTAL,output_type='max',when='ascent'),
        SimOutput('Avg. Stability',FlightDataType.TYPE_STABILITY,output_type='avg',when='ascent'),
        SimOutput('Avg. DR',ExtendedDataType.TYPE_DAMPING_RATIO,output_type='avg',when='ascent'),
        SimOutput('Avg. Nat Freq',ExtendedDataType.TYPE_NATURAL_FREQUENCY,output_type='avg',when='ascent'),
        SimOutput('Avg. Char Len',ExtendedDataType.TYPE_CHAR_OSCILLATION_DISTANCE,output_type='avg',when='ascent'),
    ]
    def __init__(self, ORinstance, orh, ork_file, idx, name, motor):
        self.idx = idx
        self.name = name
        self.motor = motor
        self.ork_file = ork_file
        self.or_instance = ORinstance
        self.orh = orh
        self.data = []
        self.num_iters = 1
        self.events = []
        self.vary_params = True
    
    def run(self, iterations = 1):
        iterations = min(max(1,iterations),100)
        self.num_iters = iterations
        self.data = []
        self.events = []
        self.doc = self.orh.load_doc(self.ork_file)

        sim = self.doc.getSimulation(self.idx) 
        opts = sim.getOptions()
        rocket = opts.getRocket()
        self.hold_parameters(opts,rocket)

        for i in range(iterations):
            print("Running simulation iteration " + str(i+1)+ " of " + str(iterations))

            if iterations > 1 and self.vary_params:
                self.vary_parameters(opts,rocket)

            # Run simulation
            orsimlistener = ORSimListener(sim, rocket)
            self.orh.run_simulation(sim,listeners=[orsimlistener])
            data = self.orh.get_timeseries(sim, [e for e in FlightDataType]) # get all data available
            extended_data = orsimlistener.get_results()
            data.update(extended_data)
            events = self.orh.get_events(sim)
            
            # Add data to simulation list
            self.data.append(data)           
            self.events.append(events)
        self.update_outputs()
    
    def update_outputs(self):
        for output in self.outputs:
            output.update(self.data,self.events)

    def hold_parameters(self,opts,rocket):
        self.launchrod_dir = np.rad2deg(opts.getLaunchRodDirection())
        self.launchrod_ang = np.rad2deg(opts.getLaunchRodAngle())
        self.windspeed_avg = opts.getWindSpeedAverage()
        self.windturb_int = opts.getWindTurbulenceIntensity()
        self.comps = [x for x in orhh.get_all_components(rocket) if bool(x.isMassive())] # dont include items that don't have a mass, ruins everything
        self.masses = [float(x.getMass()) for x in self.comps]
    
    def vary_parameters(self,opts,rocket):
        ''' Vary the simulation parameters using normal distributions to introduce noise into the system. 
            Aids in determining a more realistic standard deviation for altitude with many simulation runs. '''
        for i in range(len(self.comps)):
            component = self.comps[i]
            new_m = self.masses[i]*gauss(1.0,0.025) # mass of components taken to be +/- 2.5%
            try:
                component.setMassOverridden(True)
                component.setOverrideMass(new_m) # vary mass of components with +/- 5 percent standard dev
            except Exception as e:
                print(e)
        opts.setLaunchRodAngle(np.deg2rad(gauss(self.launchrod_ang,2))) # vary launch rod angle +/- 2deg
        opts.setLaunchRodDirection(np.deg2rad(gauss(self.launchrod_dir,5))) # vary launch rod direction +/- 5deg
        opts.setWindSpeedAverage(max(0,self.windspeed_avg*gauss(1.0,0.05))) # vary average windspeed +/- 5% 
        opts.setWindTurbulenceIntensity(max(0,gauss(self.windturb_int,0.05))) # vary turbulence intensity +/- 5%

    @staticmethod
    def clear_outputs():
        for output in Sim.outputs:
            output.clear()