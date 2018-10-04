from numpy import ones, arange
from numpy.random import choice


def factorial_indices(f1, f2):
    """create full factorial indices from two factors"""
    n1 = len(f1)
    n2 = len(f2)

    f1_ix = (arange(n1).reshape(n1, 1)
             * ones((1, n2), dtype=int)).reshape(n1 * n2)
    f2_ix = (arange(n2).reshape(1, n2)
             * ones((n1, 1), dtype=int)).reshape(n1 * n2)

    return f1_ix, f2_ix


def latin_hyper_index(i1, i2):
    if type(i1) is int:
        i1 = arange(i1)
    if type(i2) is int:
        i2 = arange(i2)

    if len(i2) < len(i1):
        i1, i2 = (i2, i1)
    selection = []
    if isinstance(i1, dict):
        indices = list(i1.keys())
    else:
        indices = arange(len(i1))
    while len(selection) < len(i2):
        num_to_choose = len(i1) if (len(i2) - len(selection)) > len(i1) else len(i2) - len(selection)
        selection += list(choice(indices, num_to_choose, replace=False))

    return selection
