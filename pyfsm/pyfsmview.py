#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyfsmview

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

__author__    = "Raul ALvarez"
__email__     = "ralvarezb78@gmail.com"
__version__   = "1.0.0"
__license__   = "MIT"
__date__      = "2025-06-15"

import logging

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logger.addHandler(logging.NullHandler())
try: 
    import os 
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
    from typing import List
    from queue import Queue 
    from pyfsm import fsm
    from pyfsm import fsm_bindings
    from pyfsmgraph import dynamic_graph
    import time 
    import json 
except Exception as e: 
    logger.error(e)
    raise e

class pyfsm_http_visualizer: 
    def __init__(self, http_port:int=8000, ws_port:int=8765, ws_host : str = 'localhost',
                 html_template : str ='./template/index.html', mode : str = 'ligth')->None:
        """ 
        Constructor: 
        
        :param http_port: Port of htttp server
        :type http_port: int 
        
        :param ws_port: Websocket port 
        :type ws_port: int 

        :param ws_host: Host of websocket, 'localhost' for incoming local connections, '0.0.0.0' for external.
        :type ws_host: str 

        :param mode: Color theme 'ligth' or 'dark'
        :type mode: str

        :return: None
        :rtype: None

        """
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
        self.dgraph : Optional[dynamic_graph] = None 
        self._mode : str = mode 

    def bind(self, f: fsm)->None:
        """ Binds http visualizer to Finite State machine 
        :param f: Finite State Machine class from pyfsm or inherited class 
        :type f: fsm class

        :return: None
        :rtype: None
        """
        self.fsm_instance = f
        self.fsm_instance.binding = self.fsmbind
        self.dgraph = dynamic_graph(f, mode = self._mode)

    
    def _run(self): 
        """
        Internal method called by run_fsm(): Runs FSM inside a thread on two possible fashions:
        - Free running with sleep 
        - Step by step throug event

        :return: None 
        :rtype: None 

        """
        logger.info("_run() method started...")
        # main running loop: while ev_running is set. 
        while self.fsmbind.ev_running.is_set():
            if self.fsmbind.ev_async_flag.is_set: 
                if self.fsmbind.ev_loop_flag.is_set():
                    self.fsm_instance.step()
                    if len(self.fsm_instance.true_transitions_name) > 0:
                        self.fsmbind.q_output.put(True)
                        # print("Transition to queue")
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
        """
        Runs FSM.

        :param run_method_async: If true, FSM is running on free mode with sleep interval. 
                                 Otherwise runs step by step through event self.fsmbind.ev_loop_flag.
        :type run_method_async: bool
        :return: Coroutine object
        :rtype: Coroutine
        """

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
        css_path = os.path.abspath('./template/css')
        js_path = os.path.abspath('./template/js')
        print(css_path)
        print(js_path)
        self.app.router.add_static('/css/', path=css_path, name='css')
        self.app.router.add_static('/js/', path=js_path, name='js')        

        self.app.on_startup.append(self.http_startup)
        self.app.on_cleanup.append(self.http_cleanup)
        # Usar AppRunner para arrancar el servidor
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, host=self.ws_host, port=self.http_port)
        await site.start()

    async def ws_handle(self, websocket):
        self.clients.add(websocket)
        logger.info("Client connected.")
        if self._mode == 'ligth': 
            bg = self.dgraph.properties.bgcolor_ligth['bgcolor']
            tcol = self.dgraph.properties.color_ligth['color']
        else: 
            bg = self.dgraph.properties.bgcolor_dark['bgcolor']
            tcol = self.dgraph.properties.color_dark['color']

        await websocket.send(json.dumps(
                                        {'style': f"body {{ background-color: {bg}; color: {tcol}; }}"}
                                        )
                             )
        try:
            async for msg in websocket:
                logger.info(f"Message from client {msg}")
                await asyncio.sleep(0)
        except websockets.exceptions.ConnectionClosedOK:
            logger.error(websockets.exceptions.ConnectionClosedOK)
        except websockets.exceptions.ConnectionClosedError:
            logger.error(websockets.exceptions.ConnectionClosedError)
        except Exception as e:
            logger.error(e)
        finally:
            self.clients.remove(websocket)

    async def ws_broadcast(self, msg : str): 
        if self.clients: 
            await asyncio.gather(
                    *[ws.send(msg) for ws in self.clients],
                    return_exceptions=True
            )
        else: 
            pass

    async def start_websocket(self):
        async with websockets.serve(self.ws_handle, self.ws_host, self.ws_port):
            try: 
               await asyncio.Future() 
            except asyncio.exceptions.CancelledError: 
                logger.error(asyncio.exceptions.CancelledError)
                self.fsmbind.ev_running.clear()

    async def transmit(self):
        while self.fsmbind.ev_running.is_set():
            dd = dict()
            if not self.fsmbind.q_input.empty(): 
                term_msg = ''
                while not self.fsmbind.q_input.empty():
                    term_msg += self.fsmbind.q_input.get().strip()+'\n\r' 
                    await asyncio.sleep(0)
                dd['term'] = term_msg 

            if not self.fsmbind.q_output.empty():
                _ = self.fsmbind.q_output.get()
                if self.dgraph is not None:
                    msg = self.dgraph.build_svg()
                    dd['svg'] = msg
                    # esto hay que mejorar
                    # if not self.fsmbind.q_input.empty(): 
                    #     term_msg = ''
                    #     while not self.fsmbind.q_input.empty():
                    #         term_msg += self.fsmbind.q_input.get().strip()+'\n\r' 
                    #         await asyncio.sleep(0)
                    #     dd['term'] = term_msg 
            if len(dd) > 0: 
                await self\
                .ws_broadcast(\
                json.dumps(dd)
                )
            await asyncio.sleep(0.1)

    async def start(self):
        logger.info("Starting all tasks")
        
        run_method_async=True 
        if run_method_async: 
            self.fsmbind.ev_async_flag.set()
        else:
            self.fsmbind.ev_async_flag.clear()
        self.fsmbind.ev_running.set()
        asyncio.create_task(asyncio.to_thread(self._run))

        await asyncio.gather(
            self.start_http_server(),
            self.start_websocket(),
            self.transmit(), 
            # self.run_fsm(), 
            *(fn() for fn in self.tasks)
        )

if __name__ == '__main__': 

    class test_fsm(fsm):
        def __init__(self, history_len=10) -> None:
            super().__init__(history_len)
            self.a = 0

        def tcondition(self)->bool:
            return True #(self.a % 10) == 0 

        def step(self) -> None:
            self.a += 1
            self.a %= 2
            super().step()
            
        async def printstate(self)->None:
            print("Prinstate running...")
            while True:
                print(f'{self.a} {self.state}')
                self.binding.q_input.put(f'{self.a} {self.state}')

                await asyncio.sleep(0.1)

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

    
    service = pyfsm_http_visualizer(mode = 'dark')
    service.bind(f)
    service.tasks.append(f.printstate)

    if service.dgraph is not None:
        service.dgraph.add_custom_node_properties('A', {'label': 'init', })
        service.dgraph.add_custom_node_properties('B', {'label': r'state\nB'})
        service.dgraph.add_custom_node_properties('C', {'label': r'state\nC'})
        service.dgraph.add_custom_node_properties('D', {'label': r'state\nD'})
        
        service.dgraph.add_custom_edge_properties('t0', {'label': 't_init', 'penwidth': '3'})

    service.fsmbind.ev_loop_flag.set()
    try: 
        asyncio.run(service.start())
    except KeyboardInterrupt: 
        service.fsmbind.ev_running.clear()
        print("Ctrl-C detected. exit()")

