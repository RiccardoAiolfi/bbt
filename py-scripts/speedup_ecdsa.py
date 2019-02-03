#!/usr/bin/env python3

# Copyright (C) 2017-2019 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

import random
import time
from hashlib import sha256 as hf

from btclib.curve import Curve, Point, mult, _double_mult, _mult_jac
from btclib.curves import secp256k1 as ec
from btclib.rfc6979 import _rfc6979
from btclib.dsa import _sign, ECDS, mod_inv


def _verhlp(ec: Curve, e: int, P: Point, sig: ECDS, std: bool = True) -> bool:
    # Private function for test/dev purposes

    r, s = sig

    # Let P = point(pk); fail if point(pk) fails.
    ec.require_on_curve(P)
    if P[1] == 0:
        raise ValueError("public key is infinite")

    if std or r < ec._p - ec.n:
        s1 = mod_inv(s, ec.n)
        u1 = e*s1
        u2 = r*s1                                              # 4
        # Let R = u*G + v*P.
        RJ = _double_mult(ec, u1, ec.GJ, u2, (P[0], P[1], 1))  # 5

        # Fail if infinite(R).
        assert RJ[2] != 0, "how did you do that?!?"            # 5
    else:
        RJ = _double_mult(ec, e, ec.GJ, r, (P[0], P[1], 1))  # 5

        # Fail if infinite(R).
        assert RJ[2] != 0, "how did you do that?!?"            # 5

        try:
            K = r, ec.y(r), 1
            sK = _mult_jac(ec, s, K)
            if (sK[0]*RJ[2]*RJ[2] % ec._p) == (RJ[0]*sK[2]*sK[2] % ec._p):
                return True
        except Exception:
            pass

        s1 = mod_inv(s, ec.n)
        RJ = _mult_jac(ec, s1, RJ)

    Rx = (RJ[0]*mod_inv(RJ[2]*RJ[2], ec._p)) % ec._p
    v = Rx % ec.n                                          # 6, 7
    # Fail if r ≠ x(R) %n.
    return r == v                                          # 8




random.seed(42)

# setup
qs = []
es = []
Qs = []
sigs = []
for _ in range(5):
    q = random.getrandbits(ec.nlen) % ec.n
    qs.append(q)
    Qs.append(mult(ec, q, ec.G))
    e = random.getrandbits(ec.nlen) % ec.n
    es.append(e)
    k = _rfc6979(ec, hf, e, q)
    sigs.append(_sign(ec, e, q, k))

start = time.time()
for i in range(len(qs)):
    assert _verhlp(ec, es[i], Qs[i], sigs[i], True)
elapsed1 = time.time() - start

start = time.time()
for i in range(len(qs)):
    assert _verhlp(ec, es[i], Qs[i], sigs[i], False)
elapsed2 = time.time() - start

print(elapsed2 / elapsed1)
