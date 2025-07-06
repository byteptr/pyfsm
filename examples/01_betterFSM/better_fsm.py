
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
better_fsm.py

A better example and cleaner code using class inheritance

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

from pyfsm import fsm 

class myfsm(fsm):
    # Constructor 
    def __init__(self, *args, **kwargs) -> None:
        # Never forgetinitialize base class
        super().__init__(*args,**kwargs)
        # countervariable and increment
        self.counter : int = 0
        self.increment : int = 1

    # Transition functions
    def t0(self)->bool:
        return (self.counter % 10) == 0  

    def t1(self)->bool:
        return (self.counter % 7) == 0  
    
    def t2(self)->bool:
        return (self.counter % 11) == 0 

    def t3(self)->bool:
        return True 

    # Overload of control functions
    def step(self): 
        super().step()
        self.counter += self.increment

    def reset(self): 
        super().reset()
        self.counter = 0


if __name__ == "__main__": 

    f = myfsm()

    f.add_transition('A => B : t0')
    f.add_transition('B => C : t1')
    f.add_transition('C => A : t2')
    f.add_transition('D => A : t3')

    f.add_condition('t0', f.t0)
    f.add_condition('t1', f.t1)
    f.add_condition('t2', f.t2)
    f.add_condition('t3', f.t3)
    
    f.compile()

    for j in range(130):
        prev_state = f.states[f.state]
        f.step()

        if prev_state != f.states[f.states[f.state]]:
            print(f"{prev_state}->{f.states[f.state]}")

    print('done')
    print(f)
    print("class printed")

