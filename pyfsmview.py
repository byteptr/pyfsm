"""
Module for view finite state machines as pyfsm module part. 

Author: Raul Alvarez
Email: ralvarezb78@gmail.com
Version: 1.0.0
Date: 2025-06-15
License: MIT

Copyright (c) 2025 Raul Alvarez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from dataclasses import dataclass, field
from graphviz import Digraph
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol
from aiohttp import web
import aiofiles 
from typing import Set
from typing import Optional
from queue import Queue 
from pyfsm import fsm
from pyfsm import fsm_bindings
import time 



class pyfsm_http_visualizer: 
    def __init__(self, http_port:int=8000, ws_port:int=8765, ws_host : str = '0.0.0.0',
                 html_template='aioftest.html'):

        self.http_port = http_port
        self.ws_port = ws_port
        self.ws_host = ws_host
        self.html_template = html_template
        self.app = None
        self.clients: Set[WebSocketServerProtocol] = set()
        self.inbox : Queue = Queue()
        self.outbox : Queue = Queue()
        self.fsm_instance : Optional[fsm] = None
        self.fsmbind : fsm_bindings = fsm_bindings() 


    def bind(self, f: fsm)->None:
        self.fsm_instance = f
        self.fsm_instance.binding = self.fsmbind
    
    def _run(self): 
        while not self.fsmbind.ev_running.is_set():
            # main running loop 
            if not self.fsmbind.ev_async_flag.is_set():
                self.fsm_instance.step()
                time.sleep(self.fsmbind.sleep_time)
            else: 
                if not self.fsmbind.ev_loop_flag.is_set():
                    self.fsm_instance.step()
                    self.fsmbind.ev_loop_flag.set()
                time.sleep(max(0.02, self.fsmbind.sleep_time))
                

    async def run_fsm(self):
        _ = await asyncio.to_thread(self._run)


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

