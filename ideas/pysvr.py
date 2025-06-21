from dataclasses import dataclass, field
from graphviz import Digraph
import asyncio
import websockets
import random

# Funciones de configuración por defecto
def gv_node_properties():
    return {"shape": "circle", "style": "filled", "fillcolor": "lightgray"}

def gv_edge_properties():
    return {"color": "black", "arrowhead": "normal"}

# Clase que gestiona propiedades
@dataclass
class gvproperties:
    default_node_properties: dict = field(default_factory=gv_node_properties)
    default_edge_properties: dict = field(default_factory=gv_edge_properties)
    special_nodes: dict = field(default_factory=dict)
    special_edges: dict = field(default_factory=dict)

    def add_node_properties(self, nodename, **kwargs):
        self.special_nodes[nodename] = kwargs

    def del_node_properties(self, nodename):
        if nodename in self.special_nodes:
            del self.special_nodes[nodename]

    def add_edge_properties(self, src, dst, **kwargs):
        self.special_edges[(src, dst)] = kwargs

    def del_edge_properties(self, src, dst):
        self.special_edges.pop((src, dst), None)

# Generar SVG
def build_svg_from_config(config: gvproperties) -> str:
    dot = Digraph()

    dot.attr('node', **config.default_node_properties)
    dot.attr('edge', **config.default_edge_properties)

    for nodo, props in config.special_nodes.items():
        dot.node(nodo, **props)

    for (src, dst), props in config.special_edges.items():
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
