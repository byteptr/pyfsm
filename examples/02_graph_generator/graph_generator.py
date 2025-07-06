
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example using graph generator

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
from pyfsmgraph import dynamic_graph

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
    
    dg = dynamic_graph(f)
    f.state = 0

    print(dg.node_transitions)
    print(dg.states)
    _ = dg.build_svg()


