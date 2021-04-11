from tweetfeed import utils
import numpy as np


def test_set_seed():
    utils.set_seed()
    a = np.random.randn(2, 3)
    b = np.random.randn(2, 3)
    utils.set_seed()
    x = np.random.randn(2, 3)
    y = np.random.randn(2, 3)
    assert np.array_equal(a, x)
    assert np.array_equal(b, y)
