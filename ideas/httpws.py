from dataclasses import dataclass, field
from graphviz import Digraph
import asyncio
import websockets
from aiohttp import web
import aiofiles 
from typing import Set, Any
from queue import Queue 

class pyfsm_http_visualizer: 
    def __init__(self, http_port:int=8000, ws_port:int=8765, ws_host : str = '0.0.0.0',
                 html_template='aioftest.html'):

        self.http_port = http_port
        self.ws_port = ws_port
        self.ws_host = ws_host
        self.html_template = html_template
        self.app = None
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.inbox : Queue = Queue()
        self.outbox : Queue = Queue()
        self.fsm : Any = None # correct typing coming soon

    def bind_fsm(self, fsm)->None:
        self.fsm = fsm

    async def run_fsm(self):
        _ = await asyncio.to_thread(self.fsm, id(self.fsm))

    async def http_startup(self, param): 
        await asyncio.sleep(0)

    async def http_cleanup(self, param): 
        await asyncio.sleep(0)

    async def http_handle(self, request):
        async with aiofiles.open(self.html_template, 'r') as fd: 
            html = await fd.read()
        return web.Response(text=html, content_type='text/html')

    async def start_http_server(self):
        self.app = web.Application()
        self.app.router.add_get('/', self.http_handle)
        self.app.on_startup.append(self.http_startup)
        self.app.on_cleanup.append(self.http_cleanup)
        # Usar AppRunner para arrancar el servidor
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, host=self.ws_host, port=self.http_port)
        await site.start()

    async def ws_handle(self, websocket, path):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                await asyncio.sleep(0)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        finally:
            self.clients.remove(websocket)

    async def ws_broadcast(self, msg : str): 
        if self.clients: 
            await asyncio.gather(
                    *[ws.send(msg) for ws in self.clients],
                    return_exceptions=True
            )

    async def start_websocket(self):
        async with websockets.serve(self.ws_handle, self.ws_host, self.ws_port):
            try: 
               await asyncio.Future() 
            except asyncio.exceptions.CancelledError: 
                print("\nWebsockets terminate.")

    async def start(self):
        await asyncio.gather(
            self.start_http_server(),
            self.start_websocket(),
        )
if __name__ == '__main__': 

    service = pyfsm_http_visualizer()
    try: 
        asyncio.run(service.start())
    except KeyboardInterrupt: 
        print("Ctrl-C detected. exit()")

