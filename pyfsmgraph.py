from dataclasses import dataclass, field
from graphviz import Digraph
import asyncio
import websockets
import random
from pyfsm import fsm 

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


def _gv_active_node_ligth_properties():
    return { 
            "color": "#000000", 
            "fillcolor": "#FFFFCC", 
            "fontcolor" : "#000000"
            }

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

def _gv_active_edge_ligth_properties():
    return {"color": "#000000", 
            "arrowhead": "normal", 
            "fontcolor" : "#000000"
            }

def _gv_active_edge_drak_properties():
    return {"color": "#000000", 
            "arrowhead": "normal", 
            "fontcolor" : "#000000"
            }

# Clase que gestiona propiedades
@dataclass
class gvproperties:

    mode : str = 'light'

    default_init_node_properties: dict = field(default_factory=_gv_init_node_ligth_properties)
    default_node_properties: dict = field(default_factory=_gv_node_ligth_properties)
    default_edge_properties: dict = field(default_factory=_gv_edge_ligth_properties)     
    active_node_light_properties : dict = field(default_factory=_gv_active_node_ligth_properties) 
    active_node_dark_properties : dict = field(default_factory=_gv_active_node_dark_properties) 
    active_edge_ligth_properties : dict = field(default_factory= _gv_active_edge_ligth_properties)
    active_edge_dark_properties : dict = field(default_factory=_gv_active_edge_drak_properties)


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


    # Generar SVG
    def build_svg_from_self(self) -> str:
        dot = Digraph()

        dot.attr('node', **self.properties.default_node_properties)
        dot.attr('edge', **self.properties.default_edge_properties)

        # for nodo, props in self.properties.special_nodes.items():
        #     dot.node(nodo, **props)
        #
        # for (src, dst), props in self.properties.special_edges.items():
        #     dot.edge(src, dst, **props)

        return dot.pipe(format="svg").decode("utf-8")

if __name__ == "__main__":
    pass 
