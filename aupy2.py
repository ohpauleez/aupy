#!/usr/bin/env python

"""Aupy 2.0
Author: Paul deGrandis
Created: June 02 2008

Requires Python 2.5
Copyright (c) 2008 Paul deGrandis // aupy.org

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from __future__ import with_statement
import sys
if sys.version < '2.5':
    print "Aupy 2.0 requires Python 2.5 or higher"
    sys.exit(1)

from threading import Thread
from contextlib import contextmanager
from functools import wraps



class RegisterUtilityMethods(type):
    """A metaclass to auto register utility methods"""
    def __new__(mcls, classname, bases, classdict):
        """Auto register all utility methods
        Do this in a similar manner as the earlier version of Aupy did"""

        utilMeths = classdict.setdefault("_utilityMethods", [])
        for item in classdict.values():
            if callable(item) and hasattr(item, "_utilitySpecs"):
                utilMeths.append(item)
        return super(RegisterUtilityMethods, mcls).__new__(mcls, classname, bases, classdict)


class Utility(object):
    """A class containing all necessary functionality for 
    utility creation and interaction."""

    class UtilityError(Exception):
        """A class for general utility method errors"""
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    
    class UtilityMethodsMixIn(object):
        """This mixin provides the extra functionality for classes
        that contain Utility Methods.
        Currently this is only auto Utility Method Registration."""
        __metaclass__ = RegisterUtilityMethods

        def __init__(self):
            super(UtilityMethodsMixIn, self).__init__()

    @staticmethod
    def isValidUtilityMethod(func):
        """Allows reflection to work on utility methods; 
        Answers: 'Could this be a utility method?'"""
        return hasattr(func, "_utilitySpecs")

    @staticmethod
    def isUtilityMethod(func, self_or_dict=[]):
        """Checks the current registered functions to see if
        a given function is a known utility method.
        Please also see isValidUtilityMethod.

        Arguments:
            func - the function in question
            [self_or_dict] - an object's identity reference or dictionary (for scoping)
        Returns:
            result - a boolean"""
        return func in Utility.getAllRegisteredUtilityFunctions(self_or_dict)
        
    @staticmethod
    def checkUtilityResult(utilityFunc, *args, **kwargs):
        """Evaluate a utility function's result against a specific evaluation function.
        The evaluation function can be used to specify thresholds, but by default
        uses the bool function.  All callback info is removed before evaluation.

        Arguments:
            utilityFunc - the function to call to generate the result; the utility function
            [evalFunc] - the evaluation function for utilityFunc's result
                        THIS MUST BE PASSED AS A KEYWORD ARG!
                        IT WILL GET POPPED BEFORE f IS EVALUATED; IT WILL NOT BE IN f's KWARGS!
        Returns:
            func_result - the function's, utilityFunc's, result
        Raises:
            Utility.UtilityError if utilityFunc's result fails the evaluation"""
        evalFunc = kwargs.pop("evalFunc", bool)
        #remove all callback related args:
        cb = kwargs.pop("utilityCallback", None)
        cb_args = kwargs.pop("utilityCallbackArgs", None)
        func_result = utilityFunc(*args, **kwargs)
        utility_result = evalFunc(func_result)
        if not utility_result:
            raise Utility.UtilityError
        return func_result

    @staticmethod
    def handleCallback(*args, **kwargs):
        """Handle callbacks for Utility Exceptions.
        This is mostly used internally for contexts, but can be used by developers.
        
        Arguments (All must be passed via keyword arguments):
            [utilityCallback] - the callback function; If not specified, no callback will take place
            [utilityCallbackArgs] - arguments to pass to the callback function, if not specified,
                                    the args pass to this handler will be used
        Returns:
            utilityCallback(utilityCallbackArgs)
        Raises:
            raise - if no callback is specified, a call to raise takes place.
                    This is because this is mostly used within contexts, where
                    this behavior makes sense (an exception within the user-defined block)"""
        utilityCallback = kwargs.get("utilityCallback", None)
        if utilityCallback:
            utilityCallbackArgs = kwargs.get("utilityCallbackArgs", args)
            return utilityCallback(*utilityCallbackArgs)
        else:
            raise

    @staticmethod
    def _dictOrGlobals(f, args):
        """This is used to establish scoping attributes
        and is only intended to be used by utility and monitor decorators.

        Arguments:
            f - the function who needs to get access to _dictOrGlobals
                in a decorator, this is the function passed in.
            args - the list/tuple of args passed to a function/method
        Returns:
            self_dict - a dictionary that is either globals() or class/obj dict"""
        #return len(args)>0 and hasattr(args[0], f.__name__) and args[0].__dict__ or globals()
        if len(args) > 0 and hasattr(args[0], f.__name__):
            return args[0].__dict__
        return globals()
    
    @staticmethod
    def getAllRegisteredUtilityFunctions(self_or_dict=None):
        """Returns all utility functions within all given scopes.
            Scope is determined by a function object passed in.

        Arguments:
            self_or_dict - the object's identity reference or the object's dictionary
        Returns:
            all_utils - list of all available utility functions"""
        class_utils = []
        if type(self_or_dict) is dict:
            class_utils = self_or_dict.get("_utilityMethods", [])
        else:
            class_utils = hasattr(self_or_dict, "_utilityMethods") and self_or_dict._utilityMethods or []
        glob_utils = globals().get("_utilityMethods", [])
        all_utils = glob_utils + class_utils
        return all_utils
    
    @staticmethod
    def registerAllGlobalUtilityFunctions():
        """Registers Global space utility functions
        This is instead of runtime discovery"""
        glob_dict = globals()
        meths = glob_dict.setdefault("_utilityMethods", [])
        for elem in glob_dict:
            elem = glob_dict.get(elem)
            if callable(elem) and Utility.isValidUtilityMethod(elem):
                meths.append(elem)

    @staticmethod
    def sortUtilityFunctions(all_utils):
        """Sort out all pre, post, and concurrent utility functions

        Arguments:
            all_utils - a list of valid utility functions
        Returns:
            pre_utils, post_utils, concurrent_utils - lists of utility functions"""
        if len(all_utils) < 1:
            return [], [], []
        util_funcs = filter(Utility.isValidUtilityMethod, all_utils)
        pre_utils, post_utils, concurrent_utils = [], [], []
        for func in util_funcs:
            if func._utilitySpecs.get("pre", False):
                pre_utils.append(func)
            if func._utilitySpecs.get("post", False):
                post_utils.append(func)
            if func._utilitySpecs.get("concurrent", False):
                conncurrent_utils.append(func)
        return pre_utils, post_utils, concurrent_utils

    ## --- UTILITY DECORATORS --- ##
    @staticmethod
    def utility(f):
        """A decorator to mark a function or method as a utility method.

        This is to be used with the @monitor decorator.
        If a global function is decorated, it'll be available in global scope to all monitored methods.
        If a method is decorated, it'll be available in class scope to monitored methods."""
        @wraps(f)
        def new_util_f(*args, **kwargs):
            # Get the global dictionary or the class/obj dictionary...
            self_dict = Utility._dictOrGlobals(f, args)
            # Check to see if we're already recorded, if so, remove so we can re-add
            if hasattr(self_dict, '_utilityMethods'):
                if f in self_dict["_utilityMethods"]:
                    self_dict["_utilityMethods"].remove(f)
            else:
                # Since we're not recording utils, start
                self_dict['_utilityMethods'] = []
            self_dict["_utilityMethods"].append(f)
            return f(*args, **kwargs)
        new_util_f._utilitySpecs={"pre":True, "post":True, "concurrent":False}
        return new_util_f

    @staticmethod
    def pre_utility(f):
        """A decorator to mark a function or method as a pre utility method.
        See the utility method decorator for more information."""
        pre_util_ret = utility(f)
        pre_util_ret._utilitySpecs["post"] = False
        return pre_util_return

    @staticmethod
    def post_utility(f):
        """A decorator to mark a function or method as a post utility method.
        See the utility method decorator for more information."""
        post_util_ret = utility(f)
        post_util_ret._utilitySpecs["pre"] = False
        return post_util_return

    @staticmethod
    def concurrent_utility(f):
        """A decorator to mark a function or method as a concurrent utility method.
        See the utility method decorator for more information."""
        con_util_ret = utility(f)
        con_util_ret._utilitySpecs["pre"] = False
        con_util_ret._utilitySpecs["post"] = False
        con_util_ret._utilitySpecs["concurent"] = True
        return con_util_return

    ## --- CONTEXTS --- ##
    @staticmethod
    @contextmanager
    def contextUtility(utilityFunc, *args, **kwargs):
        """A context for block-wise utility.

        This method will evaluate your function result with a keyword
        arg passed function, evalFunc.  If this is not passed in,
        the function result is evaluted with bool.  A Utility.UtilityError
        is raised if the result fails the evaluation.  Otherwise
        the developer must raise UtilityError or some child thereof
        within the function (for finer control)

        Support for callbacks are via any callable object passed in as
        a kwarg as 'utilityCallback'.  Args to this callable can be passed
        in as 'utilityCallbackArgs'.  If no callback args are passed, the
        arg list passed to the function will be passed onto the callback.
        If the first utility check fails, a UtilityError will be yielded.

        Arguments:
            utilityFunc - a utility function used for evalutation,
                This function does not have to be decorated as utility, it can be any function whatsoever
            args - collection of args, passed to the function, utilityFunc
            kwargs - a dictionary of keyword args, passed to the function, utilityFunc
        Yields:
            The result of the first evaluation of your function, utilityFunc
            If the pre evaluated context fails, a UtilityError will be yielded; check for it!"""
        has_yielded = False
        try:
            utility_result = Utility.checkUtilityResult(utilityFunc, *args, **kwargs)
            yield utility_result
            has_yielded = True
            utility_result = Utility.checkUtilityResult(utilityFunc, *args, **kwargs)
        except Utility.UtilityError:
            Utility.handleCallback(*args, **kwargs)
            if not has_yielded:
                yield Utility.UtilityError("Your pre-evaluated context failed")

    @staticmethod
    @contextmanager
    def contextPreUtility(utilityFunc, *args, **kwargs):
        """A context for block-wise pre-utility.

        This method will evaluate your function result with a keyword
        arg passed function, evalFunc.  If this is not passed in,
        the function result is evaluted with bool.  A Utility.UtilityError
        is raised if the result fails the evaluation.  Otherwise
        the developer must raise UtilityError or some child thereof
        within the function (for finer control)

        Support for callbacks are via any callable object passed in as
        a kwarg as 'utilityCallback'.  Args to this callable can be passed
        in as 'utilityCallbackArgs'.  If no callback args are passed, the
        arg list passed to the function will be passed onto the callback.
        If the first utility check fails, a UtilityError will be yielded.

        Arguments:
            utilityFunc - a utility function used for evalutation,
                This function does not have to be decorated as utility, it can be any function whatsoever
            args - collection of args, passed to the function, utilityFunc
            kwargs - a dictionary of keyword args, passed to the function, utilityFunc
        Yields:
            The result of the first evaluation of your function, utilityFunc
            If the pre evaluated context fails, a UtilityError will be yielded; check for it!"""
        has_yielded = False
        try:
            utility_result = Utility.checkUtilityResult(utilityFunc, *args, **kwargs)
            yield utility_result
            has_yielded = True
        except Utility.UtilityError:
            Utility.handleCallback(*args, **kwargs)
            if not has_yielded:
                yield Utility.UtilityError("Your pre-evaluated context failed")

    @staticmethod
    @contextmanager
    def contextPostUtility(utilityFunc, *args, **kwargs):
        """A context for block-wise post-utility.

        This method will evaluate your function result with a keyword
        arg passed function, evalFunc.  If this is not passed in,
        the function result is evaluted with bool.  A Utility.UtilityError
        is raised if the result fails the evaluation.  Otherwise
        the developer must raise UtilityError or some child thereof
        within the function (for finer control)

        Support for callbacks are via any callable object passed in as
        a kwarg as 'utilityCallback'.  Args to this callable can be passed
        in as 'utilityCallbackArgs'.  If no callback args are passed, the
        arg list passed to the function will be passed onto the callback.

        Arguments:
            utilityFunc - a utility function used for evalutation,
                This function does not have to be decorated as utility, it can be any function whatsoever
            args - collection of args, passed to the function, utilityFunc
            kwargs - a dictionary of keyword args, passed to the function, utilityFunc
        Yields:
            The result of the first evaluation of your function, utilityFunc"""
        try:
            yield utility_result
            utility_result = Utility.checkUtilityResult(utilityFunc, *args, **kwargs)
        except Utility.UtilityError:
            Utility.handleCallback(*args, **kwargs)

    @staticmethod
    @contextmanager
    def contextConcurrentUtility(utilityFunc, *args, **kwargs):
        """A context for block-wise concurrent-utility.

        This method will evaluate your function result with a keyword
        arg passed function, evalFunc.  If this is not passed in,
        the function result is evaluted with bool.  A Utility.UtilityError
        is raised if the result fails the evaluation.  Otherwise
        the developer must raise UtilityError or some child thereof
        within the function (for finer control)

        Support for callbacks are via any callable object passed in as
        a kwarg as 'utilityCallback'.  Args to this callable can be passed
        in as 'utilityCallbackArgs'.  If no callback args are passed, the
        arg list passed to the function will be passed onto the callback.

        Arguments:
            utilityFunc - a utility function used for evalutation,
                This function does not have to be decorated as utility, it can be any function whatsoever
            args - collection of args, passed to the function, utilityFunc
            kwargs - a dictionary of keyword args, passed to the function, utilityFunc
        Yields:
            concurrent utility thread start() status"""
        try:
            t = Thread(target=utilityFunc, name=f.__name__+"_ContextThread", args=args, kwargs=kwargs)
            t.setDaemon(True)
            yield t.start()
            #TODO Kill the thread here, perhaps we need to make a new killable Thread class
            #       (or one that just returns the threads pid, so we can os.popen("kill %d"% t_pid)
            # Ideally a coroutine setup would rock, or some single thread solution.
        except:
            Utility.handleCallback(*args, **kwargs)
    
    ## --- MONITOR DECORATOR --- ##
    ## ___   The Heart   ___ ##
    @staticmethod
    def monitor(f, *utility_funcs):
        """Decorates methods or functions that should be monitored and verified
        by utility functions (those decorated with @utility or similar)

        Arguments:
            *util_funcs - the utility functions that should monitor this operations
                If absent or passed as None, ALL availble utility functions in class wide
                and global scope will be used..
        Notes:
            If you monitor a global function, only global utility functions will be available
            If you monitor a method, class wide and global utility functions are available"""
        @wraps(f)
        def new_monitor_f(*args, **kwargs):
            meth_return = None
            util_funcs = utility_funcs
            if (util_funcs == ()) or (None in util_funcs):
                if len(args) > 0 and f.__name__ in dir(args[0]):
                    util_funcs = Utility.getAllRegisteredUtilityFunctions(args[0])
                else:
                    util_funcs = Utility.getAllRegisteredUtilityFunctions()
            #Filter and sort the functions
            pre_utils, post_utils, concurrent_utils = Utility.sortUtilityFunctions(util_funcs)

            for func in pre_utils:
                if not func(*args, **kwargs):
                    raise UtilityError("Pre-Utility failed for: %s" % func.__name__)
            
            #TODO This needs to be replaced with killable threads or ideally a coroutine setup
            #       (or one that just returns the threads pid, so we can os.popen("kill %d"% t_pid)
            for func in concurrent_utils:
                t = Thread(target=func, name=func.__name__+"_ConncurrentUtilThread", args=args, kwargs=kwargs)
                t.setDaemon(True)
                t.start()
            
            meth_return = f(*args, **kwargs)

            for func in post_utils:
                if not func(*args, **kwargs):
                    raise UtilityError("Post-Utility failed for: %s" % func.__name__)

            return meth_return
        return new_monitor_f


if __name__ == "__main__":

    Utility.registerAllGlobalUtilityFunctions()

    class TempObj(object):
        __metaclass__ = RegisterUtilityMethods
        
        @Utility.monitor
        def testMonMeth(self):
            print "utils1:", Utility.getAllRegisteredUtilityFunctions(self)
            print "monitoring..."
        @Utility.utility
        def testMeth(self, arg1=1):
            print "testMeth talking..."
            return True


    print "utils2:", Utility.getAllRegisteredUtilityFunctions()
    to = TempObj()
    to.testMonMeth()

    @Utility.utility
    def testFunc(arg1=1):
        print "this is a function"
        return True

    testFunc()
    print "utils:3", Utility.getAllRegisteredUtilityFunctions()
    
    class TempObj2(object):
        @Utility.utility
        def testMeth(self, arg1=1):
            print "testMeth2 talking..."
            print "utils4:", Utility.getAllRegisteredUtilityFunctions(self)
            return True
    to2 = TempObj2()
    to2.testMeth()
    print "utils5:", Utility.getAllRegisteredUtilityFunctions()


    def contextual_utility(arg1):
        return arg1[1:]

    with Utility.contextUtility(contextual_utility, [1,3,5], evalFunc=bool) as status:
        print "your status is:", status
        

    print "done"



