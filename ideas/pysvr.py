from dataclasses import dataclass, field
from graphviz import Digraph
import asyncio
import websockets
import random

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

# Clase que gestiona propiedades
@dataclass
class gvproperties:

    mode : str = 'light'

    default_init_node_properties: dict = field(default_factory=_gv_init_node_ligth_properties)
    default_node_properties: dict = field(default_factory=_gv_node_ligth_properties)
    default_edge_properties: dict = field(default_factory=_gv_edge_ligth_properties) 
    
    active_node_light_properties : dict = field(default_factory=_gv_active_node_ligth_properties) 
    active_node_dark_properties : dict = field(default_factory=_gv_active_node_dark_properties) 
    active_edge_ligth_properties : dict = field(default_factory= )
    active_edge_dark_properties : dict = field(default_factory= )


    def __post__init__(self):
        if self.mode == 'dark':
            self.default_init_node_properties: dict = field(default_factory=_gv_init_node_dark_properties)
            self.default_node_properties: dict = field(default_factory=_gv_node_dark_properties)
            self.default_edge_properties: dict = field(default_factory=_gv_edge_dark_properties) 

    def add_node_properties(self, nodename, **kwargs):
        self.special_nodes[nodename] = kwargs

    def del_node_properties(self, nodename):
        if nodename in self.special_nodes:
            del self.special_nodes[nodename]

    def add_edge_properties(self, src, dst, **kwargs):
        self.special_edges[(src, dst)] = kwargs

    def del_edge_properties(self, src, dst):
        self.special_edges.pop((src, dst), None)

class DynamicGraph: 
    def __init__(self) -> None:
        self.properties = gvproperties(mode='dark')


    # Generar SVG
    def build_svg_from_self(self) -> str:
        dot = Digraph()

        dot.attr('node', **self.properties.default_node_properties)
        dot.attr('edge', **self.properties.default_edge_properties)

        for nodo, props in self.properties.special_nodes.items():
            dot.node(nodo, **props)

        for (src, dst), props in self.properties.special_edges.items():
            dot.edge(src, dst, **props)

        return dot.pipe(format="svg").decode("utf-8")

# Instancia global
graph_config = gvproperties()
graph_config.add_node_properties("A", fillcolor="red")
graph_config.add_node_properties("B", fillcolor="green")
graph_config.add_edge_properties("A", "B", color="blue", label="ir")

# Clientes conectados
clientes = set()

# Colores aleatorios
def random_color():
    return random.choice(["red", "green", "blue", "orange", "purple", "yellow"])

# Animador: cambia colores y reenvía SVG
async def update_node_colors_periodically():
    while True:
        # Cambia el color de cada nodo
        for nodo in graph_config.special_nodes:
            graph_config.special_nodes[nodo]["fillcolor"] = random_color()

        svg = build_svg_from_config(graph_config)

        # Enviar a todos los clientes
        for ws in list(clientes):
            try:
                await ws.send(svg)
            except websockets.ConnectionClosed:
                clientes.remove(ws)

        await asyncio.sleep(1)

# Handler de conexión
async def enviar_svg(websocket, *args):
    print("Cliente conectado")
    clientes.add(websocket)
    try:
        while True:
            await asyncio.sleep(0.5)  # mantener conexión abierta
    finally:
        clientes.remove(websocket)
        print("Cliente desconectado")

# Main
async def main():
    asyncio.create_task(update_node_colors_periodically())
    async with websockets.serve(enviar_svg, "localhost", 8765):
        print("Servidor WebSocket corriendo en ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
