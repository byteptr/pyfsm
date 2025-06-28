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
from typing import Callable
from typing import Set
from typing import Awaitable
from typing import Optional
from typing import Any
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
        self.tasks : List[Callable[...,Awaitable[Any]]] = []

    def bind(self, f: fsm)->None:
        self.fsm_instance = f
        self.fsm_instance.binding = self.fsmbind
    
    def _run(self): 
        print("_run() method started...")
        # main running loop: while ev_running is set. 
        while self.fsmbind.ev_running.is_set():
            # self.fsm_instance.step()
            # time.sleep(self.fsmbind.sleep_time)
            if self.fsmbind.ev_async_flag.is_set: 
                if self.fsmbind.ev_loop_flag.is_set():
                    self.fsm_instance.step()
                time.sleep(self.fsmbind.sleep_time)
            else:
                #otherwise if no free running option is set, 
                # we check if loop flag is set, then executes one step
                # finally clears the flag and waits for some amount of time
                if self.fsmbind.ev_loop_flag.is_set():
                    self.fsm_instance.step()
                    self.fsmbind.ev_loop_flag.clear()
                time.sleep(self.fsmbind.sleep_async)


    async def run_fsm(self, run_method_async: bool = True):
        print("starting run_fsm()")
        if run_method_async: 
            self.fsmbind.ev_async_flag.set()
        else:
            self.fsmbind.ev_async_flag.clear()

        self.fsmbind.ev_running.set()
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
                service.fsmbind.ev_running.clear()

    async def start(self):
        print("Starting all tasks")
        await asyncio.gather(
            self.start_http_server(),
            self.start_websocket(),
            self.run_fsm(), 
            *(fn() for fn in self.tasks)
        )

class test_fsm(fsm):
    def __init__(self, history_len=10) -> None:
        super().__init__(history_len)
        self.a = 0

    def tcondition(self)->bool:
        return (self.a % 10) == 0 

    def step(self) -> None:
        self.a += 1
        self.a %= 100
        super().step()

    async def printstate(self)->None:
        print("Prinstate running...")
        while True:
            print(f'{self.a} {self.state}')
            await asyncio.sleep(0.1)

if __name__ == '__main__': 
    f = test_fsm()

    f.add_transition('A => B : t0')
    f.add_transition('B => C : t1')
    f.add_transition('C => D : t2')
    f.add_transition('D => A : t3')

    f.add_condition('t0', f.tcondition)
    f.add_condition('t1', f.tcondition)
    f.add_condition('t2', f.tcondition)
    f.add_condition('t3', f.tcondition)

    f.compile()

    
    service = pyfsm_http_visualizer()
    service.bind(f)
    service.tasks.append(f.printstate)

    service.fsmbind.ev_loop_flag.set()
    try: 
        asyncio.run(service.start())
    except KeyboardInterrupt: 
        service.fsmbind.ev_running.clear()
        print("Ctrl-C detected. exit()")

