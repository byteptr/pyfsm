import numpy as np
from dataclasses import dataclass, field
from graphviz import Digraph
from numpy._core.numeric import where
from pyfsm import fsm 
from typing import Optional
import os 

# Funciones de configuración por defecto

def _gv_init_node_dark_properties():
    return {"shape": "doublecircle", 
            "style": "filled", 
            "color": "#DCDCAA", 
            "fillcolor": "#00000000", 
            "fontcolor" : "#DCDCAA"}

def _gv_node_dark_properties():
    return {"shape": "circle", 
            "style": "filled", 
            "color": "#DCDCAA", 
            "fillcolor": "#00000000", 
            "fontcolor" : "#DCDCAA"}

def _gv_edge_dark_properties():
    return {"color": "#DCDCAA", 
            "arrowhead": "normal", 
            "fontcolor" : "#DCDCAA"
            }

def _gv_init_node_ligth_properties():
    return {"shape": "doublecircle", 
            "style": "filled", 
            "color": "#303030", 
            "fillcolor": "#FFFFFF", 
            "fontcolor" : "#000000"}

def _gv_node_ligth_properties():
    return {"shape": "circle", 
            "style": "filled", 
            "color": "#303030", 
            "fillcolor": "#FFFFFF", 
            "fontcolor" : "#000000"
            }

def _gv_edge_ligth_properties():
    return {"color": "#303030", 
            "arrowhead": "normal", 
            "fontcolor" : "#000000"
            }

def _gv_active_node_dark_properties():
    return { 
            "color": "#FFFF00", 
            "fillcolor": "#E5FFCC:#00FFFF",
            "fontcolor" : "#000000"
            }

def _gv_active_node_ligth_properties():
    return { 
            "color": "#FF0000", 
            "fillcolor": "#FFCCFF:#FFCCCC",
            "fontcolor" : "#000000",
            "gradientangle" : "120",
            }

def _gv_active_init_node_dark_properties():
    return {"shape" : "doublecircle",
            "color": "#FFFF00",
            "fillcolor": "#E5FFCC:#00FFFF",
            "gradientangle" : "120",
            "fontcolor" : "#000000"
            }

def _gv_active_init_node_ligth_properties():
    return {"shape" : "doublecircle",
            "color": "#FF0000", 
            "fillcolor": "#FFCCFF:#FFCCCC",
            "fontcolor" : "#000000",
            "gradientangle" : "120",
            }

def _gv_active_edge_dark_properties():
    return {"color": "#FFFF00",
            "arrowhead": "normal", 
            "fontcolor" : "#FFFF00"
            }

def _gv_active_edge_ligth_properties():
    return {"color": "#000000", 
            "arrowhead": "normal", 
            "fontcolor" : "#000000"
            }

def _gv_default_background_ligth_properties():
    return {'bgcolor' : '#FFFFFF'}

def _gv_default_background_dark_properties():
    return {'bgcolor' : '#303030'}

# Clase que gestiona propiedades
@dataclass
class gvproperties:

    mode : str = 'light'

    default_init_node_light_properties: dict = field(default_factory=_gv_init_node_ligth_properties)
    default_init_node_dark_properties: dict = field(default_factory=_gv_init_node_dark_properties)

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

    bgcolor_ligth  : dict = field(default_factory=_gv_default_background_ligth_properties)
    bgcolor_dark : dict = field(default_factory=_gv_default_background_dark_properties)

    def __post__init__(self):
        if self.mode == 'dark':
            self.default_init_node_properties: dict = field(default_factory=_gv_init_node_dark_properties)
            self.default_active_init_node_properties: dict = field(default_factory=_gv_active_init_node_dark_properties)
            self.default_node_properties: dict = field(default_factory=_gv_node_dark_properties)
            self.default_active_node_properties: dict = field(default_factory=_gv_active_node_dark_properties)
            self.default_edge_properties: dict = field(default_factory=_gv_edge_dark_properties) 
        else: 
            self.default_init_node_properties: dict = field(default_factory=_gv_init_node_ligth_properties)
            self.default_active_init_node_properties: dict = field(default_factory=_gv_active_init_node_ligth_properties)
            self.default_node_properties: dict = field(default_factory=_gv_node_ligth_properties)
            self.default_active_node_properties: dict = field(default_factory=_gv_active_node_ligth_properties)
            self.default_edge_properties: dict = field(default_factory=_gv_edge_ligth_properties) 

class DynamicGraph: 
    def __init__(self) -> None:
        self.properties = gvproperties(mode='ligth')
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
    def build_svg(self) -> str:
        dot = Digraph()

        if self.properties.mode == 'ligth': 
            dot.attr(**self.properties.bgcolor_ligth)
        else: 
            dot.attr(**self.properties.bgcolor_dark)

        dot.attr(fontname='Courier New')
        dot.attr('node', fontname='Courier New')
        dot.attr('edge', fontname='Courier New')

        if self.properties.mode == 'ligth': 
            dot.attr('node', **self.properties.default_node_light_properties)
            dot.attr('edge', **self.properties.default_edge_ligth_properties)
        else:
            dot.attr('node', **self.properties.default_node_dark_properties)
            dot.attr('edge', **self.properties.default_edge_dark_properties) 

        if self.states[self.fsm_inst.state] == self.initial_state: 
            if self.properties.mode == 'ligth':
                dot.node(str(self.initial_state), **self.properties.active_init_ligth_properties)
            else:
                dot.node(str(self.initial_state), **self.properties.active_init_dark_properties)
        else: 
            if self.properties.mode == 'ligth':
                dot.node(str(self.initial_state), **self.properties.default_init_node_light_properties)
            else: 
                dot.node(str(self.initial_state), **self.properties.default_init_node_dark_properties)


        for node in (n for n in self.states if n != self.initial_state):
            if node != self.states[self.fsm_inst.state]:
                dot.node(node)
            else:
                if self.properties.mode == 'ligth':
                    dot.node(node, **self.properties.active_node_light_properties)
                else: 
                    dot.node(node, **self.properties.active_node_dark_properties)

        # edges 

        for transition in self.node_transitions.keys():
            print(f"Node transition {transition}")
            dot.edge(*self.node_transitions[transition], label = transition)

        if os.path.exists('diagrama_test.pdf'):
            os.remove('diagrama_test.pdf')

        dot.render('diagrama_test', format='pdf', cleanup=True)
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

    print(f'Entry point {f.entry_point}')
    print(f'State {f.state}')
    
    a = 0

    dg = DynamicGraph()
    f.state = 0
    dg.get_fsm(f)

    print(dg.node_transitions)
    print(dg.states)
    _ = dg.build_svg()



