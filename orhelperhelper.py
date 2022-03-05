from logging import root
import orhelper
from orhelper import FlightDataType, FlightEvent
from orhelper import JIterator
from enum import Enum
from typing import Union, List, Iterable, Dict
import numpy as np

''' Extend FlightDataType to include our added data types. '''
flightdatalen = max([x.value for x in FlightDataType])
class ExtendedDataType(Enum):
    TYPE_DAMPING_COEFF = flightdatalen + 1
    TYPE_DAMPING_RATIO = flightdatalen + 2
    TYPE_CORRECTIVE_COEFF = flightdatalen + 3
    TYPE_NATURAL_FREQUENCY = flightdatalen + 4
    TYPE_DYNAMIC_PRESSURE = flightdatalen + 5
    TYPE_FLUTTER_VELOCITY = flightdatalen + 6

''' orhelper add-on functions. '''
def get_all_components(rocket,debug=False):
    ''' Get all components objects and return them as a list. '''
    ret = []
    for component in JIterator(rocket):
         ret.append(component)
         if debug:
             print(component.getName())
    return ret

def calculate_fin_flutter_coeff(rocket):
    ''' Get fin components and calculate flutter coeff - the resulting fin flutter critical speed is:
            v_finflutter = flutter_coeff * a * sqrt(G/P)

            where  a = speed of sound at current altitude
                   G = shear modulus of fin material (assumed isotropic)
                   P = static pressure at current altitude
     '''
    fins = None
    for component in JIterator(rocket):
        try:
            component.getRootChord() # check to see if component is a TrapezoidalFinSet
            fins = component
            break
        except:
            pass
    if fins is None:
        raise AttributeError("Rocket does not have a trapezoidal fin set.")
    rootchord = float(fins.getRootChord())
    tipchord = float(fins.getTipChord())
    thickness = float(fins.getThickness())
    semispan = float(fins.getSpan())
    fin_area = 0.5*(rootchord+tipchord)*semispan
    aspect_ratio = (semispan**2)/fin_area
    l = tipchord/rootchord
    vf_coeff = np.sqrt(2*(aspect_ratio+2)*((thickness/rootchord)**3)/(1.337*(aspect_ratio**3)*(l+1)))

    return vf_coeff

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
