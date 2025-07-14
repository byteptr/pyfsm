#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyfsm.py

Module for the management, representation, and analysis of finite state machines (FSM).

This module provides classes and functions to:
- Define state machines.
- Generate transition matrices.
- Analyze connectivity and accessibility between all states.
- Detect inaccessible or unreachable states.
- Detect windowed state-cycles  
- Detect closed cycles

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
    from io import StringIO
    import numpy as np 
    import warnings
    import re 
    import pandas as pd
    from collections import deque
    from dataclasses import dataclass
    from dataclasses import field
    from typing import Any
    from typing import List
    from typing import Union, Callable
    from typing import Optional
    from typing import Deque
    from typing import Set
    from typing import Tuple
    from typing import Dict
    from queue import Queue
    from threading import Event
except Exception as e: 
    logging.error(e)
    raise e

__graphviz_present__ = None

try:
    from graphviz import Digraph
    __graphviz_present__ = True
except ImportError:
    __graphviz_present__ = False
finally:
    logger.info(f'Graphviz presence {__graphviz_present__}')


def custom_formatwarning(msg, category, filename, lineno, line=None):
    return f"WARNING: {msg}\n"

warnings.formatwarning = custom_formatwarning


@dataclass(frozen=True)
class FSMSysMgs:
    
    @staticmethod
    def error_expresion_match(*args,**kwargs)->str: 
        msg = 'Expresion does not match state_origin {->|=>|,} state_destiny : transition' 

        if len(args) > 0:
            msg +='\n'
            msg += ','.join(args)

        if len(kwargs) > 0:
            msg +='\n'
            msg += ','.join(f"{k}:{v}" for k, v in kwargs.items())

        return msg+'\n'

    @staticmethod
    def error_redundant_condition(*args,**kwargs)->str: 
        msg = "Condition already exists. Please, delete first."

        if len(args) > 0:
            msg +='\n'
            msg += ','.join(args)

        if len(kwargs) > 0:
            msg +='\n'
            msg += ','.join(f"{k}:{v}" for k, v in kwargs.items())

        return msg+'\n'

    @staticmethod
    def error_inconsistent_transition(tsymbol1:str, tsymbol2:str, definition:str)->str:
        return (f"FATAL: Inconsistency between transition symbols ({tsymbol1}, {tsymbol2}) at definition:\n"
                f"{definition}\n"
                "Use the same as first. {->, =>, or comma}\n")

    @staticmethod
    def error_undefined_transition(t:str)->str: 
        return (f'{t} not in defined conditions\n')

    @staticmethod
    def warning_unused_transitions(remaining_transitions:List)->str:
        return (f'Unused transitions {remaining_transitions}\n')

    @staticmethod
    def warning_dead_states(dead_states:List, reached_from:str)->str:
        return f'Dead state(s) found.\n{','.join([s for s in dead_states])}\n'+\
            f'Cannot be reached from {reached_from}\n'

    @staticmethod
    def error_non_disjoint_transitions(state:str, transitions:str)->str:
       return f"Non-disjoint transitions at: {state}\n{transitions}\n"
    
    @staticmethod
    def error_transition_eval_error(state: str, transition: str, eval_fcnexp : str = '')->str:
        msg = 'Runtime error evaluating transition function\n'+\
            f'at state: {state} transition: {transition}'
        if len(eval_fcnexp) > 0: 
            msg += f' :: {eval_fcnexp}'
        msg += '\n'
        return msg 

    @staticmethod
    def debug_machine_transition(state0:str, tsymbol:str,state1:str,\
                                 transition : str)->str:
        return f'{state0} {tsymbol} {state1} : {transition}\n'

    @staticmethod
    def error_add_on_entry_action(state:str)->str:
        return f'Unknown state {state} for On Entry Action, create state first.'

    @staticmethod
    def error_add_on_exit_action(state:str)->str:
        return f'Unknown state {state} for On Exit Action, create state first.'

    @staticmethod
    def error_add_on_state_action(state:str)->str:
        return f'Unknown state {state} for On State Action, create state first.'

    @staticmethod
    def error_add_on_transition_action(t:str)->str:
        return f'Unknown transition {t} for On Transition Action, create first.'

    @staticmethod
    def warning_on_entry_action(states:str)->str:
        return f'Warning: undefined states on entry action {states}'

    @staticmethod
    def warning_on_exit_action(states:str)->str:
        return f'Warning: Undefined states on exit action {states}'

    @staticmethod
    def warning_on_state_action(state:str)->str:
        return f'Warning: Undefined states on state action {state}'

    @staticmethod
    def warning_on_transition_action(t:str)->str:
        return f'Warning: undefined transitions on transition action {t}'

# Finite state machine exceptions. 
# TODO: migrate exception treatement to other file
class FSMException(Exception):
    "Base class for FSM exceptions"
    pass 

class FSMInvalidSyntax(FSMException):
    pass

class FSMRuntimeException(FSMException):
    pass

class FSMUnknownException(FSMException): 
    pass

class FSMRedundantCondition(FSMInvalidSyntax):
    pass 

class FSMInconsistentTransition(FSMInvalidSyntax):
    pass

class FSMUndefinedTransition(FSMInvalidSyntax):
    pass

class FSMTransitionEvalError(FSMRuntimeException):
    pass

class FSMNondisjoinctTransitions(FSMRuntimeException):
    pass

class FSMOnEntryActionError(FSMRuntimeException):
    pass

class FSMOnExitActionError(FSMRuntimeException):
    pass

class FSMOnTransitionActionError(FSMRuntimeException):
    pass

class FSMOnStateActionError(FSMRuntimeException):
    pass

class FSMUnknownState(FSMInvalidSyntax):
    pass 

class FSMUnknownTransition(FSMInvalidSyntax):
    pass 

@dataclass 
class fsm_bindings:

    CMD_START : str = 'start' # start running FSM
    CMD_STOP : str = 'stop' # stop running FSM
    CMD_STEP : str = 'step' # execute step by step FSM  (event trigger)
    CMD_RESET : str = 'reset' # resets the finite state machine
    CMD_QUIT : str = 'quit' #  Exits from FSM running thread 
    CMD_TIME_TRIGGER : str = 'time_triggered' # uses sleep()
    CMD_EVENT_TRIGGER : str = 'event_triggered' # uses step 
    CMD_GET_TRIGGER : str = 'get_trigger' # get trigger type event or sleep
    CMD_SET_SLEEP : str = 'set_sleep' # change sleep time
    CMD_GET_SLEEP : str = 'get_sleep' # get sleep time

    MSG_TRIGGER_TIME : str = 'sleep_trigger'
    MSG_TRIGGER_EVENT : str = 'event_trigger'

    q_input : Queue = field(default_factory=Queue)
    q_output : Queue = field(default_factory=Queue)
    ev_running : Event = field(default_factory = Event)
    ev_loop_flag : Event = field(default_factory = Event)
    ev_async_flag : Event = field(default_factory = Event)
    sleep_time : float = 0.5
    sleep_async : float = 0.5

    def __post__init__(self) -> None: 
        self._inmutable__fields_ : Set = set()
        #Declare here non mutable fields by set comprehension 
        # Where looking for the fields which contains CMD and MSG at begining
        self._inmutable__fields_.update( 
         {cts for cts in filter(lambda x: True if x.split('_')[0] in {'CMD','MSG'} \
            else False, self.__class__.__dict__.keys())})
        # lastly protect _inmutable__fields_ itself against mutability 
        self._inmutable__fields_.add('_inmutable__fields_')

    def __setattr__(self, name: str, value: Any, /) -> None:
        if hasattr(self,"_inmutable__fields_") and name in self._inmutable__fields_: 
            raise AttributeError(f'{name} is not mutable.')
        else:
            super().__setattr__(name,value)

class fsm:
    """
    Represents a finite state machine (FSM). This class allows you to define states and transitions of an FSM,
    as well as retrieve basic information about its structure.

    :ivar history_len: Array length of past states history, in order to detect unintended loops.
    :ivar parse_state: Regex expression to parse state machines. 
    :ivar tmatrix: Matrix form of state machine.
    :ivar machine_transitions: list containing defined transitions.
    :ivar true_transitions: vector containing transition conditions that are True
    :ivar true_transitions_name: vector containing names of transition conditions that are True for debug purposes
    :ivar entry-point: Initial state. 
    :ivar conditions: Dictionary that contains expressions or funcions of named transitions.
    :ivar state: Current state. 
    :ivar states: Defined name of number-coded states.
    :ivar dead_states: List of states that aren't never reachable from entry point or initial state.
    :ivar state_history: A list of present and previous states in order. 
    :ivar check_cycles: If True check for cycles provoqued by external conditions that are considered abnormal.
    :ivar tsymbol: Current transition symbol, it can be ->, => or a comma. Once defined on first expression it can't be replaced.
    :ivar check_disjoint: If True check for disjoint transitions on defined state, if not, throws an error FSMNondisjoinctTransitions
    :ivar warnings: If true, prints the warnings.
    :ivar debug: If true prints debug messages.

    """

    def __init__(self, history_len = 10) -> None:
        """
        Class constructor

        :param history_len: Length of vector containing the present and past states.
        :type history_len: int 
        :return: None
        :rtype: None

        """
        self.parse_state = \
            re.compile(r'^\s*(?P<origin>\w+)\s*(?P<tsymbol>\-\>|\s*,\s*|=>)\s*'+\
            r'(?P<dest>\w+)\s*:\s*(?P<transition>\w+)\s*$')
        self.tmatrix : Optional[np.ndarray] = None 
        self.machine_trasitions : List = []
        self.true_transitions : List = []
        self.true_transitions_name : List = []
        self.entry_point : Optional[str] = None
        self.conditions = dict()
        self.state : Optional[int] = None
        self.states : List[str] = []
        self.dead_states = []
        self.state_history : Deque[Optional[int]]= deque([None]*history_len, maxlen = history_len) 
        self.history_len = history_len
        self.check_cycles = False
        self.tsymbol = None
        self.check_disjoint = True 
        self.warnings = False 
        self.debug = False 
        # Class bindings 
        self.binding : Optional[fsm_bindings] = None
        # actions
        self.actions_on_state : Dict[str, Union[str, Callable[...,Any]]] = {}
        self.actions_on_entry : Dict[str, Union[str, Callable[...,Any]]] = {}
        self.actions_on_exit : Dict[str, Union[str, Callable[...,Any]]] = {}
        self.actions_on_transition : Dict[str, Union[str, Callable[...,Any]]] = {}
        self.invalid_actions : Dict[str, set] = {}

    def reset(self)->None:
        """
        Resets the finite state machine.

        :return: None
        :rtype: None

        """
        self.true_transitions.clear() 
        self.state_history = deque([None]*self.history_len, maxlen = self.history_len) 
        self.state = self.index_dict[self.entry_point]
        self.state_history.clear()
        self.state_history.append(self.state)

    def add_transition(self, s:str)->None:
        """
        Add state transition or define a state machine <state_0> <transition_symbol> <state_1> : <transition_identifier>
        Where: 

            state_0 : Is the name of present state 
            transition_symbol : One of those symbols allowed to represent a transition {->|=>|,}
            state_1 : New state

        Note: 
            Once a valid transition symbol is chose, it must remains the same for all machine state definitions, otherwise
            compile() method will throw an Exception FSMInconsistentTransition


        Examples:

            Valid state machine syntax:  

                f = fsm()
                f.add_transition('A => B : t0')
                f.add_transition('B => C : t1')
                f.add_transition('C => A : t3')
                f.add_transition('D => A : t4')
                f.add_transition('D => D : t2')

            This is also valid: 
            
                f = fsm()
                f.add_transition('A -> B : t0')
                f.add_transition('B -> C : t1')
                f.add_transition('C -> A : t3')
                f.add_transition('D -> A : t4')
                f.add_transition('D -> D : t2')

            As well as:

                f = fsm()
                f.add_transition('A,B : t0')
                f.add_transition('B,C : t1')
                f.add_transition('C,A : t3')
                f.add_transition('D,A : t4')
                f.add_transition('D,D : t2')

            This is not valid: 
            
                f = fsm()
                f.add_transition('A => B : t0')
                f.add_transition('B => C : t1')
                f.add_transition('C -> A : t3') # Transition symbol syntax inconsistency
                f.add_transition('D -> A : t4')


        :param s: String containing the syntax describing state transition.
        :type s: str
        :return: None
        :rtype: None


        """
        if (transition_match := self.parse_state.match(s)):
            self.machine_trasitions.append(s)
        else:
            logger.error(FSMSysMgs.error_expresion_match())
            raise FSMInvalidSyntax

    def get_state(self)->str:
        """

        Get current state name

        :return: Strng containing the current state name 
        :rtype: str

        """
        if self.state is not None:
            return self.states[self.state]
        else: 
            return ''

    def add_condition(self,t:str, fcond:Union[str,Callable[...,bool]])->None:
        """
        Adds function/expression evaluate named condition. 

        :param t: String containing the name of transition described on 
                    state machine.
        :type t: str
        :param fcond: function returning bool or string expression to evaluate 
                        which results on a boolean type
        :type fcond: str, Callable[...,bool]  
        :return: None
        :rtype: None

        Examples:

                def test_fcn():
                    return a%7 == 0

                f.add_condition('t0', 'a%10 == 0')  # Expression: evaluates a%10 == 0
                f.add_condition('t1', test_fcn)     # Function: evaluates a%7 == 0

        Note: Conditions must be unique for each transition, if one transition name is 
                repeated, this will throw FSMRedundantCondition exception.
                To change one condition function/expression, you must dele first with
                del_condition() method


        """
        if not t in self.conditions.keys():
            self.conditions[t] = fcond
        else:
            logger.error(FSMSysMgs.error_redundant_condition())
            raise FSMRedundantCondition
    
    def del_condition(self,cond)->None:
        """
        Deletes existing condition.

        :param cond: Existing condition to delete.
        :type cond: str
        :return: None
        :rtype: None

        """
        del self.conditions[cond]

    def compile(self)->None:
        """
        Compiles the state machine.
        1.- Get a list of total states 
        2.- Parses all transitions 
        3.- Creates FSM in matrix form
        4.- Verifies the integrity of transitions (unused, non-defined)
        5.- Calculates non-reachable / dead states from entry point.

        Warnings: 
        ---------
            warning_unused_transitions() : Transitions that are valid, declared, but unused.
            warning_dead_states() : If Dead / unracheable states found.

        Exceptions: 
        -----------
            FSMUnknownException : If non-defined or general faillure goes on.
            FSMInconsistentTransition : If The transition syntax is not 
            consistent (different symbols used to)

        :return: None
        :rtype: None

        """
        self.states = sorted(set(
            s
                for x in [
                        self.parse_state.match(dd).groupdict()
                        for dd in self.machine_trasitions
                    ]
                for s in (x['origin'], x['dest'])
            )
        )

        N = len(self.states)
        self.tmatrix = np.full((N,N), None, dtype=object)
        self.index_dict = {ss:k for k,ss in enumerate(self.states)}
        remaining_transitions = set(self.conditions.keys())
        try: 
            for k,m in enumerate(self.machine_trasitions): 
                dd = self.parse_state.match(m).groupdict()
                if k == 0: 
                    self.tsymbol = dd['tsymbol']
                    self.entry_point = dd['origin'] # Automatic initial state determination. 
                    self.state = self.index_dict[self.entry_point]
                    self.state_history.append(self.state)
                elif self.tsymbol != dd['tsymbol']:
                    errmsg = FSMSysMgs.error_inconsistent_transition(
                        tsymbol1=self.tsymbol, 
                        tsymbol2=dd['tsymbol'], 
                        definition=m)
                    logger.error(errmsg)
                    raise FSMInconsistentTransition(errmsg)


                self.tmatrix[self.index_dict[dd['origin']],self.index_dict[dd['dest']]] = dd['transition']
                if dd['transition'] in self.conditions.keys():
                    remaining_transitions.remove(dd['transition'])
                else: 
                    errmsg = FSMSysMgs.error_undefined_transition(dd['transition'])
                    logger.error(errmsg)
                    raise FSMUndefinedTransition(errmsg)

        except Exception as e:
            logger.error(e)
            raise FSMUnknownException(e)

        if len(remaining_transitions) > 0: 
            warnmsg = FSMSysMgs.warning_unused_transitions(
                    remaining_transitions=remaining_transitions)
            logger.warning(warnmsg)
            if self.warnings:
                warnings.warn(warnmsg)  
        if self.verify_deadStates(): 
            warnmsg = FSMSysMgs.warning_dead_states(self.dead_states,\
                            self.states[self.index_dict[self.entry_point]])
            logger.warning(warnmsg)
            if self.warnings: 
                warnings.warn(warnmsg) 

        # Check actions
        remain_on_entry = set(self.actions_on_entry.keys())-set(self.states)
        remain_on_exit = set(self.actions_on_exit.keys())-set(self.states)
        remain_on_state = set(self.actions_on_state.keys())-set(self.states)
        remain_on_transition = set(self.actions_on_transition.keys())-set(self.conditions)
        self.invalid_actions = {}
        for m in filter(lambda x: len(x[0]) > 0,
            (
                (remain_on_entry, FSMSysMgs.warning_on_entry_action, 'on_entry'),
                (remain_on_exit, FSMSysMgs.warning_on_exit_action, 'on_exit'),
                (remain_on_state, FSMSysMgs.warning_on_state_action,'on_state'),
                (remain_on_transition, FSMSysMgs.warning_on_transition_action, 'on_transition')
            )
                        ):

            self.invalid_actions[m[-1]] = m[0]

            # if m[-1] not in self.invalid_actions.keys():
            #     self.invalid_actions[m[-1]] = [m[0]]
            # else: 
            #     self.invalid_actions[m[-1]].append(m[0])

            warnmsg = m[1](' '.join(m[0]))
            logger.warning(warnmsg)

            if self.warnings: 
                warnings.warn(warnmsg)

    def verify_deadStates(self)->bool:
        """
        Verifies if there are unreachable 
        states from initial state.
        Note: The list of dead states is available on self.dead_states 

        :return : True if dead states are present
        :rtype : bool

        """
        M = self.get_allPaths()
        self.dead_states.clear() 

        idx = self.index_dict[self.entry_point]
        for k in range(M.shape[0]):
            if (M[idx,k] == 0) and (idx != k):
                self.dead_states.append(self.states[k])

        if len(self.dead_states) > 0: 
            return True
        return False

    def get_allPaths(self)->np.ndarray:
        """
        Calculates accessibility matrix from state transition matrix M nxn: 
        R = M+M^2+M^3+M^4+...+M^n

        :return R: Accesibility Matrix R[i,j], if stat j is reachable from 
                state i, then R[i,j] > 0
        :rtype np.ndarray: nxn Square Matrix

        """
        M = np.not_equal(self.tmatrix, None).astype(int)
        N = M.shape[0]
        R = M.copy()
        P = M.copy()
        for _ in range(N-1):
            R += P 
            P = P@M
        return R

    def detect_closed_cycle(self, max_len:Optional[int]=None)->Optional[List]:
        """
        Detects if exists a closed cycles on state machine.

        :param max_len: max length search on history 
        :type max_len: None (by default) or integer. If None is chosen, length equals to history states length.
        :return: List containing closed cycle. 
        :rtype: None if no cycles or list 

        """
        # Mus filter all None among zeroes
        filtered_history = [past_state for past_state in \
            filter(lambda x: x is not None, self.state_history)]        
        n = len(filtered_history)
        if max_len is None: 
            max_len = n 
        # Trying all possible path lengths
        for len_cycle in range(1, min(max_len, n // 2) + 1):
            cycle = filtered_history[-2 * len_cycle : -len_cycle]  # patrón anterior
            repetition = filtered_history[-len_cycle:]  # patrón actual
            if cycle == repetition:
                return cycle  # Cycle detected
        return None

    def detect_windowed_cycles(self, max_len:Optional[int]=None)->Optional[List[List]]:
        """
        Detects cycles on a window.

        :param max_len: max length search on history 
        :type max_len: None (by default) or integer. If None is chosen, length 
            equals to history states length.
        :return: List containing list of cycles. 
        :rtype: None if no cycles or list 

        """

        filtered_history = [past_state for past_state in \
            filter(lambda x: x is not None, self.state_history)]
        n = len(filtered_history)
        if max_len is None: 
            max_len = n 
        repeated_cycles = []
        for iter_cycle_len in range(1, min(max_len, n // 2) + 1):
            for start_point in range(n - 2 * iter_cycle_len + 1):
                chunk1 = filtered_history[start_point : start_point \
                    + iter_cycle_len]
                chunk2 = filtered_history[start_point + iter_cycle_len \
                    : start_point + 2 * iter_cycle_len]
                if chunk1 == chunk2:
                    repeated_cycles.append(chunk1)
        if len(repeated_cycles ) > 0: 
            return repeated_cycles
        return None

    def set_initialState(self, ep:str):
        """
        Changes entry point (initial state) (first declared by default)
        :param ep: Initial state name
        :type ep: str.

         """
        self.entry_point = ep
        self.state = self.index_dict[ep]
        self.state_history.clear()
        self.state_history.append(self.state)
    
    def printable_history(self)->str:
        """
        Creates a printable history of states.

        :return : History of states 
        :rtype : str

        """
        ptrbl = StringIO()
        print([self.states[x] for x in self.state_history if x is not None],\
              file=ptrbl)
        return ptrbl.getvalue()

    def step(self)-> None:
        """
        Executes one step on FSM

        :return None:
        :rtype: NoneType

        """
        if (f := self.actions_on_state[self.get_state()]) is not None:
            try: 
                if isinstance(f, str): 
                    eval(f)
                else: 
                    f()
            except Exception as e:
                msg = f"On State {self.get_state()} {e}"
                logger.error(msg)
                raise FSMOnEntryActionError(msg)

        self.true_transitions.clear()
        self.true_transitions_name.clear()
        t = ''
        try: 
            for k,t in enumerate(self.tmatrix[self.state,:]):
                tcond = False
                if isinstance(t,str):
                    if isinstance(self.conditions[t], str):
                        tcond = eval(self.conditions[t])
                    elif callable(self.conditions[t]):
                        tcond = self.conditions[t]()

                if tcond: 
                    self.true_transitions.append(k)
                    self.true_transitions_name.append(t)

                    if not self.check_disjoint:
                        break

        except Exception as e: 
                errmsg = FSMSysMgs.error_transition_eval_error(
                        state = self.get_state(), transition = t,
                        eval_fcnexp=self.conditions[t])
                errmsg = str(e) +'\n'+errmsg
                logger.error(errmsg)
                raise FSMTransitionEvalError(errmsg) 

        if len(self.true_transitions) > 1:
            errmsg = FSMSysMgs.error_non_disjoint_transitions(self.get_state(),
                      transitions=str(self.true_transitions_name))
            logger.error(errmsg)
            raise FSMNondisjoinctTransitions(errmsg)

        elif len(self.true_transitions) == 0: 
            return 
        else:
            state_prev = self.get_state() # get previous state name
            self.state = self.true_transitions[0] # change state 
            self.state_history.append(self.state) # get new state name
            state_new = self.get_state()

            # Iterate over 3-tuple containing : 
            # field : transition name, previous state, new state 
            # alist : Action List: On Transition (from old to new state), 
            #         On Exit (from old), On Entry (to new) 
            # except: Exception type 
            #       -FSMOnTransitionActionError: Exception call when transition
            #       -FSMOnExitActionError: Exception call when exits state
            #       -FSMOnEntryActionError: Exception call when enters state
            for field, alist, excpt in zip(
                (self.true_transitions_name[0], state_prev, state_new), 
                (self.actions_on_transition, self.actions_on_exit, 
                 self.actions_on_entry),
                (FSMOnTransitionActionError, FSMOnExitActionError, 
                 FSMOnEntryActionError)):

                try:
                    # Check if action is registered
                    if (f:= alist.get(field)) is not None:
                        if isinstance(f, str):
                            eval(f)
                        else: 
                            f()
                # Manage exception if fails
                except Exception as e: 
                    msg = f'{field}: {e}'
                    logger.error(msg)
                    raise excpt(msg)

            debugmsg = FSMSysMgs.debug_machine_transition(
                                self.states[self.state_history[-2]], 
                                self.tsymbol, 
                                self.states[self.state_history[-1]], 
                                self.true_transitions_name[0])
            logger.debug(debugmsg)
            if self.debug: 
                print(debugmsg)

    def add_action_on_entry(self, state:str, f:Union[str,Callable[...,Any]])->None:
        self.actions_on_entry[state] = f

    def add_action_on_exit(self,state:str, f:Union[str,Callable[...,Any]])->None:
        self.actions_on_exit[state] = f

    def add_action_on_transition(self,t:str, f:Union[str,Callable[...,Any]])->None:
        self.actions_on_transition[t] = f

    def add_action_on_state(self,state:str, f:Union[str,Callable[...,Any]])->None:
        self.actions_on_state[state] = f

    def __repr__(self) -> str:
        msg = f'<class {self.__class__.__name__} at {hex(id(self))}\n\n' 
        msg += 'Description: Finite state machine.\n\n' 
        reprnames = ('machine_trasitions', 'conditions', 'parse_state')
        msg += "State transitions:\n"
        for t in self.machine_trasitions: 
            msg += '\t'+str(t)+'\n'          
        msg += '\nTransition conditions:\n'
        for key,value in self.conditions.items():
            if not callable(value):
                msg += '\t'+key+'::'+str(value)+'\n'
            else:
                fcn_name = re.match(r'<\S+\s+(?P<fcn_name>\w+)', str(value)).groupdict()['fcn_name']
                msg += '\t'+key+'::'+fcn_name+'()\n'

        msg += '\n'
        ivars = sorted(set(self.__dict__.keys()) - set(reprnames))
        custom_repr = ('state','state_history','tmatrix')
        for v in ivars:
            if v not in custom_repr:
                msg += f'{v} : {self.__dict__[v]}\n'
            elif v == 'state': 
                msg += f'{v} : {self.states[self.__dict__[v]]}\n'
            elif v == 'state_history':
                msg += f'{v} : {[self.states[s] for s in filter(lambda x:x is not None, self.state_history)]}\n'
            elif v == 'tmatrix': 
                msg += f'\n{v}:\n\n' + self.printable_matrix(none_as_zero=True)+'\n\n'
                msg += f'\n{"Accesibility Matrix"}:\n\n' + \
                    self.printable_matrix(M = self.get_allPaths(),none_as_zero=True)+'\n\n'
        msg = msg.rstrip()
        msg += ' >\n'
        return msg

    def printable_matrix(self, M: Optional[np.ndarray] = None, none_as_zero: bool = False) -> str:
        """
        Pretty print (pandas like) of a viven matrix

        """
        if M is None:
            M = self.tmatrix
        states = self.states
        N = len(states)

        # Convertimos None a '' o '0' y todo lo demás a string, usando vectorización NumPy
        # Primero creamos una matriz object para convertir sin errores
        M_obj = M.astype(object)

        # Vectorizamos la conversión:
        vec_convert = np.vectorize(lambda x: '0' if (x is None and none_as_zero) else ('' if x is None else str(x)))
        str_matrix = vec_convert(M_obj)

        # Calculamos ancho máximo por columna comparando con headers
        # max len por columna en la matriz
        col_max_len = np.max(np.vectorize(len)(str_matrix), axis=0)
        header_len = np.array([len(s) for s in states])
        column_widths = np.maximum(col_max_len, header_len)
        column_widths = np.maximum(column_widths, 4)  # mínimo ancho 4

        # Ancho fila header
        row_header_width = max(len(s) for s in states) + 2

        output = StringIO()

        # Cabecera columnas
        header = ' ' * row_header_width + ''.join(
            f'{states[i]:>{column_widths[i] + 2}}' for i in range(N)
        )
        print(header, file=output)

        # Construimos las filas vectorizando el formateo (no muy vectorizado para el print final)
        for i in range(N):
            row_str = f'{states[i]:>{row_header_width}}'
            for j in range(N):
                row_str += f'{str_matrix[i, j]:>{column_widths[j] + 2}}'
            print(row_str, file=output)

        return output.getvalue()

def onEnter_A():
    print("Entering state A")
def onEnter_B():
    print("Entering state B")
def onEnter_C():
    print("Entering state C")
def onEnter_D():
    print("Entering state D")

def onState_A():
    print("On state A")
def onState_B():
    print("On state B")
def onState_C():
    print("On state C")
def onState_D():
    print("On state D")

def onExit_A():
    print("Exiting state A")
def onExit_B():
    print("Exiting state B")
def onExit_C():
    print("Exiting state C")
def onExit_D():
    print("Exiting state D")


def onTransition_t0():
    print("Transitioning from state t0")
def onTransition_t1():
    print("Transitioning from state t1")
def onTransition_t2():
    print("Transitioning from state t2")
def onTransition_t3():
    print("Transitioning from state t3")

# simple example 
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

    # f.add_action_on_entry('A', onEnter_A)
    f.add_action_on_entry('B', onEnter_B)
    f.add_action_on_entry('C', onEnter_C)
    f.add_action_on_entry('D', onEnter_D)
    
    f.add_action_on_state('A', onState_A)
    f.add_action_on_state('B', onState_B)
    f.add_action_on_state('C', onState_C)
    f.add_action_on_state('D', onState_D)

    f.add_action_on_exit('A', onExit_A)
    f.add_action_on_exit('B', onExit_B)
    f.add_action_on_exit('C', onExit_C)
    f.add_action_on_exit('D', onExit_D)
    
    f.add_action_on_transition('t0', onTransition_t0)
    f.add_action_on_transition('t1', onTransition_t1)
    f.add_action_on_transition('t2', onTransition_t2)
    f.add_action_on_transition('t3', onTransition_t3)

    f.compile()

    # print(f.invalid_actions)

    a = 0

    for j in range(130): 
        f.step()
        if (j > 100) and (len(f.true_transitions) != 0): 
            break
        a += 1

    print('done')
    print(f)
    print("class printed")

