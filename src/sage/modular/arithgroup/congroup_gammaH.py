r"""
Congruence Subgroup `\Gamma_H(N)`

AUTHORS:

- Jordi Quer

- David Loeffler
"""

################################################################################
#
#       Copyright (C) 2009, The Sage Group -- http://www.sagemath.org/
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#  The full text of the GPL is available at:
#
#                  http://www.gnu.org/licenses/
#
################################################################################

from sage.rings.arith import euler_phi, lcm, gcd, divisors, get_inverse_mod, get_gcd, factor
from sage.modular.modsym.p1list import lift_to_sl2z
from congroup_generic import CongruenceSubgroup, is_CongruenceSubgroup
from arithgroup_element import ArithmeticSubgroupElement
from sage.modular.cusps import Cusp
from sage.misc.cachefunc import cached_method

# Just for now until we make an SL_2 group type.
from sage.rings.integer_ring import ZZ
from sage.rings.finite_rings.integer_mod_ring import IntegerModRing
from sage.matrix.matrix_space import MatrixSpace

Mat2Z = MatrixSpace(ZZ,2)


_gammaH_cache = {}
def GammaH_constructor(level, H):
    r"""
    Return the congruence subgroup `\Gamma_H(N)`, which is the subgroup of
    `SL_2(\ZZ)` consisting of matrices of the form `\begin{pmatrix} a & b \\
    c & d \end{pmatrix}` with `N | c` and `a, b \in H`, for `H` a specified
    subgroup of `(\ZZ/N\ZZ)^\times`.

    INPUT:

    - level -- an integer
    - H -- either 0, 1, or a list
        * If H is a list, return `\Gamma_H(N)`, where `H`
          is the subgroup of `(\ZZ/N\ZZ)^*` **generated** by the
          elements of the list.
        * If H = 0, returns `\Gamma_0(N)`.
        * If H = 1, returns `\Gamma_1(N)`.

    EXAMPLES::

        sage: GammaH(11,0) # indirect doctest
        Congruence Subgroup Gamma0(11)
        sage: GammaH(11,1)
        Congruence Subgroup Gamma1(11)
        sage: GammaH(11,[2])
        Congruence Subgroup Gamma_H(11) with H generated by [2]
        sage: GammaH(11,[2,1])
        Congruence Subgroup Gamma_H(11) with H generated by [2]
        sage: GammaH(14,[10])
        Traceback (most recent call last):
        ...
        ArithmeticError: The generators [10] must be units modulo 14
    """
    from all import Gamma0, Gamma1, SL2Z
    if level == 1:
        return SL2Z
    elif H == 0:
        return Gamma0(level)
    elif H == 1:
        return Gamma1(level)

    H = _normalize_H(H, level)

    key = (level, tuple(H))
    try:
        return _gammaH_cache[key]
    except KeyError:
        _gammaH_cache[key] = GammaH_class(level, H)
        return _gammaH_cache[key]

def is_GammaH(x):
    """
    Return True if x is a congruence subgroup of type GammaH.

    EXAMPLES::

        sage: from sage.modular.arithgroup.all import is_GammaH
        sage: is_GammaH(GammaH(13, [2]))
        True
        sage: is_GammaH(Gamma0(6))
        True
        sage: is_GammaH(sage.modular.arithgroup.congroup_generic.CongruenceSubgroup(5))
        False
    """
    return isinstance(x, GammaH_class)

def _normalize_H(H, level):
    """
    Normalize representatives for a given subgroup H of the units
    modulo level.

    NOTE: This function does *not* make any attempt to find a minimal
    set of generators for H. It simply normalizes the inputs for use
    in hashing.

    EXAMPLES::

        sage: sage.modular.arithgroup.congroup_gammaH._normalize_H([23], 10)
        [3]
        sage: sage.modular.arithgroup.congroup_gammaH._normalize_H([1,5], 7)
        [5]
        sage: sage.modular.arithgroup.congroup_gammaH._normalize_H([4,18], 14)
        Traceback (most recent call last):
        ...
        ArithmeticError: The generators [4, 18] must be units modulo 14
        sage: sage.modular.arithgroup.congroup_gammaH._normalize_H([3,17], 14)
        [3]
        sage: sage.modular.arithgroup.congroup_gammaH._normalize_H([-1,7,9], 10)
        [7, 9]
    """
    if not isinstance(H, list):
        raise TypeError, "H must be a list."
    H = [ZZ(h) for h in H]
    for h in H:
        if gcd(h, level) > 1:
            raise ArithmeticError, 'The generators %s must be units modulo %s'%(H, level)
    H = list(set([h%level for h in H]))
    H.sort()
    if 1 in H:
        H.remove(1)
    return H

class GammaH_class(CongruenceSubgroup):

    r"""
    The congruence subgroup `\Gamma_H(N)` for some subgroup `H \trianglelefteq
    (\ZZ / N\ZZ)^\times`, which is the subgroup of `{\rm
    SL}_2(\ZZ)` consisting of matrices of the form `\begin{pmatrix} a &
    b \\ c & d \end{pmatrix}` with `N \mid c` and `a, b \in H`.

    TESTS:

    We test calculation of various invariants of the group: ::

        sage: GammaH(33,[2]).projective_index()
        96
        sage: GammaH(33,[2]).genus()
        5
        sage: GammaH(7,[2]).genus()
        0
        sage: GammaH(23, [1..22]).genus()
        2
        sage: Gamma0(23).genus()
        2
        sage: GammaH(23, [1]).genus()
        12
        sage: Gamma1(23).genus()
        12

    We calculate the dimensions of some modular forms spaces: ::

        sage: GammaH(33,[2]).dimension_cusp_forms(2)
        5
        sage: GammaH(33,[2]).dimension_cusp_forms(3)
        0
        sage: GammaH(33,[2,5]).dimension_cusp_forms(2)
        3
        sage: GammaH(32079, [21676]).dimension_cusp_forms(20)
        180266112

    We can sometimes show that there are no weight 1 cusp forms: ::

        sage: GammaH(20, [9]).dimension_cusp_forms(1)
        0

    """

    def __init__(self, level, H):
        r"""
        The congruence subgroup `\Gamma_H(N)`. The subgroup H
        must be input as a list.

        EXAMPLES::

            sage: GammaH(117, [4])
            Congruence Subgroup Gamma_H(117) with H generated by [4]
            sage: G = GammaH(16, [7])
            sage: G == loads(dumps(G))
            True
            sage: G is loads(dumps(G))
            True
        """
        CongruenceSubgroup.__init__(self, level)
        self.__H = _normalize_H(H, level)

    def restrict(self, M):
        r"""
        Return the subgroup of `\Gamma_0(M)`, for `M` a divisor of `N`,
        obtained by taking the image of this group under reduction modulo `N`.

        EXAMPLES::

            sage: G = GammaH(33,[2])
            sage: G.restrict(11)
            Congruence Subgroup Gamma_H(11) with H generated by [2]
            sage: G.restrict(1)
            Modular Group SL(2,Z)
            sage: G.restrict(15)
            Traceback (most recent call last):
            ...
            ValueError: M (=15) must be a divisor of the level (33) of self
        """
        M = ZZ(M)
        if self.level() % M:
            raise ValueError, "M (=%s) must be a divisor of the level (%s) of self" % (M, self.level())
        return self._new_group_from_level(M)

    def extend(self, M):
        r"""
        Return the subgroup of `\Gamma_0(M)`, for `M` a multiple of `N`,
        obtained by taking the preimage of this group under the reduction map;
        in other words, the intersection of this group with `\Gamma_0(M)`.

        EXAMPLES::

            sage: G = GammaH(33, [2])
            sage: G.extend(99)
            Congruence Subgroup Gamma_H(99) with H generated by [2, 35, 68]
            sage: G.extend(11)
            Traceback (most recent call last):
            ...
            ValueError: M (=11) must be a multiple of the level (33) of self

        """
        M = ZZ(M)
        if M % self.level():
            raise ValueError, "M (=%s) must be a multiple of the level (%s) of self" % (M, self.level())
        return self._new_group_from_level(M)

    def __reduce__(self):
        """
        Used for pickling self.

        EXAMPLES::

            sage: GammaH(92,[5,11]).__reduce__()
            (<function GammaH_constructor at ...>, (92, [5, 11]))
        """
        return GammaH_constructor, (self.level(), self.__H)

    def divisor_subgroups(self):
        r"""
        Given this congruence subgroup `\Gamma_H(N)`, return all
        subgroups `\Gamma_G(M)` for `M` a divisor of `N` and such that
        `G` is equal to the image of `H` modulo `M`.

        EXAMPLES::

            sage: G = GammaH(33,[2]); G
            Congruence Subgroup Gamma_H(33) with H generated by [2]
            sage: G._list_of_elements_in_H()
            [1, 2, 4, 8, 16, 17, 25, 29, 31, 32]
            sage: G.divisor_subgroups()
            [Modular Group SL(2,Z),
             Congruence Subgroup Gamma_H(3) with H generated by [2],
             Congruence Subgroup Gamma_H(11) with H generated by [2],
             Congruence Subgroup Gamma_H(33) with H generated by [2]]
        """
        v = self.__H
        ans = []
        for M in self.level().divisors():
            w = [a % M for a in v if a%M]
            ans.append(GammaH_constructor(M, w))
        return ans

    def __cmp__(self, other):
        """
        Compare self to other.

        The ordering on congruence subgroups of the form GammaH(N) for
        some H is first by level and then by the subgroup H. In
        particular, this means that we have Gamma1(N) < GammaH(N) <
        Gamma0(N) for every nontrivial subgroup H.

        EXAMPLES::

            sage: G = GammaH(86, [9])
            sage: G.__cmp__(G)
            0
            sage: G.__cmp__(GammaH(86, [11])) is not 0
            True
            sage: Gamma1(11) < Gamma0(11)
            True
            sage: Gamma1(11) == GammaH(11, [])
            True
            sage: Gamma0(11) == GammaH(11, [2])
            True
        """
        if not is_CongruenceSubgroup(other):
            return cmp(type(self), type(other))

        c = cmp(self.level(), other.level())
        if c: return c

        if is_GammaH(other):
            return cmp(self._list_of_elements_in_H(), other._list_of_elements_in_H())
        return cmp(type(self), type(other))

    def _generators_for_H(self):
        """
        Return generators for the subgroup H of the units mod
        self.level() that defines self.

        EXAMPLES::

            sage: GammaH(17,[4])._generators_for_H()
            [4]
            sage: GammaH(12,[-1])._generators_for_H()
            [11]
        """
        return self.__H

    def _repr_(self):
        """
        Return the string representation of self.

        EXAMPLES::

            sage: GammaH(123, [55])._repr_()
            'Congruence Subgroup Gamma_H(123) with H generated by [55]'
        """
        return "Congruence Subgroup Gamma_H(%s) with H generated by %s"%(self.level(), self.__H)

    def _latex_(self):
        r"""
        Return the \LaTeX representation of self.

        EXAMPLES::

            sage: GammaH(3,[2])._latex_()
            '\\Gamma_H(3)'
        """
        return "\\Gamma_H(%s)"%self.level()

    @cached_method
    def _list_of_elements_in_H(self):
        """
        Returns a sorted list of Python ints that are representatives
        between 1 and N-1 of the elements of H.

        WARNING: Do not change this returned list.

        EXAMPLES::

            sage: G = GammaH(11,[3]); G
            Congruence Subgroup Gamma_H(11) with H generated by [3]
            sage: G._list_of_elements_in_H()
            [1, 3, 4, 5, 9]
        """
        N = self.level()
        if N == 1:
            return [1]
        gens = self.__H

        H = set([1])
        N = int(N)
        for g in gens:
            if gcd(g, N) != 1:
                raise ValueError, "gen (=%s) is not in (Z/%sZ)^*"%(g,N)
            gk = int(g) % N
            sbgrp = [gk]
            while not (gk in H):
                gk = (gk * g)%N
                sbgrp.append(gk)
            H = set([(x*h)%N for x in sbgrp for h in H])
        H = list(H)
        H.sort()
        return H

    def is_even(self):
        """
        Return True precisely if this subgroup contains the matrix -1.

        EXAMPLES::

            sage: GammaH(10, [3]).is_even()
            True
            sage: GammaH(14, [1]).is_even()
            False
        """
        if self.level() == 1:
            return True
        v = self._list_of_elements_in_H()
        return int(self.level() - 1) in v

    @cached_method
    def generators(self):
        r"""
        Return generators for this congruence subgroup.

        The result is cached.

        EXAMPLE::

            sage: for g in GammaH(3, [2]).generators():
            ...     print g
            ...     print '---'
            [1 1]
            [0 1]
             ---
            [-1  0]
            [ 0 -1]
            ---
            [ 1 -1]
            [ 0  1]
            ---
            [1 0]
            [3 1]
            ---
            [1 1]
            [0 1]
            ---
            [-1  0]
            [ 3 -1]
            ---
            [ 1  0]
            [-3  1]
            ---
        """
        from sage.modular.modsym.ghlist import GHlist
        from congroup_pyx import generators_helper
        level = self.level()
        gen_list = generators_helper(GHlist(self), level, Mat2Z)
        return [self(g, check=False) for g in gen_list]

    def _coset_reduction_data_first_coord(G):
        """
        Compute data used for determining the canonical coset
        representative of an element of SL_2(Z) modulo G. This
        function specifically returns data needed for the first part
        of the reduction step (the first coordinate).

        INPUT:
            G -- a congruence subgroup Gamma_0(N), Gamma_1(N), or Gamma_H(N).

        OUTPUT:
            A list v such that
                v[u] = (min(u*h: h in H),
                        gcd(u,N) ,
                        an h such that h*u = min(u*h: h in H)).

        EXAMPLES::

            sage: G = GammaH(12,[-1,5]); G
            Congruence Subgroup Gamma_H(12) with H generated by [5, 11]
            sage: G._coset_reduction_data_first_coord()
            [(0, 12, 0), (1, 1, 1), (2, 2, 1), (3, 3, 1), (4, 4, 1), (1, 1, 5), (6, 6, 1),
            (1, 1, 7), (4, 4, 5), (3, 3, 7), (2, 2, 5), (1, 1, 11)]
        """
        H = [ int(x) for x in G._list_of_elements_in_H() ]
        N = int(G.level())

        # Get some useful fast functions for inverse and gcd
        inverse_mod = get_inverse_mod(N)   # optimal inverse function
        gcd = get_gcd(N)   # optimal gcd function

        # We will be filling this list in below.
        reduct_data = [0] * N

        # We can fill in 0 and all elements of H immediately
        reduct_data[0] = (0,N,0)
        for u in H:
            reduct_data[u] = (1, 1, inverse_mod(u, N))

        # Make a table of the reduction of H (mod N/d), one for each
        # divisor d.
        repr_H_mod_N_over_d = {}
        for d in divisors(N):
            # We special-case N == d because in this case,
            # 1 % N_over_d is 0
            if N == d:
                repr_H_mod_N_over_d[d] = [1]
                break
            N_over_d = N//d
            # For each element of H, we look at its image mod
            # N_over_d. If we haven't yet seen it, add it on to
            # the end of z.
            w = [0] * N_over_d
            z = [1]
            for x in H:
                val = x%N_over_d
                if not w[val]:
                    w[val] = 1
                    z.append(x)
            repr_H_mod_N_over_d[d] = z

        # Compute the rest of the tuples. The values left to process
        # are those where reduct_data has a 0. Note that several of
        # these values are processed on each loop below, so re-index
        # each time.
        while True:
            try:
                u = reduct_data.index(0)
            except ValueError:
                break
            d = gcd(u, N)
            for x in repr_H_mod_N_over_d[d]:
                reduct_data[(u*x)%N] = (u, d, inverse_mod(x,N))

        return reduct_data

    def _coset_reduction_data_second_coord(G):
        """
        Compute data used for determining the canonical coset
        representative of an element of SL_2(Z) modulo G. This
        function specifically returns data needed for the second part
        of the reduction step (the second coordinate).

        INPUT:
            self

        OUTPUT:
            a dictionary v with keys the divisors of N such that v[d]
            is the subgroup {h in H : h = 1 (mod N/d)}.

        EXAMPLES::

            sage: G = GammaH(240,[7,239])
            sage: G._coset_reduction_data_second_coord()
            {1: [1], 2: [1], 3: [1], 4: [1], 5: [1, 49], 6: [1], 48: [1, 191], 8: [1], 80: [1, 7, 49, 103], 10: [1, 49], 12: [1], 15: [1, 49], 240: [1, 7, 49, 103, 137, 191, 233, 239], 40: [1, 7, 49, 103], 20: [1, 49], 24: [1, 191], 120: [1, 7, 49, 103, 137, 191, 233, 239], 60: [1, 49, 137, 233], 30: [1, 49, 137, 233], 16: [1]}
            sage: G = GammaH(1200,[-1,7]); G
            Congruence Subgroup Gamma_H(1200) with H generated by [7, 1199]
            sage: K = G._coset_reduction_data_second_coord().keys() ; K.sort()
            sage: K == divisors(1200)
            True
        """
        H = G._list_of_elements_in_H()
        N = G.level()
        v = { 1: [1] , N: H }
        for d in [x for x in divisors(N) if x > 1 and x < N ]:
            N_over_d = N // d
            v[d] = [x for x in H if x % N_over_d == 1]
        return v

    @cached_method
    def _coset_reduction_data(self):
        """
        Compute data used for determining the canonical coset
        representative of an element of SL_2(Z) modulo G.

        EXAMPLES::

            sage: G = GammaH(12,[-1,7]); G
            Congruence Subgroup Gamma_H(12) with H generated by [7, 11]
            sage: G._coset_reduction_data()
            ([(0, 12, 0), (1, 1, 1), (2, 2, 1), (3, 3, 1), (4, 4, 1), (1, 1, 5), (6, 6, 1), (1, 1, 7), (4, 4, 5), (3, 3, 7), (2, 2, 5), (1, 1, 11)],
            {1: [1], 2: [1, 7], 3: [1, 5],  4: [1, 7], 6: [1, 5, 7, 11], 12: [1, 5, 7, 11]})
        """
        return (self._coset_reduction_data_first_coord(),
                                       self._coset_reduction_data_second_coord())


    def _reduce_coset(self, uu, vv):
        r"""
        Compute a canonical form for a given Manin symbol.

        INPUT:
        Two integers (uu,vv) that define an element of `(Z/NZ)^2`.
            uu -- an integer
            vv -- an integer

        OUTPUT:
           pair of integers that are equivalent to (uu,vv).

        NOTE: We do *not* require that gcd(uu,vv,N) = 1.  If the gcd is
        not 1, we return (0,0).

        EXAMPLES:

        An example at level 9.::

            sage: G = GammaH(9,[7]); G
            Congruence Subgroup Gamma_H(9) with H generated by [7]
            sage: a = []
            sage: for i in range(G.level()):
            ...     for j in range(G.level()):
            ...       a.append(G._reduce_coset(i,j))
            sage: v = list(set(a))
            sage: v.sort()
            sage: v
            [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (3, 1), (3, 2), (6, 1), (6, 2)]

        An example at level 100::

            sage: G = GammaH(100,[3,7]); G
            Congruence Subgroup Gamma_H(100) with H generated by [3, 7]
            sage: a = []
            sage: for i in range(G.level()):
            ...   for j in range(G.level()):
            ...       a.append(G._reduce_coset(i,j))
            sage: v = list(set(a))
            sage: v.sort()
            sage: len(v)
            361

        This demonstrates the problem underlying trac \#1220::

            sage: G = GammaH(99, [67])
            sage: G._reduce_coset(11,-3)
            (11, 96)
            sage: G._reduce_coset(77, -3)
            (11, 96)
        """
        N = int(self.level())
        u = uu % N
        v = vv % N
        first, second = self._coset_reduction_data()

        if gcd(first[u][1], first[v][1]) != 1:
            return (0,0)
        if not u:
            return (0, first[v][0])
        if not v:
            return (first[u][0], 0)

        new_u = first[u][0]
        d = first[u][1]
        new_v = (first[u][2] * v) % N
        H_ls = second[d]
        if len(H_ls) > 1:
            new_v = min([ (new_v * h)%N for h in H_ls ])

        return (new_u, new_v)

    def reduce_cusp(self, c):
        r"""
        Compute a minimal representative for the given cusp c. Returns
        a cusp c' which is equivalent to the given cusp, and is in
        lowest terms with minimal positive denominator, and minimal
        positive numerator for that denominator.

        Two cusps `u_1/v_1` and `u_2/v_2` are equivalent modulo `\Gamma_H(N)`
        if and only if

        .. math::

            v_1 =  h v_2 \bmod N\quad \text{and}\quad u_1 =  h^{-1} u_2 \bmod {\rm gcd}(v_1,N)

        or

        .. math::

            v_1 = -h v_2 \bmod N\quad \text{and}\quad u_1 = -h^{-1} u_2 \bmod {\rm gcd}(v_1,N)

        for some `h \in H`.

        EXAMPLES::

            sage: GammaH(6,[5]).reduce_cusp(Cusp(5,3))
            1/3
            sage: GammaH(12,[5]).reduce_cusp(Cusp(8,9))
            1/3
            sage: GammaH(12,[5]).reduce_cusp(Cusp(5,12))
            Infinity
            sage: GammaH(12,[]).reduce_cusp(Cusp(5,12))
            5/12
            sage: GammaH(21,[5]).reduce_cusp(Cusp(-9/14))
            1/7
        """

        return self._reduce_cusp(c)[0]

    def _reduce_cusp(self, c):
        r"""
        Compute a minimal representative for the given cusp c.
        Returns a pair (c', t), where c' is the minimal representative
        for the given cusp, and t is either 1 or -1, as explained
        below. Largely for internal use.

        The minimal representative for a cusp is the element in `P^1(Q)`
        in lowest terms with minimal positive denominator, and minimal
        positive numerator for that denominator.

        Two cusps `u1/v1` and `u2/v2` are equivalent modulo `\Gamma_H(N)`
        if and only if
            `v1 =  h*v2 (mod N)` and `u1 =  h^(-1)*u2 (mod gcd(v1,N))`
        or
            `v1 = -h*v2 (mod N)` and `u1 = -h^(-1)*u2 (mod gcd(v1,N))`
        for some `h \in H`. Then t is 1 or -1 as c and c' fall into
        the first or second case, respectively.

        EXAMPLES::

            sage: GammaH(6,[5])._reduce_cusp(Cusp(5,3))
            (1/3, -1)
            sage: GammaH(12,[5])._reduce_cusp(Cusp(8,9))
            (1/3, -1)
            sage: GammaH(12,[5])._reduce_cusp(Cusp(5,12))
            (Infinity, 1)
            sage: GammaH(12,[])._reduce_cusp(Cusp(5,12))
            (5/12, 1)
            sage: GammaH(21,[5])._reduce_cusp(Cusp(-9/14))
            (1/7, 1)
        """

        N = int(self.level())
        Cusps = c.parent()
        v = int(c.denominator() % N)
        H = self._list_of_elements_in_H()

        # First, if N | v, take care of this case. If u is in \pm H,
        # then we return Infinity. If not, let u_0 be the minimum
        # of \{ h*u | h \in \pm H \}. Then return u_0/N.
        if not v:
            u = c.numerator() % N
            if u in H:
                return Cusps((1,0)), 1
            if (N-u) in H:
                return Cusps((1,0)), -1
            ls = [ (u*h)%N for h in H ]
            m1 = min(ls)
            m2 = N-max(ls)
            if m1 < m2:
                return Cusps((m1,N)), 1
            else:
                return Cusps((m2,N)), -1

        u = int(c.numerator() % v)
        gcd = get_gcd(N)
        d = gcd(v,N)

        # If (N,v) == 1, let v_0 be the minimal element
        # in \{ v * h | h \in \pm H \}. Then we either return
        # Infinity or 1/v_0, as v is or is not in \pm H,
        # respectively.
        if d == 1:
            if v in H:
                return Cusps((0,1)), 1
            if (N-v) in H:
                return Cusps((0,1)), -1
            ls = [ (v*h)%N for h in H ]
            m1 = min(ls)
            m2 = N-max(ls)
            if m1 < m2:
                return Cusps((1,m1)), 1
            else:
                return Cusps((1,m2)), -1

        val_min = v
        inv_mod = get_inverse_mod(N)

        # Now we're in the case (N,v) > 1. So we have to do several
        # steps: first, compute v_0 as above. While computing this
        # minimum, keep track of *all* pairs of (h,s) which give this
        # value of v_0.
        hs_ls = [(1,1)]
        for h in H:
            tmp = (v*h)%N

            if tmp < val_min:
                val_min = tmp
                hs_ls = [(inv_mod(h,N), 1)]
            elif tmp == val_min:
                hs_ls.append((inv_mod(h,N), 1))

            if (N-tmp) < val_min:
                val_min = N - tmp
                hs_ls = [(inv_mod(h,N), -1)]
            elif (N-tmp) == val_min:
                hs_ls.append((inv_mod(h,N), -1))

        # Finally, we find our minimal numerator. Let u_1 be the
        # minimum of s*h^-1*u mod d as (h,s) ranges over the elements
        # of hs_ls. We must find the smallest integer u_0 which is
        # smaller than v_0, congruent to u_1 mod d, and coprime to
        # v_0. Then u_0/v_0 is our minimal representative.
        u_min = val_min
        sign = None
        for h_inv,s in hs_ls:
            tmp = (h_inv * s * u)%d
            while gcd(tmp, val_min) > 1 and tmp < u_min:
                tmp += d
            if tmp < u_min:
                u_min = tmp
                sign = s

        return Cusps((u_min, val_min)), sign

    def _find_cusps(self):
        r"""
        Return an ordered list of inequivalent cusps for self, i.e. a
        set of representatives for the orbits of self on
        `\mathbf{P}^1(\QQ)`.  These are returned in a reduced
        form; see self.reduce_cusp for the definition of reduced.

        ALGORITHM:
            Lemma 3.2 in Cremona's 1997 book shows that for the action
            of Gamma1(N) on "signed projective space"
            `\Q^2 / (\Q_{\geq 0}^+)`, we have `u_1/v_1 \sim u_2 / v_2`
            if and only if `v_1 = v_2 \bmod N` and `u_1 = u_2 \bmod
            gcd(v_1, N)`. It follows that every orbit has a
            representative `u/v` with `v \le N` and `0 \le u \le
            gcd(v, N)`.  We iterate through all pairs `(u,v)`
            satisfying this.

            Having found a set containing at least one of every
            equivalence class modulo Gamma1(N), we can be sure of
            picking up every class modulo GammaH(N) since this
            contains Gamma1(N); and the reduce_cusp call does the
            checking to make sure we don't get any duplicates.

        EXAMPLES::

            sage: Gamma1(5)._find_cusps()
            [0, 2/5, 1/2, Infinity]
            sage: Gamma1(35)._find_cusps()
            [0, 2/35, 1/17, 1/16, 1/15, 1/14, 1/13, 1/12, 3/35, 1/11, 1/10, 1/9, 4/35, 1/8, 2/15, 1/7, 1/6, 6/35, 1/5, 3/14, 8/35, 1/4, 9/35, 4/15, 2/7, 3/10, 11/35, 1/3, 12/35, 5/14, 13/35, 2/5, 3/7, 16/35, 17/35, 1/2, 8/15, 4/7, 3/5, 9/14, 7/10, 5/7, 11/14, 4/5, 6/7, 9/10, 13/14, Infinity]
            sage: Gamma1(24)._find_cusps() == Gamma1(24).cusps(algorithm='modsym')
            True
            sage: GammaH(24, [13,17])._find_cusps() == GammaH(24,[13,17]).cusps(algorithm='modsym')
            True
        """

        s = []
        hashes = []
        N = self.level()

        for d in xrange(1, 1+N):
            w = N.gcd(d)
            M = int(w) if w > 1 else 2
            for a in xrange(1,M):
                if gcd(a, w) != 1:
                    continue
                while gcd(a, d) != 1:
                    a += w
                c = self.reduce_cusp(Cusp(a,d))
                h = hash(c)
                if not h in hashes:
                    hashes.append(h)
                    s.append(c)
        return sorted(s)

    def __call__(self, x, check=True):
        r"""
        Create an element of this congruence subgroup from x.

        If the optional flag check is True (default), check whether
        x actually gives an element of self.

        EXAMPLES::

            sage: G = GammaH(10, [3])
            sage: G([1, 0, -10, 1])
            [ 1   0]
            [-10  1]
            sage: G(matrix(ZZ, 2, [7, 1, 20, 3]))
            [ 7  1]
            [20  3]
            sage: GammaH(10, [9])([7, 1, 20, 3])
            Traceback (most recent call last):
            ...
            TypeError: matrix must have lower right entry (=3) congruent modulo 10 to some element of H
        """
        if isinstance(x, ArithmeticSubgroupElement) and x.parent() == self:
            return x
        x = ArithmeticSubgroupElement(self, x, check=check)
        if not check:
            return x

        c = x.c()
        d = x.d()
        N = self.level()
        if c%N != 0:
            raise TypeError, "matrix must have lower left entry (=%s) divisible by %s" %(c, N)
        elif d%N in self._list_of_elements_in_H():
            return x
        else:
            raise TypeError, "matrix must have lower right entry (=%s) congruent modulo %s to some element of H" %(d, N)

    def gamma0_coset_reps(self):
        r"""
        Return a set of coset representatives for self \\ Gamma0(N), where N is
        the level of self.

        EXAMPLE::

            sage: GammaH(108, [1,-1]).gamma0_coset_reps()
            [[1 0] [0 1], [-43 -45] [108 113], [ 31  33] [108 115], [-49 -54]
            [108 119], [ 25  28] [108 121], [-19 -22] [108 125], [-17 -20] [108
            127], [ 47  57] [108 131], [ 13  16] [108 133], [ 41  52] [108
            137], [  7   9] [108 139], [-37 -49] [108 143], [-35 -47] [108
            145], [ 29  40] [108 149], [ -5  -7] [108 151], [ 23  33] [108
            155], [-11 -16] [108 157], [ 53  79] [108 161]]
        """
        from all import Gamma0
        N = self.level()
        G = Gamma0(N)
        s = []
        return [G(lift_to_sl2z(0, d.lift(), N)) for d in _GammaH_coset_helper(N, self._list_of_elements_in_H())]

    def coset_reps(self):
        r"""
        Return a set of coset representatives for self \\ SL2Z.

        EXAMPLES::

            sage: list(Gamma1(3).coset_reps())
            [[1 0]
            [0 1], [-1 -2]
            [ 3  5], [ 0 -1]
            [ 1  0], [-2  1]
            [ 5 -3], [1 0]
            [1 1], [-3 -2]
            [ 8  5], [ 0 -1]
            [ 1  2], [-2 -3]
            [ 5  7]]
            sage: len(list(Gamma1(31).coset_reps())) == 31**2 - 1
            True
        """
        from all import Gamma0, SL2Z
        reps1 = Gamma0(self.level()).coset_reps()
        for r in reps1:
            reps2 = self.gamma0_coset_reps()
            for t in reps2:
                yield SL2Z(t)*r


    def is_subgroup(self, other):
        r"""
        Return True if self is a subgroup of right, and False
        otherwise.

        EXAMPLES::

            sage: GammaH(24,[7]).is_subgroup(SL2Z)
            True
            sage: GammaH(24,[7]).is_subgroup(Gamma0(8))
            True
            sage: GammaH(24, []).is_subgroup(GammaH(24, [7]))
            True
            sage: GammaH(24, []).is_subgroup(Gamma1(24))
            True
            sage: GammaH(24, [17]).is_subgroup(GammaH(24, [7]))
            False
            sage: GammaH(1371, [169]).is_subgroup(GammaH(457, [169]))
            True
        """

        from all import is_Gamma0, is_Gamma1
        if not isinstance(other, GammaH_class):
            raise NotImplementedError

        # level of self should divide level of other
        if self.level() % other.level():
            return False

        # easy cases
        if is_Gamma0(other):
            return True # recall self is a GammaH, so it's contained in Gamma0

        if is_Gamma1(other) and len(self._generators_for_H()) > 0:
            return False

        else:
            # difficult case
            t = other._list_of_elements_in_H()
            for x in self._generators_for_H():
                if not (x in t):
                    return False
            return True


    def index(self):
        r"""
        Return the index of self in SL2Z.

        EXAMPLE::

            sage: [G.index() for G in Gamma0(40).gamma_h_subgroups()]
            [72, 144, 144, 144, 144, 288, 288, 288, 288, 144, 288, 288, 576, 576, 144, 288, 288, 576, 576, 144, 288, 288, 576, 576, 288, 576, 1152]
        """
        from all import Gamma1
        return Gamma1(self.level()).index() / len(self._list_of_elements_in_H())

    def nu2(self):
        r"""
        Return the number of orbits of elliptic points of order 2 for this
        group.

        EXAMPLE::

            sage: [H.nu2() for n in [1..10] for H in Gamma0(n).gamma_h_subgroups()]
            [1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0]
            sage: GammaH(33,[2]).nu2()
            0
            sage: GammaH(5,[2]).nu2()
            2

        AUTHORS:

        - Jordi Quer

        """
        N = self.level()
        H = self._list_of_elements_in_H()
        if N % 4 == 0: return ZZ(0)
        for p, r in N.factor():
            if p % 4 == 3: return ZZ(0)
        return (euler_phi(N) // len(H))*len([x for x in H if (x**2 + 1) % N == 0])

    def nu3(self):
        r"""
        Return the number of orbits of elliptic points of order 3 for this
        group.

        EXAMPLE::

            sage: [H.nu3() for n in [1..10] for H in Gamma0(n).gamma_h_subgroups()]
            [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            sage: GammaH(33,[2]).nu3()
            0
            sage: GammaH(7,[2]).nu3()
            2

        AUTHORS:

        - Jordi Quer

        """
        N = self.level()
        H = self._list_of_elements_in_H()
        if N % 9 == 0: return ZZ(0)
        for p, r in N.factor():
            if p % 3 == 2: return ZZ(0)
        lenHpm = len(H)
        if N - ZZ(1) not in H: lenHpm*=2
        return (euler_phi(N)//lenHpm)*len([x for x in H if (x**2+x+1) % N == 0])

    def ncusps(self):
        r"""
        Return the number of orbits of cusps (regular or otherwise) for this subgroup.

        EXAMPLE::

            sage: GammaH(33,[2]).ncusps()
            8
            sage: GammaH(32079, [21676]).ncusps()
            28800

        AUTHORS:

        - Jordi Quer

        """
        N = self.level()
        H = self._list_of_elements_in_H()
        c = ZZ(0)
        for d in [d for d in N.divisors() if d**2 <= N]:
            Nd = lcm(d,N//d)
            Hd = set([x % Nd for x in H])
            lenHd = len(Hd)
            if Nd-1 not in Hd: lenHd *= 2
            summand = euler_phi(d)*euler_phi(N//d)//lenHd
            if d**2 == N:
                c = c + summand
            else:
                c = c + 2*summand
        return c

    def nregcusps(self):
        r"""
        Return the number of orbits of regular cusps for this subgroup. A cusp is regular
        if we may find a parabolic element generating the stabiliser of that
        cusp whose eigenvalues are both +1 rather than -1. If G contains -1,
        all cusps are regular.

        EXAMPLES::

            sage: GammaH(20, [17]).nregcusps()
            4
            sage: GammaH(20, [17]).nirregcusps()
            2
            sage: GammaH(3212, [2045, 2773]).nregcusps()
            1440
            sage: GammaH(3212, [2045, 2773]).nirregcusps()
            720

        AUTHOR:

        - Jordi Quer
        """
        if self.is_even():
            return self.ncusps()

        N = self.level()
        H = self._list_of_elements_in_H()

        c = ZZ(0)
        for d in [d for d in divisors(N) if d**2 <= N]:
            Nd = lcm(d,N//d)
            Hd = set([x%Nd for x in H])
            if Nd - 1 not in Hd:
                summand = euler_phi(d)*euler_phi(N//d)//(2*len(Hd))
                if d**2==N:
                    c = c + summand
                else:
                    c = c + 2*summand
        return c

    def nirregcusps(self):
        r"""
        Return the number of irregular cusps for this subgroup.

        EXAMPLES::

            sage: GammaH(3212, [2045, 2773]).nirregcusps()
            720
        """

        return self.ncusps() - self.nregcusps()

    def dimension_new_cusp_forms(self, k=2, p=0):
        r"""
        Return the dimension of the space of new (or `p`-new)
        weight `k` cusp forms for this congruence subgroup.

        INPUT:

        -  ``k`` - an integer (default: 2), the weight. Not fully implemented for k = 1.
        -  ``p`` - integer (default: 0); if nonzero, compute the `p`-new subspace.

        OUTPUT: Integer

        EXAMPLES::

            sage: GammaH(33,[2]).dimension_new_cusp_forms()
            3
            sage: Gamma1(4*25).dimension_new_cusp_forms(2, p=5)
            225
            sage: Gamma1(33).dimension_new_cusp_forms(2)
            19
            sage: Gamma1(33).dimension_new_cusp_forms(2,p=11)
            21

        """
        N = self.level()
        if p==0 or N % p != 0:
            return sum([H.dimension_cusp_forms(k) * mumu(N // H.level()) \
                    for H in self.divisor_subgroups()])
        else:
            return self.dimension_cusp_forms(k) - \
                   2*self.restrict(N//p).dimension_new_cusp_forms(k)

def _GammaH_coset_helper(N, H):
    r"""
    Return a list of coset representatives for H in (Z / NZ)^*.

    EXAMPLE::

        sage: from sage.modular.arithgroup.congroup_gammaH import _GammaH_coset_helper
        sage: _GammaH_coset_helper(108, [1, 107])
        [1, 5, 7, 11, 13, 17, 19, 23, 25, 29, 31, 35, 37, 41, 43, 47, 49, 53]
    """
    t = [IntegerModRing(N)(1)]
    W = [IntegerModRing(N)(h) for h in H]
    HH = [IntegerModRing(N)(h) for h in H]
    k = euler_phi(N)

    for i in xrange(1, N):
        if gcd(i, N) != 1: continue
        if not i in W:
            t.append(t[0]*i)
            W = W + [i*h for h in HH]
            if len(W) == k: break
    return t

def mumu(N):
    """
    Return 0 if any cube divides `N`. Otherwise return
    `(-2)^v` where `v` is the number of primes that
    exactly divide `N`.

    This is similar to the Moebius function.

    INPUT:


    -  ``N`` - an integer at least 1


    OUTPUT: Integer

    EXAMPLES::

        sage: from sage.modular.arithgroup.congroup_gammaH import mumu
        sage: mumu(27)
        0
        sage: mumu(6*25)
        4
        sage: mumu(7*9*25)
        -2
        sage: mumu(9*25)
        1
    """
    if N < 1:
        raise ValueError, "N must be at least 1"
    p = 1
    for _,r in factor(N):
        if r > 2:
            return ZZ(0)
        elif r == 1:
            p *= -2
    return ZZ(p)
