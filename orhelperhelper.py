import orhelper
from orhelper import FlightDataType, FlightEvent
from orhelper import JIterator
from enum import Enum
from typing import Union, List, Iterable, Dict
import numpy as np

''' Extend FlightDataType to include our added data types. '''
added_datatypes = [
    'TYPE_DAMPING_COEFF',
    'TYPE_DAMPING_RATIO',
    'TYPE_CORRECTIVE_COEFF',
    'TYPE_NATURAL_FREQUENCY',
    'TYPE_DYNAMIC_PRESSURE',
    'TYPE_FLUTTER_VELOCITY',
]

datatypenames = [m.name for m in FlightDataType] + added_datatypes
datatypedict = {}
for i in range(len(datatypenames)):
    datatypedict[datatypenames[i]] = i+1

FlightDataType = Enum('FlightDataType', datatypedict)

''' orhelper add-on functions. '''
def get_all_components(rocket,debug=False):
    ''' Get all components objects and return them as a list. '''
    ret = []
    for component in JIterator(rocket):
         ret.append(component)
         if debug:
             print(component.getName())
    return ret

def get_simulation_names(doc):
    ''' Get all simulations in a doc and return them as a list.'''
    ret = []
    for sim in doc.getSimulations():
        ret.append(str(sim.getName()))
    return ret

def get_status_flight_data(status, variables : Iterable[Union[FlightDataType, str]]):
    ''' Get most recent flight data values from a simulation status. '''
    def translate_flight_data_type(flight_data_type:Union[FlightDataType, str]):
        if isinstance(flight_data_type, FlightDataType):
            name = flight_data_type.name
        elif isinstance(flight_data_type, str):
            name = flight_data_type
        else:
            raise TypeError("Invalid type for flight_data_type")
        return getattr(FlightDataType, name)

    branch = status.getFlightData()
    output = dict()
    for v in variables:
        output[v] = np.array(branch.get(translate_flight_data_type(v)))
    return output
