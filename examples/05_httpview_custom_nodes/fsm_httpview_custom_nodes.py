#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Functional example of HTTP visualizer/viewer and custom nodes example 

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

import asyncio 
from pyfsm import fsm
from pyfsmview import pyfsm_http_visualizer 

class test_fsm(fsm):
    def __init__(self, history_len=10) -> None:
        super().__init__(history_len)
        self.a = 0

    def tcondition(self)->bool:
        return self.a == 0 

    def step(self) -> None:
        self.a += 1
        self.a %= 2
        super().step()

    # Additional sync task example 04
    async def printstate(self)->None:
        print("Prinstate running...")
        while True:
            print(f'{self.a} {self.state}')
            await asyncio.sleep(0.1)
        

if __name__ == '__main__':

    # First create an instance of FSm as usual
    f = test_fsm()
    # Define states and transitions 
    f.add_transition('A => B : t0')
    f.add_transition('B => C : t1')
    f.add_transition('C => D : t2')
    f.add_transition('D => A : t3')
    # Attach functions or expressions to transitions 
    f.add_condition('t0', f.tcondition)
    f.add_condition('t1', f.tcondition)
    f.add_condition('t2', f.tcondition)
    f.add_condition('t3', f.tcondition)
    # Compile
    f.compile()

    # Create an HTTP visualizer service
    service = pyfsm_http_visualizer(mode = 'dark')
    # bind to FSM 
    service.bind(f)

    # add new task 
    service.tasks.append(f.printstate)

    # ***** CUSTOM NODE PROPERTIES *****
    # More representative names for FHSM diagram 
    if service.dgraph is not None:
        service.dgraph.add_custom_node_properties('A', {'label': 'init', })
        service.dgraph.add_custom_node_properties('B', {'label': r'state\nB'})
        service.dgraph.add_custom_node_properties('C', {'label': r'state\nC'})
        service.dgraph.add_custom_node_properties('D', {'label': r'state\nD'})

    # Set ev_loop_flag to allow run the step() on FSM
    service.fsmbind.ev_loop_flag.set()

    # Start service and run until Ctrl-C pressed
    try: 
        asyncio.run(service.start())
    except KeyboardInterrupt: 
        service.fsmbind.ev_running.clear()
        print("Ctrl-C detected. exit()")


