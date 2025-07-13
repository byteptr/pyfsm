# pyfsm

Module for the management, representation, and analysis of finite state machines (FSM).

## Features

- Define state machines.
- Define actions 
- Generate transition matrices.
- Analyze connectivity and accessibility between all states.
- Detect inaccessible or unreachable states.
- Detect windowed state-cycles.
- Detect closed cycles.

## Introduction

This module provides classes and functions to create, manage, and analyze finite state machines (FSM). It offers tools to represent FSMs, evaluate their structure, and identify important properties such as state accessibility and cycle detection.
I often code state machines to drive, test hardware, and make measurement tools. So, tired about verbosity I decide to make my own tool to describe FSMs in very direct fashion.
Then I decided to add a tool to visualize the states on real time.

## Description

The FSM is represented by square matrix form where the matrix is an adjacency matrix that represents the directed graph of the deterministic automata.
Here, the rows represent the current state and the columns the next state; each element $a(i,j) = \delta_k$ represents a transition condition which can be 1 or 0, (True or False), 
so in this case i-th state goes to j-th state if k-th condition is true.


<p align="center">
  <img src="img/matrix_fsm.png" >
</p>

This matrix represents the following FSM: 

<p align="center">
  <img src="img/diagram.png" >
</p>

In order to describe a FSM you need a 3-element Tuple: $s_{origin}\to s_{destiny}:t_{condition}$ where $s_{k}$ are the states and $t_k$ transition conditions: functions or expressions 
to be evaluated if theu are **true** or **false**.  

To describe correctly FSM in deterministic case, the following conditions must be fullfilled: 

1. A transition condition from state $s_i$ to $s_j$ is unique
1. Given a state $s_i$, whose outgoing flow branches into several paths toward the possible states $s_{k},s_{r},s_{t},...,s_{v}$
    according to the associated transitions $\delta_{i,k},\delta_{i,r},\delta_{i,t},...,\delta_{i,v}$, these transitions must satisfy the condition of being mutually exclusive. 
    That is, only one of them must be true in the s i-th state.  
    $$\bigcap^{\infty} \delta_{i,m} = 0$$  
      $$s := s_{k} | s_{i} \cap \delta_{i,k}$$  
1. Transition condition $s_{origin}\to s_{destiny}:t_{condition}$ must be unique. 

## State Machine Actions 
On FSM there are 4 types of actions:
1. On enter: When FSM enters new state.  
1. On state: When FSM is in particular state and step() cycle is called.  
1. On exit: When FSM exits from current state.  
1. On transition: When a particular transition condition is met.  

When two or more conditions are met, the order is the following:
1. On State action callback is called on current state
1. On Transition action callback is called to current state associated transition condition which is True 
1. On Exit action callback is called on current state
1. On Enter action callback is called on new state

## Dead states detection 
Dead states are non-reachable states or states described on FSM that are not reachable because all entries on a given column related to this state are zero.  
To ensure good FSM description a static check for dead states can be performed through accesibility matrix $R$.


The accessibility matrix (also known as the reachability matrix) is a matrix that shows which nodes in a graph can reach which other nodes, either directly or through a path of one or more steps.
If you start with an adjacency matrix $M$, which tells you which nodes are directly connected, the accessibility matrix $R$ tells you whether there is any path at all from node 
$i$ to node $j$, regardless of how many steps it takes.
$$R = \bigwedge_{k=1}^{N} M^k$$
I prefer to perfom matrix summation instead OR operation, first because all non zero entries are the reachability between states like boolean matrix, and 
second, this will give us the number of paths of any length (1 to N), from state $i$ to state $j$. So: 
$$R = \sum_{k=1}^{N} M^k$$
- $R_{i,j}$ show us how many paths of length 1 to N exists from state $i$ to state $j$.
- If $R_{i,j}$ = 0 there is no path between i-th and j-th states.
- If $R_{i,j}$ > 0 there is one or more paths between i-th and j-th states.

For dead states detection, please, refer to ```get_allPaths()``` method.

## Loops or cycle detection
Sometimes, state machines are correctly coded in theoretical terms. However, when they interact with the physical world, unforeseen conditions may arise. Even if the code is correct, the system can enter a limit cycle that may affect an automated process.
For example, let's suppose we have implemented an FSM to characterize and measure battery charging curves. Suppose that full charge detection is based on voltage measurement rather than a coulomb-counting gauge. If, for some reason (battery degradation, a fault in the charging system, etc.), the system fails to reach the threshold voltage, it could enter a cycle like charge → verification → reset → charge → verification → reset...
Since such cycles can be arbitrarily long and vary in nature, two functions have been provided for cycle detection.
Given cycle detection, one can detet the abnormal behavior and take decisions based on that. This makes the code more robust.

#### Closed cycle detection 
Detects if exists a closed cycles on state machine.
Refer to ```detect_closed_cycle()```

#### Windowed cycle detection
Detects cycles on a window.
Refer to ```detect_windowed_cycles()```


## Usage
```python
    def test_fcn():
        return True

    f = fsm()

    f.add_transition('A => B : t0')
    f.add_transition('B => C : t1')
    f.add_transition('C => A : t2')
    f.add_transition('D => A : t3')

    f.add_condition('t0', 'a%10 == 0')
    f.add_condition('t1', 'a%10 == 0')
    f.add_condition('t2', 'a%10 == 0')
    f.add_condition('t3', test_fcn)
    
    f.compile()
    a = 0

    for j in range(130): 
        f.step()
        if (j > 100) and (len(f.true_transitions) != 0): 
            break
        a += 1

    print('done')
    print(f)
```

## Exception classes
<p align="center">
  <img src="img/fsm_exception_class.png" alt="Ligth mode" />  
    <br>Exception hierarchy<br>
</p>

There are two main types of exceptions:
- Invalid Syntax exceptions  
Invalid syntax exceptions are triggered when we are defining FSM before executing it if the user violates the rules of FSM definition. The Syntax exceptions are:
    - Redundant condition : When one transition is use on more than one state transition condition. 
        ```python
                f = fsm()
                f.add_transition('A => B : t0') # OK
                f.add_transition('B => C : t1') # OK
                f.add_transition('C => D : t2') # OK
                f.add_transition('D => A : t3') # OK
                f.add_transition('D => D : t2') # ERROR : Already defined transition for C = > D
        ```
    - Inconsistent transition : When the symbol used to describe  a transition is not the same.  
        You can express transitions using 3 types of symbols: '->', '=>' and ',' (comma). Once one is chosen, it cannot be changed.  

        For example: 
        * This is valid:  

        ```python
                f = fsm()
                f.add_transition('A => B : t0')
                f.add_transition('B => C : t1')
                f.add_transition('C => A : t3')
                f.add_transition('D => A : t4')
                f.add_transition('D => D : t2')
        ```
        * This is also valid: 
        ```python 
                f = fsm()
                f.add_transition('A -> B : t0')
                f.add_transition('B -> C : t1')
                f.add_transition('C -> A : t3')
                f.add_transition('D -> A : t4')
                f.add_transition('D -> D : t2')

        ``` 
        * This too: 
        ```python 
                f = fsm()
                f.add_transition('A,B : t0')
                f.add_transition('B,C : t1')
                f.add_transition('C,A : t3')
                f.add_transition('D,A : t4')
                f.add_transition('D,D : t2')
        ``` 
        * But this is not valid:
        ```python
                f = fsm()
                f.add_transition('A => B : t0')
                f.add_transition('B => C : t1')
                f.add_transition('C -> A : t3') # Transition symbol syntax inconsistency
                f.add_transition('D -> A : t4')

        ```

- Runtime exceptions:  
Runtime exceptions may occur when FSM definition is syntactically correct but some rules are violated at executing time.
    * FSMTransitionEvalError: This exeception raise when there is an error evaluating transition conditions.
    * FSMNondisjoinctTransitions : This error may occur when in an executing flow there are bifurcations and two or more transition conditions are true.
    For example, let us suppose the following FSM: 

        ```python
                f = fsm()
                f.add_transition('A => B : t0')
                f.add_transition('B => C : t1')
                f.add_transition('B => D : t2') 
                f.add_transition('B => E : t3')
                ...
                f.compile()
                ...

                    f.step()
                ... 
        ```
And t1 through t3 are simultaneously true.
<p align="center">
  <img src="img/bifurcation.png" />  
    <br>t1, t2 and t3 are True at same time (non disjoint transitions)<br>
</p>
This raises FSMNondisjoinctTransitions

# pyfsmview 
## Remote HTTP FSM viewer in real time 
pyfsmview is a minimalist http/websocket server to visualize and debug FSM from pyfsm module in real-time to visualize and debug FSM from pyfsm module on real time.

<p align="center">
  <img src="img/fsm_dark.gif" alt="Dark mode" width="600"/>  
    <br>Dark mode<br>
</p>
<p align="center">
  <img src="img/fsm_ligth.gif" alt="Ligth mode" width="600"/>  
    <br>Ligth mode<br>
</p>

### Minimal Example: 

```python
import asyncio
from pyfsm import fsm
from pyfsmview import pyfsm_http_visualizer

if __name__ == '__main__': 

    # FSM Overloading
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

        # Custom co-routine (optional)
        async def printstate(self)->None:
            print("Prinstate running...")
            while True:
                print(f'{self.a} {self.state}')
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

    # Create http visualizer instance in dark mode 
    service = pyfsm_http_visualizer(mode = 'dark')
    service.bind(f) # binds FSM to visualizer
    service.tasks.append(f.printstate) # Adds additional coroutine if you want
    
    service.fsmbind.ev_loop_flag.set() # Event loop flag must be set
    # Runs until Ctrl-C is pressed 
    try: 
        asyncio.run(service.start()) # Classic asyncio running coroutines
    except KeyboardInterrupt: 
        service.fsmbind.ev_running.clear() # Signal stop all 
        print("Ctrl-C detected. exit()")

```
Open a web browser and connect to url: ```localhost:8000```

## Installation

Coming soon....

## License

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


