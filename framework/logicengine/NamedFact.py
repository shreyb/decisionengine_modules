# A NamedFact represents one fact known to the LogicEngine.

# The current intent is that user-supplied facts will be expressions
# that can make use of objects that are numpy arrays, or pandas
# dataframes, and can call methods on those obhjects. However, facts
# will not directly make use of functions from either numpy or pandas.
#
# Example expressions for facts:
#   "vals.sum() > 40"   # OK, vals can be a numpy.ndarray
#   "np.sum(vals) > 40" # WRONG, illegal call to np.sum

# If support for direct use of numpy and pandas functions becomes
# wanted, then uncomment the following two import statements, and
# switch the definition of facts_globals to the commented-out
# version.#

import numpy as np
import pandas as pd
facts_globals = {}
#facts_globals = {"np": np, "pd": pd}

class NamedFact(object):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def evaluate(self, d):
        """Return the truth value of this fact, in the context
        of the given data 'd'."""
        return eval(self.expr, facts_globals, d)