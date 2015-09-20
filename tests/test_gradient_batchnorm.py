# ----------------------------------------------------------------------------
# Copyright 2015 Nervana Systems Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------

"""
Generalized gradient testing applied to batchnorm layer
"""

import itertools as itt
import numpy as np
from neon import NervanaObject
from neon.layers.layer import BatchNorm
from tests.grad_funcs import general_gradient_comp


# add a reset methods to the layer classes
# this is used to reset the layer so that
# running fprop and bprop mulitple times
# produces repeatable results
# some layers just need the function defined
class BatchNormWithReset(BatchNorm):
    def reset(self):
        self.allparams = None
        self.x = None
        self.deltas = None


def pytest_generate_tests(metafunc):
    # main test generator
    # generates the parameter combos for
    # the tests based on whether the
    # "--all" option is given to py.test
    # that option is added in conftest.py

    # global parameter
    if metafunc.config.option.all:
        bsz_rng = [16, 32, 64]
    else:
        bsz_rng = [8]

    # mlp tests
    if 'bnargs' in metafunc.fixturenames:
        fargs = []
        if metafunc.config.option.all:
            n = [2, 4, 8, 10, 64, (16, 16, 3), (14, 14, 1)]
        else:
            n = [2, 4]

        # generate the params lists
        fargs = itt.product(n, bsz_rng)

        # parameterize the call for all test functions
        # with mlpargs as an argument
        metafunc.parametrize("bnargs", fargs)


def test_batchnorm(backend_cpu64, bnargs):
    n, batch_size = bnargs
    NervanaObject.be.bsz = NervanaObject.be.batch_size = batch_size

    layer = BatchNormWithReset()
    inp_shape = None
    inp_size = n
    if isinstance(n, tuple):
        inp_shape = n
        from operator import mul
        inp_size = reduce(mul, n)
    inp = np.random.randn(inp_size, batch_size)

    epsilon = 1.0e-5
    pert_frac = 0.1  # test 10% of the inputs
    # select pert_frac fraction of inps to perturb
    pert_cnt = int(np.ceil(inp.size*pert_frac))
    pert_inds = np.random.permutation(inp.size)[0:pert_cnt]

    (max_abs, max_rel) = general_gradient_comp(layer,
                                               inp,
                                               epsilon=epsilon,
                                               lshape=inp_shape,
                                               pert_inds=pert_inds)
    assert max_abs < 1.0e-7
