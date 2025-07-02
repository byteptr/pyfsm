import numpy as np
from dataclasses import dataclass, field
from graphviz import Digraph
import asyncio
from numpy._core.numeric import where
import websockets
import random
from pyfsm import fsm 
from typing import Optional

# Funciones de configuración por defecto

def _gv_init_node_ligth_properties():
    return {"shape": "doublecircle", 
            "style": "filled", 
            "color": "#000000", 
            "fillcolor": "#FFFFFF", 
            "fontcolor" : "#000000"}

def _gv_node_ligth_properties():
    return {"shape": "circle", 
            "style": "filled", 
            "color": "#000000", 
            "fillcolor": "#FFFFFF", 
            "fontcolor" : "#000000"}

def _gv_edge_ligth_properties():
    return {"color": "#000000", 
            "arrowhead": "normal", 
            "fontcolor" : "#000000"
            }

def _gv_init_node_dark_properties():
    return {"shape": "doublecircle", 
            "style": "filled", 
            "color": "#303030", 
            "fillcolor": "#303030", 
            "fontcolor" : "#FFFFFF"}

def _gv_node_dark_properties():
    return {"shape": "circle", 
            "style": "filled", 
            "color": "#303030", 
            "fillcolor": "#303030", 
            "fontcolor" : "#FFFFFF"}

def _gv_edge_dark_properties():
    return {"color": "#303030", 
            "arrowhead": "normal", 
            "fontcolor" : "#FFFFFF"
            }


# def _gv_active_node_ligth_properties():
#     return { 
#             "color": "#000000", 
#             "fillcolor": "#FFFFCC", 
#             "fontcolor" : "#000000"
#             }

def _gv_active_node_ligth_properties():
    return { 
            "color": "#000000", 
            "fillcolor": "#FFF1E0:#FFE6EB",
            "fontcolor" : "#000000"
            }

def _gv_active_node_dark_properties():
    return { 
            "color": "#000000", 
            "fillcolor": "#0F2027:#203A43:#2C5364",
            "fontcolor" : "#000000"
            }

def _gv_active_init_node_ligth_properties():
    return { 
            "shape" : "doublecircle"
            "color": "#000000", 
            "fillcolor": "#FFF1E0:#FFE6EB",
            "fontcolor" : "#000000"
            }

def _gv_active_init_node_dark_properties():
    return {
            "shape" : "doublecircle"
            "color": "#000000", 
            "fillcolor": "#0F2027:#203A43:#2C5364",
            "fontcolor" : "#000000"
            }


def _gv_active_edge_ligth_properties():
    return {"color": "#000000", 
            "arrowhead": "normal", 
            "fontcolor" : "#000000"
            }

def _gv_active_edge_dark_properties():
    return {"color": "#000000", 
            "arrowhead": "normal", 
            "fontcolor" : "#000000"
            }

# Clase que gestiona propiedades
@dataclass
class gvproperties:

    mode : str = 'light'

    default_init_node_light_properties: dict = field(default_factory=_gv_init_node_ligth_properties)
    default_init_node_dark_properties: dict = field(default_factory=_gv_init_node_ligth_properties)

    default_node_light_properties: dict = field(default_factory=_gv_node_ligth_properties)
    default_node_dark_properties: dict = field(default_factory=_gv_node_dark_properties)

    default_edge_ligth_properties: dict = field(default_factory=_gv_edge_ligth_properties)     
    default_edge_dark_properties: dict = field(default_factory=_gv_edge_dark_properties)     

    active_init_ligth_properties: dict = field(default_factory=_gv_active_init_node_ligth_properties)
    active_init_dark_properties: dict = field(default_factory=_gv_active_init_node_dark_properties)

    active_node_light_properties : dict = field(default_factory=_gv_active_node_ligth_properties) 
    active_node_dark_properties : dict = field(default_factory=_gv_active_node_dark_properties) 

    active_edge_ligth_properties : dict = field(default_factory= _gv_active_edge_ligth_properties)
    active_edge_dark_properties : dict = field(default_factory=_gv_active_edge_dark_properties)


    def __post__init__(self):
        if self.mode == 'dark':
            self.default_init_node_properties: dict = field(default_factory=_gv_init_node_dark_properties)
            self.default_node_properties: dict = field(default_factory=_gv_node_dark_properties)
            self.default_edge_properties: dict = field(default_factory=_gv_edge_dark_properties) 

    # def add_node_properties(self, nodename, **kwargs):
    #     self.special_nodes[nodename] = kwargs
    #
    # def del_node_properties(self, nodename):
    #     if nodename in self.special_nodes:
    #         del self.special_nodes[nodename]
    #
    # def add_edge_properties(self, src, dst, **kwargs):
    #     self.special_edges[(src, dst)] = kwargs
    #
    # def del_edge_properties(self, src, dst):
    #     self.special_edges.pop((src, dst), None)

class DynamicGraph: 
    def __init__(self) -> None:
        self.properties = gvproperties(mode='dark')
        self.node_transitions = dict()
        self.states : list = []
        self.initial_state : Optional[str] = ''

    def get_fsm(self,f:fsm):
        self.fsm_inst = f
        self.initial_state = f.entry_point
        self.states = f.states.copy()
        indexes = np.where(np.not_equal(f.tmatrix, None))
        coordinates = list(zip(*indexes))
        for r,c in coordinates: 
            self.node_transitions[f.tmatrix[r,c]] = (f.states[r],f.states[c])
        
    # Generar SVG
    def build_svg_from_self(self) -> str:
        dot = Digraph()

        dot.attr('node', **self.properties.default_node_properties)
        dot.attr('edge', **self.properties.default_edge_properties)

        if self.states[self.fsm_inst.state] == self.initial_state: 
            if self.mode == 'ligth':
                dot.node(str(self.initial_state), **self.properties.active_init_ligth_properties)
            else:
                dot.node(str(self.initial_state), **self.properties.active_init_dark_properties)

        else: 
            if self.mode == 'ligth':
                dot.node(str(self.initial_state), **self.properties.default_init_node_light_properties)
            else: 
                dot.node(str(self.initial_state), **self.properties.default_init_node_dark_properties)


        for node in (n for n in self.states if n != self.initial_state):
            if node != self.states[self.fsm_inst.state]:
                dot.node(node)
            else:
                dot.node(node, **self.properties.gv)


        # for nodo, props in self.properties.special_nodes.items():
        #     dot.node(nodo, **props)
        #
        # for (src, dst), props in self.properties.special_edges.items():
        #     dot.edge(src, dst, **props)

        return dot.pipe(format="svg").decode("utf-8")

if __name__ == "__main__":
    f = fsm()

    f.add_transition('A => B : t0')
    f.add_transition('B => C : t1')
    f.add_transition('C => D : t2')
    f.add_transition('D => A : t3')

    f.add_condition('t0', 'a%10 == 0')
    f.add_condition('t1', 'a%10 == 0')
    f.add_condition('t2', 'a%10 == 0')
    f.add_condition('t3', 'a%10 == 0')
    
    f.compile()
    a = 0

    dg = DynamicGraph()

    dg.get_fsm(f)

    print(dg.node_transitions)
    print(dg.states)


