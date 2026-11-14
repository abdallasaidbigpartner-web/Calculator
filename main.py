"""Ultimate Calculator - created by Abdalla Said Ahmed. Built with Kivy."""

# ===== ENGINE START =====
import ast
import math
try:
    import cmath
except ImportError:  # fallback if the phone's Python has no cmath
    import types as _types

    def _csqrt(z):
        z = complex(z)
        r = abs(z)
        im = math.sqrt(max(0.0, (r - z.real) / 2))
        return complex(math.sqrt((r + z.real) / 2), -im if z.imag < 0 else im)

    def _clog(z):
        z = complex(z)
        return complex(math.log(abs(z)), math.atan2(z.imag, z.real))

    def _cexp(z):
        z = complex(z)
        m = math.exp(z.real)
        return complex(m * math.cos(z.imag), m * math.sin(z.imag))

    cmath = _types.SimpleNamespace(
        sqrt=_csqrt, log=_clog, exp=_cexp,
        log10=lambda z: _clog(z) / math.log(10),
        phase=lambda z: math.atan2(complex(z).imag, complex(z).real))
import operator
import random
import re
from fractions import Fraction


class CalcError(Exception):
    pass


class Text(str):
    pass


def _tidy(v, tol=1e-12):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            raise CalcError("range")
        r = round(v)
        if r != 0 and abs(v - r) < tol * abs(r):
            return int(r)
        return float("%.12g" % v)
    if isinstance(v, complex):
        mag = abs(v)
        a = 0.0 if abs(v.real) < tol * mag else v.real
        b = 0.0 if abs(v.imag) < tol * mag else v.imag
        a, b = _tidy(a, tol), _tidy(b, tol)
        return a if b == 0 else complex(a, b)
    if isinstance(v, Fraction):
        return int(v) if v.denominator == 1 else _tidy(float(v), tol)
    if isinstance(v, list):
        return [_tidy(e, tol) for e in v]
    return v


def _clean(v):
    return 0.0 if abs(v) < 1e-12 else round(v, 12)


def _num(v):
    if isinstance(v, complex):
        if abs(v.imag) < 1e-12:
            return v.real
        raise CalcError("complex")
    if isinstance(v, (int, float, Fraction)) and not isinstance(v, bool):
        return v
    raise CalcError("type")


def _int(x):
    x = _num(x)
    if abs(x - round(x)) > 1e-9:
        raise CalcError("int")
    return int(round(x))


def _fr(v):
    if isinstance(v, Fraction):
        return v
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, float) and math.isfinite(v):
        return Fraction(v).limit_denominator(10 ** 9)
    raise CalcError("poly")


# ---------- discrete / number theory ----------
def _fact(x):
    n = _int(x)
    if n < 0 or n > 170:
        raise CalcError("fact")
    return math.factorial(n)


def _ncr(a, b):
    a, b = _int(a), _int(b)
    if a < 0 or b < 0 or a > 10000:
        raise CalcError("range")
    return math.comb(a, b)


def _npr(a, b):
    a, b = _int(a), _int(b)
    if a < 0 or b < 0 or a > 10000:
        raise CalcError("range")
    return math.perm(a, b)


def _prime(n):
    n = _int(n)
    if n < 2 or n > 10 ** 12:
        raise CalcError("range")
    f, d, m = {}, 2, n
    while d * d <= m:
        while m % d == 0:
            f[d] = f.get(d, 0) + 1
            m //= d
        d += 1
    if m > 1:
        f[m] = f.get(m, 0) + 1
    if f == {n: 1}:
        return Text("%d is prime" % n)
    return Text(" × ".join(("%d^%d" % (p, e)) if e > 1 else str(p)
                           for p, e in sorted(f.items())))


# ---------- matrices / vectors ----------
def _mat(m):
    if not (isinstance(m, list) and m and all(
            isinstance(r, list) and r and len(r) == len(m[0]) for r in m)):
        raise CalcError("matrix")
    return [[float(_num(c)) for c in r] for r in m]


def _gauss(a, b):
    n = len(a)
    if any(len(r) != n for r in a) or len(b) != n:
        raise CalcError("size")
    m = [a[i][:] + b[i][:] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(m[r][i]))
        if abs(m[p][i]) < 1e-12:
            raise CalcError("singular")
        m[i], m[p] = m[p], m[i]
        pv = m[i][i]
        m[i] = [v / pv for v in m[i]]
        for r in range(n):
            if r != i:
                f = m[r][i]
                m[r] = [x - f * y for x, y in zip(m[r], m[i])]
    return [r[n:] for r in m]


def _det(m):
    a = _mat(m)
    n = len(a)
    if n != len(a[0]):
        raise CalcError("size")
    d = 1.0
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(a[r][i]))
        if abs(a[p][i]) < 1e-14:
            return 0.0
        if p != i:
            a[i], a[p] = a[p], a[i]
            d = -d
        d *= a[i][i]
        for r in range(i + 1, n):
            f = a[r][i] / a[i][i]
            for c in range(i, n):
                a[r][c] -= f * a[i][c]
    return d


def _inv(m):
    a = _mat(m)
    n = len(a)
    return _gauss(a, [[1.0 if i == j else 0.0 for j in range(n)]
                      for i in range(n)])


def _tr(m):
    return [list(r) for r in zip(*_mat(m))]


def _mmul(a, b):
    a, b = _mat(a), _mat(b)
    if len(a[0]) != len(b):
        raise CalcError("size")
    return [[sum(x * y for x, y in zip(r, c)) for c in zip(*b)] for r in a]


def _linsolve(a, b):
    if not isinstance(b, list):
        raise CalcError("vec")
    return [r[0] for r in _gauss(_mat(a), [[float(_num(v))] for v in b])]


def _ident(n):
    n = _int(n)
    if not 1 <= n <= 10:
        raise CalcError("size")
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def _vec(*a):
    v = list(a[0]) if len(a) == 1 and isinstance(a[0], list) else list(a)
    v = [float(_num(x)) for x in v]
    if not v:
        raise CalcError("empty")
    return v


def _dot(a, b):
    a, b = _vec(a), _vec(b)
    if len(a) != len(b):
        raise CalcError("size")
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    a, b = _vec(a), _vec(b)
    if len(a) != 3 or len(b) != 3:
        raise CalcError("size")
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


# ---------- statistics / distributions ----------
def _variance(a, sample):
    v = _vec(*a)
    m = sum(v) / len(v)
    d = len(v) - (1 if sample else 0)
    if d <= 0:
        raise CalcError("stat")
    return sum((x - m) ** 2 for x in v) / d


def _median(*a):
    v = sorted(_vec(*a))
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def _reg(xs, ys):
    x, y = _vec(xs), _vec(ys)
    if len(x) != len(y) or len(x) < 2:
        raise CalcError("size")
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0:
        raise CalcError("stat")
    b1 = sxy / sxx
    r = sxy / math.sqrt(sxx * syy) if syy else 1.0
    return Text("y = %.8g x + %.8g    r = %.6g" % (b1, my - b1 * mx, r))


def _ncdf(x, m=0.0, s=1.0):
    return 0.5 * (1 + math.erf((x - m) / (s * math.sqrt(2))))


def _npdf(x, m=0.0, s=1.0):
    return math.exp(-((x - m) / s) ** 2 / 2) / (s * math.sqrt(2 * math.pi))


def _binom(n, p, k):
    n, k = _int(n), _int(k)
    if n > 1000 or n < 0:
        raise CalcError("range")
    return math.comb(n, k) * p ** k * (1 - p) ** (n - k) if 0 <= k <= n else 0.0


def _pois(k, lam):
    k = _int(k)
    if k > 170 or k < 0:
        raise CalcError("range")
    return math.exp(-lam) * lam ** k / math.factorial(k)


# ---------- unit conversion ----------
_U = {
    "m": ("L", 1), "km": ("L", 1000), "cm": ("L", .01), "mm": ("L", .001),
    "mi": ("L", 1609.344), "yd": ("L", .9144), "ft": ("L", .3048),
    "in": ("L", .0254),
    "kg": ("M", 1), "g": ("M", .001), "mg": ("M", 1e-6),
    "lb": ("M", .45359237), "oz": ("M", .028349523125), "t": ("M", 1000),
    "s": ("T", 1), "ms": ("T", .001), "min": ("T", 60), "h": ("T", 3600),
    "day": ("T", 86400),
    "m2": ("A", 1), "km2": ("A", 1e6), "ha": ("A", 1e4),
    "acre": ("A", 4046.8564224),
    "L": ("V", 1), "mL": ("V", .001), "m3": ("V", 1000),
    "gal": ("V", 3.785411784),
    "m/s": ("S", 1), "km/h": ("S", 1 / 3.6), "mph": ("S", .44704),
    "kn": ("S", .514444444),
    "J": ("E", 1), "kJ": ("E", 1000), "cal": ("E", 4.184),
    "kcal": ("E", 4184), "kWh": ("E", 3.6e6),
    "Pa": ("P", 1), "kPa": ("P", 1000), "bar": ("P", 1e5),
    "atm": ("P", 101325), "psi": ("P", 6894.757293),
    "B": ("D", 1), "KB": ("D", 1e3), "MB": ("D", 1e6), "GB": ("D", 1e9),
    "TB": ("D", 1e12),
}


def _conv(v, a, b):
    v = _num(v)
    if a in ("C", "F", "K") and b in ("C", "F", "K"):
        k = v + 273.15 if a == "C" else (v - 32) * 5 / 9 + 273.15 if a == "F" else v
        return k - 273.15 if b == "C" else (k - 273.15) * 9 / 5 + 32 if b == "F" else k
    if a not in _U or b not in _U or _U[a][0] != _U[b][0]:
        raise CalcError("units")
    return v * _U[a][1] / _U[b][1]


CONSTS = {
    "lightc": 299792458, "gravg": 9.80665, "planckh": 6.62607015e-34,
    "gravG": 6.6743e-11, "avog": 6.02214076e23, "boltz": 1.380649e-23,
    "echarge": 1.602176634e-19, "gasR": 8.314462618,
    "emass": 9.1093837015e-31, "pmass": 1.67262192369e-27,
    "permit": 8.8541878128e-12, "permeab": 1.25663706212e-6,
}
VARS = ("x", "y", "z", "A", "B", "C")


# ---------- function table ----------
def make_funcs(deg):
    r = math.radians if deg else (lambda x: x)
    d = math.degrees if deg else (lambda x: x)

    def cx(rf, cf):
        def f(x):
            if isinstance(x, complex):
                return cf(x)
            try:
                return rf(x)
            except ValueError:
                return cf(x)
        return f

    def trig(fn):
        return lambda x: _clean(fn(r(_num(x))))

    def inv(fn):
        return lambda x: _clean(d(fn(_num(x))))

    def tan(x):
        x = _num(x)
        if deg and abs((x % 180) - 90) < 1e-9:
            raise CalcError("tan")
        if not deg and abs(math.cos(x)) < 1e-12:
            raise CalcError("tan")
        return _clean(math.tan(r(x)))

    def recip(fn):
        def f(x):
            v = _clean(fn(r(_num(x))))
            if v == 0:
                raise CalcError("zero")
            return 1 / v
        return f

    def cot(x):
        c, sn = _clean(math.cos(r(_num(x)))), _clean(math.sin(r(_num(x))))
        if sn == 0:
            raise CalcError("zero")
        return c / sn

    def root(x, n):
        x, n = _num(x), _num(n)
        if x < 0 and abs(n - round(n)) < 1e-12 and int(round(n)) % 2 == 1:
            return -((-x) ** (1.0 / n))
        return x ** (1.0 / n)

    def agg(fn):
        return lambda *a: fn(_vec(*a))

    def shift(fn):
        def f(a, n):
            n = _int(n)
            if not 0 <= n <= 64:
                raise CalcError("range")
            return fn(_int(a), n)
        return f

    return {
        "sin": trig(math.sin), "cos": trig(math.cos), "tan": tan,
        "asin": inv(math.asin), "acos": inv(math.acos), "atan": inv(math.atan),
        "sinh": lambda x: math.sinh(_num(x)), "cosh": lambda x: math.cosh(_num(x)),
        "tanh": lambda x: math.tanh(_num(x)),
        "asinh": lambda x: math.asinh(_num(x)), "acosh": lambda x: math.acosh(_num(x)),
        "atanh": lambda x: math.atanh(_num(x)),
        "sec": recip(math.cos), "csc": recip(math.sin), "cot": cot,
        "log": cx(math.log10, cmath.log10), "ln": cx(math.log, cmath.log),
        "log2": lambda x: math.log2(_num(x)),
        "logb": lambda x, b: math.log(_num(x)) / math.log(_num(b)),
        "exp": cx(math.exp, cmath.exp), "sqrt": cx(math.sqrt, cmath.sqrt),
        "cbrt": lambda x: root(x, 3), "root": root, "abs": abs,
        "fact": _fact, "ncr": _ncr, "npr": _npr,
        "mod": lambda a, b: _num(a) % _num(b),
        "gcd": lambda *a: math.gcd(*[_int(x) for x in a]),
        "lcm": lambda *a: math.lcm(*[_int(x) for x in a]),
        "prime": _prime,
        "round": lambda x, n=0: round(_num(x), _int(n)),
        "floor": lambda x: math.floor(_num(x)), "ceil": lambda x: math.ceil(_num(x)),
        "sgn": lambda x: (_num(x) > 0) - (_num(x) < 0),
        "rand": lambda: random.random(),
        "randint": lambda a, b: random.randint(_int(a), _int(b)),
        "re": lambda z: complex(z).real, "im": lambda z: complex(z).imag,
        "conj": lambda z: complex(z).conjugate(),
        "arg": lambda z: d(cmath.phase(complex(z))),
        "band": lambda a, b: _int(a) & _int(b), "bor": lambda a, b: _int(a) | _int(b),
        "bxor": lambda a, b: _int(a) ^ _int(b), "bnot": lambda a: ~_int(a),
        "shl": shift(operator.lshift), "shr": shift(operator.rshift),
        "bin": lambda x: Text(bin(_int(x))), "hex": lambda x: Text(hex(_int(x))),
        "oct": lambda x: Text(oct(_int(x))),
        "det": _det, "inv": _inv, "tr": _tr, "mmul": _mmul,
        "linsolve": _linsolve, "ident": _ident,
        "dot": _dot, "cross": _cross,
        "norm": lambda a: math.sqrt(sum(x * x for x in _vec(a))),
        "mean": agg(lambda v: sum(v) / len(v)), "median": _median,
        "var": lambda *a: _variance(a, True), "varp": lambda *a: _variance(a, False),
        "stdev": lambda *a: math.sqrt(_variance(a, True)),
        "stdevp": lambda *a: math.sqrt(_variance(a, False)),
        "total": agg(sum), "min": agg(min), "max": agg(max), "reg": _reg,
        "normcdf": lambda x, m=0, s=1: _ncdf(_num(x), _num(m), _num(s)),
        "normpdf": lambda x, m=0, s=1: _npdf(_num(x), _num(m), _num(s)),
        "binom": lambda n, p, k: _binom(n, _num(p), k),
        "binomcdf": lambda n, p, k: sum(_binom(n, _num(p), j)
                                        for j in range(_int(k) + 1)),
        "poisson": lambda k, l: _pois(k, _num(l)),
        "poissoncdf": lambda k, l: sum(_pois(j, _num(l)) for j in range(_int(k) + 1)),
        "conv": _conv,
    }


LAZY = ("diff", "integ", "sigma", "prod", "lim", "solve", "expand",
        "factor", "simplify")
_FUNC_NAMES = set(make_funcs(True)) | set(LAZY)
_CONST_NAMES = {"pi", "e", "i", "phi", "ans", "mem"} | set(CONSTS)
KNOWN = sorted(_FUNC_NAMES | _CONST_NAMES | set(VARS), key=len, reverse=True)
_KNOWN_SET = set(KNOWN)


# ---------- polynomials (exact, in x) ----------
def _polyfit(F, deg=8):
    try:
        xs = list(range(deg + 3))
        ys = [_fr(F(Fraction(k))) for k in xs]
        n = deg + 1
        d, c = ys[:n], [ys[0]]
        for j in range(1, n):
            d = [(d[i + 1] - d[i]) / (xs[i + j] - xs[i]) for i in range(n - j)]
            c.append(d[0])
        poly, basis = [Fraction(0)] * n, [Fraction(1)]
        for j in range(n):
            for t, cf in enumerate(basis):
                poly[t] += c[j] * cf
            nb = [Fraction(0)] * (len(basis) + 1)
            for t, cf in enumerate(basis):
                nb[t + 1] += cf
                nb[t] -= j * cf
            basis = nb
        for k in xs[n:] + [-7, 23, 100]:
            yk = ys[k] if k in xs else _fr(F(Fraction(k)))
            if abs(_peval(poly, Fraction(k)) - yk) > Fraction(1, 10 ** 9) * (1 + abs(yk)):
                return None
        while len(poly) > 1 and poly[-1] == 0:
            poly.pop()
        return poly
    except (CalcError, ZeroDivisionError, TypeError, OverflowError, ValueError):
        return None


def _peval(co, x):
    v = Fraction(0)
    for c in reversed(co):
        v = v * x + c
    return v


def _pstr(co):
    out = []
    for k in range(len(co) - 1, -1, -1):
        c = co[k]
        if c == 0:
            continue
        m = abs(c)
        if k == 0 or m != 1:
            cs = str(m.numerator) if m.denominator == 1 else "(%d/%d)" % (m.numerator, m.denominator)
        else:
            cs = ""
        term = cs + ("" if k == 0 else "x" if k == 1 else "x^%d" % k)
        out.append(("-" if c < 0 else "") + term if not out
                   else ("- " if c < 0 else "+ ") + term)
    return " ".join(out) if out else "0"


def _pder(co):
    return [co[k] * k for k in range(1, len(co))] or [Fraction(0)]


def _pint(co):
    return [Fraction(0)] + [co[k] / (k + 1) for k in range(len(co))]


def _divisors(n):
    n, ds, d = abs(n), [], 1
    while d * d <= n:
        if n % d == 0:
            ds += [d, n // d]
        d += 1
    return sorted(set(ds))


def _lin(q, s):
    if q == 1:
        return "x" if s == 0 else "(x %s %d)" % ("-" if s > 0 else "+", abs(s))
    return "(%dx %s %d)" % (q, "-" if s > 0 else "+", abs(s))


def _factor(co):
    if len(co) == 1:
        return _pstr(co)
    L = 1
    for c in co:
        L = L * c.denominator // math.gcd(L, c.denominator)
    ints = [int(c * L) for c in co]
    g = 0
    for v in ints:
        g = math.gcd(g, v)
    ints = [v // g for v in ints]
    sign = -1 if ints[-1] < 0 else 1
    cur = [v * sign for v in ints]
    content = Fraction(g * sign, L)
    facs = []
    while len(cur) > 1:
        found = None
        if cur[0] == 0:
            found = (1, 0)
        elif abs(cur[0]) < 10 ** 9 and abs(cur[-1]) < 10 ** 9:
            n = len(cur) - 1
            for p in _divisors(cur[0]):
                for q in _divisors(cur[-1]):
                    for s in (p, -p):
                        if sum(cur[k] * s ** k * q ** (n - k) for k in range(n + 1)) == 0:
                            found = (q, s)
                            break
                    if found:
                        break
                if found:
                    break
        if not found:
            break
        q, s = found
        facs.append(_lin(q, s))
        rt, hi, quo = Fraction(s, q), [Fraction(v) for v in reversed(cur)], []
        acc = Fraction(0)
        for k, v in enumerate(hi):
            acc = v + acc * rt if k else v
            quo.append(acc)
        quo.pop()
        cur = [int(v / q) for v in reversed(quo)] or [1]
    if len(cur) == 1:
        content *= cur[0]
        rest = ""
    else:
        rest = "(" + _pstr([Fraction(v) for v in cur]) + ")"
    counts, order = {}, []
    for f in facs:
        if f not in counts:
            order.append(f)
        counts[f] = counts.get(f, 0) + 1
    parts = [f + ("^%d" % counts[f] if counts[f] > 1 else "") for f in order]
    if rest:
        parts.append(rest)
    pre = "" if content == 1 else "-" if content == -1 else (
        str(content.numerator) if content.denominator == 1
        else "(%d/%d)" % (content.numerator, content.denominator))
    return (pre + "".join(parts)) or "1"


def _poly_roots(co):
    a = [float(c) for c in reversed(co)]
    n = len(a) - 1
    if n == 1:
        rs = [-a[1] / a[0]]
    elif n == 2:
        disc = cmath.sqrt(a[1] ** 2 - 4 * a[0] * a[2])
        rs = [(-a[1] + disc) / (2 * a[0]), (-a[1] - disc) / (2 * a[0])]
    else:
        a = [c / a[0] for c in a]
        rs = [(0.4 + 0.9j) ** k for k in range(n)]
        for _ in range(500):
            big = 0.0
            for i in range(n):
                num = 0j
                for c in a:
                    num = num * rs[i] + c
                den = 1 + 0j
                for j in range(n):
                    if j != i:
                        den *= rs[i] - rs[j]
                step = num / den
                rs[i] -= step
                big = max(big, abs(step))
            if big < 1e-15:
                break
    out = []
    for z in rs:
        z = complex(z)
        if abs(z.imag) < 1e-7 * (1 + abs(z)):
            z = z.real
        t = _tidy(z, 1e-7)
        if not any(abs(complex(t) - complex(u)) < 1e-6 for u in out):
            out.append(t)
    return sorted(out, key=lambda v: (complex(v).real, complex(v).imag))


def _scan_roots(FN):
    n, lo, hi = 4000, -100.0, 100.0
    xs = [lo + (hi - lo) * i / n for i in range(n + 1)]
    vs = []
    for x in xs:
        try:
            v = FN(x)
            vs.append(v if math.isfinite(v) else None)
        except Exception:
            vs.append(None)
    roots = []

    def add(r):
        if not any(abs(r - u) < 1e-6 for u in roots):
            roots.append(r)

    for i in range(n):
        a, b = vs[i], vs[i + 1]
        if a is None or b is None:
            continue
        if a == 0:
            add(xs[i])
        elif a * b < 0:
            x0, x1 = xs[i], xs[i + 1]
            for _ in range(100):
                m = (x0 + x1) / 2
                fm = FN(m)
                if fm == 0:
                    break
                if FN(x0) * fm < 0:
                    x1 = m
                else:
                    x0 = m
            m = (x0 + x1) / 2
            if abs(FN(m)) < 1e-6:
                add(m)
    for i in range(1, n):
        a, b, c = vs[i - 1], vs[i], vs[i + 1]
        if None in (a, b, c) or a * c <= 0:
            continue
        if abs(b) <= abs(a) and abs(b) <= abs(c):
            x0, x1 = xs[i - 1], xs[i + 1]
            for _ in range(80):
                m1, m2 = x0 + (x1 - x0) / 3, x1 - (x1 - x0) / 3
                if abs(FN(m1)) < abs(FN(m2)):
                    x1 = m2
                else:
                    x0 = m1
            m = (x0 + x1) / 2
            if abs(FN(m)) < 1e-9:
                add(m)
    return [_tidy(r, 1e-9) for r in sorted(roots)]


def _newton(FN, x):
    for _ in range(80):
        f = FN(x)
        if abs(f) < 1e-13:
            return x
        h = 1e-6 * max(1.0, abs(x))
        df = (FN(x + h) - FN(x - h)) / (2 * h)
        if df == 0:
            raise CalcError("newton")
        x -= f / df
    raise CalcError("newton")


def _lazy(name, args, env, funcs):
    if not args:
        raise CalcError("args")
    node = args[0]
    rest = [_eval(a, env, funcs) for a in args[1:]]

    fx = make_funcs(False) if name in ("diff", "integ", "lim") else funcs

    def F(v):
        e = dict(env)
        e["x"] = v
        return _eval(node, e, fx)

    def FN(v):
        return float(_num(F(v)))

    co = None
    if name in ("diff", "integ", "solve", "expand", "factor", "simplify"):
        co = _polyfit(F)
    if name in ("expand", "simplify"):
        if co is None:
            raise CalcError("poly")
        return Text(_pstr(co))
    if name == "factor":
        if co is None:
            raise CalcError("poly")
        return Text(_factor(co))
    if name == "diff":
        if not rest:
            if co is None:
                raise CalcError("poly")
            return Text(_pstr(_pder(co)))
        a = rest[0]
        if co is not None:
            return _tidy(float(_peval(_pder(co), _fr(a))), 1e-9)
        a = float(_num(a))
        h = 1e-3 * max(1.0, abs(a))
        v = (-FN(a + 2 * h) + 8 * FN(a + h) - 8 * FN(a - h) + FN(a - 2 * h)) / (12 * h)
        return _tidy(v, 1e-8)
    if name == "integ":
        if not rest:
            if co is None:
                raise CalcError("poly")
            return Text(_pstr(_pint(co)) + " + C")
        if len(rest) != 2:
            raise CalcError("args")
        if co is not None:
            P = _pint(co)
            return _tidy(float(_peval(P, _fr(rest[1])) - _peval(P, _fr(rest[0]))), 1e-12)
        a, b = float(_num(rest[0])), float(_num(rest[1]))
        n = 2000
        h = (b - a) / n
        s = FN(a) + FN(b)
        for k in range(1, n):
            s += (4 if k % 2 else 2) * FN(a + k * h)
        return _tidy(s * h / 3, 1e-8)
    if name in ("sigma", "prod"):
        if len(rest) != 2:
            raise CalcError("args")
        a, b = _int(rest[0]), _int(rest[1])
        if b - a > 100000 or (name == "prod" and b - a > 2000):
            raise CalcError("range")
        acc = 0 if name == "sigma" else 1
        for k in range(a, b + 1):
            acc = acc + _num(F(k)) if name == "sigma" else acc * _num(F(k))
        return _tidy(acc)
    if name == "lim":
        a = float(_num(rest[0])) if rest else 0.0
        vals = []
        for h in (1e-6, 1e-8):
            vals.append((FN(a - h), FN(a + h)))
        l, r = vals[-1]
        if abs(l - r) > 1e-4 * (1 + abs(l)):
            raise CalcError("nolimit")
        return _tidy((l + r) / 2, 1e-5)
    if name == "solve":
        if rest:
            return _tidy(_newton(FN, float(_num(rest[0]))), 1e-9)
        if co is not None:
            if len(co) == 1:
                return Text("all x" if co[0] == 0 else "no solution")
            roots = _poly_roots(co)
        else:
            roots = _scan_roots(FN)
        if not roots:
            return Text("no real solution found")
        return Text(",   ".join("x = " + fmt(r) for r in roots))
    raise CalcError("lazy")


# ---------- evaluator ----------
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv}


def _pow(a, b):
    if abs(b) > 10000:
        raise CalcError("pow")
    if isinstance(a, int) and isinstance(b, int) and a not in (0, 1, -1):
        if b > 0 and b * math.log10(abs(a)) > 300:
            raise CalcError("too big")
    return a ** b


def _bin(op, a, b):
    la, lb = isinstance(a, list), isinstance(b, list)
    if not la and not lb:
        return _BIN[op](a, b)
    if op in (ast.Add, ast.Sub) and la and lb and len(a) == len(b):
        return [_bin(op, x, y) for x, y in zip(a, b)]
    if op is ast.Mult and la and lb:
        return _mmul(a, b)
    if op in (ast.Mult, ast.Div) and la and not lb:
        return [_bin(op, x, b) for x in a]
    if op is ast.Mult and lb and not la:
        return [_bin(op, a, y) for y in b]
    raise CalcError("type")


def _eval(node, env, funcs):
    if isinstance(node, ast.Expression):
        return _eval(node.body, env, funcs)
    if isinstance(node, ast.Constant):
        if type(node.value) in (int, float, str):
            return node.value
        raise CalcError("const")
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise CalcError("name")
    if isinstance(node, ast.List):
        return [_eval(e, env, funcs) for e in node.elts]
    if isinstance(node, ast.UnaryOp):
        v = _eval(node.operand, env, funcs)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return v
        raise CalcError("op")
    if isinstance(node, ast.BinOp):
        a = _eval(node.left, env, funcs)
        b = _eval(node.right, env, funcs)
        if isinstance(node.op, ast.Pow):
            return _pow(a, b)
        if type(node.op) in _BIN:
            return _bin(type(node.op), a, b)
        raise CalcError("op")
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and not node.keywords:
            nm = node.func.id
            if nm in LAZY:
                return _lazy(nm, node.args, env, funcs)
            if nm in funcs:
                return funcs[nm](*[_eval(a, env, funcs) for a in node.args])
        raise CalcError("func")
    raise CalcError("syntax")


def _factorials(s):
    while "!" in s:
        i = s.index("!")
        j = i - 1
        if j < 0:
            raise CalcError("fact")
        if s[j] == ")":
            depth = 0
            while j >= 0:
                if s[j] == ")":
                    depth += 1
                elif s[j] == "(":
                    depth -= 1
                    if depth == 0:
                        break
                j -= 1
            if j < 0:
                raise CalcError("paren")
            start = j
            while start > 0 and s[start - 1].isalpha():
                start -= 1
        elif s[j].isalpha():
            start = j
            while start > 0 and s[start - 1].isalpha():
                start -= 1
        else:
            start = j
            while start > 0 and (s[start - 1].isdigit() or s[start - 1] == "."):
                start -= 1
            if not (s[start].isdigit() or s[start] == "."):
                raise CalcError("fact")
        s = s[:start] + "fact(" + s[start:i] + ")" + s[i + 1:]
    return s


def _split_word(m):
    w = m.group(0)
    if w in _KNOWN_SET:
        return w
    base, dig = re.match(r"([A-Za-z]+)(\d*)$", w).groups()
    pieces, i = [], 0
    while i < len(base):
        for nm in KNOWN:
            if base.startswith(nm, i):
                pieces.append(nm)
                i += len(nm)
                break
        else:
            return w
    if any(p in _FUNC_NAMES for p in pieces[:-1]):
        return w
    if dig and pieces[-1] in _FUNC_NAMES:
        return w
    return "*".join(pieces + ([dig] if dig else []))


def _sym(p):
    return (p.replace("×", "*").replace("÷", "/").replace("−", "-")
            .replace("π", "pi").replace("√", "sqrt").replace("^", "**")
            .replace("%", "/100").replace("²", "**2").replace("Ans", "ans").replace("Mem", "mem"))


def _implicit(p):
    p = re.sub(r"[A-Za-z]+\d*", _split_word, p)
    p = re.sub(r"(?<![A-Za-z0-9_.])(\d+\.?\d*|\.\d+)(?=[A-Za-z(])", r"\1*", p)
    p = re.sub(r"(?<=\))(?=[A-Za-z(\d])", "*", p)
    p = re.sub(r"\b(pi|phi|ans|mem|e|i|x|y|z|A|B|C)(?=\()", r"\1*", p)
    return p


def _map_text(s, f):
    parts = re.split(r'("[^"]*")', s)
    return "".join(p if i % 2 else f(p) for i, p in enumerate(parts))


def prepare(expr):
    s = _map_text(expr, _sym)
    s = _factorials(s)
    opened = s.count("(") - s.count(")")
    if opened > 0:
        s += ")" * opened
    return _map_text(s, _implicit)


def make_env(ans=0.0, mem=0.0, vars_=None):
    env = {"pi": math.pi, "e": math.e, "i": 1j, "phi": (1 + 5 ** 0.5) / 2,
           "ans": ans, "mem": mem}
    env.update(CONSTS)
    env.update({n: 0 for n in VARS})
    if vars_:
        env.update(vars_)
    return env


def _final(v):
    if isinstance(v, str):
        return v
    return _tidy(v)


def evaluate(expr, deg=True, ans=0.0, mem=0.0, vars_=None):
    if not expr.strip() or len(expr) > 400:
        raise CalcError("empty")
    try:
        if "=" in expr and not any(c in expr for c in "<>≤≥≠"):
            expr = expr.strip()
            if expr.startswith("solve("):
                expr = expr[6:]
                if expr.endswith(")"):
                    expr = expr[:-1]
            parts = expr.split("=")
            if len(parts) != 2 or not parts[1].strip():
                raise CalcError("eq")
            expr = "solve((%s)-(%s))" % (parts[0], parts[1])
        tree = ast.parse(prepare(expr), mode="eval")
        return _final(_eval(tree, make_env(ans, mem, vars_), make_funcs(deg)))
    except CalcError:
        raise
    except Exception as ex:
        raise CalcError(str(ex))


def compile_fn(expr, deg=True, ans=0.0, mem=0.0, vars_=None):
    if "=" in expr:
        l, r = expr.split("=", 1)
        expr = r if l.strip() in ("y", "f(x)") else "(%s)-(%s)" % (l, r)
    tree = ast.parse(prepare(expr), mode="eval")
    funcs, env = make_funcs(deg), make_env(ans, mem, vars_)

    def f(xv):
        e = dict(env)
        e["x"] = xv
        return float(_num(_eval(tree, e, funcs)))
    return f


def _fnum(x, frac=False):
    if isinstance(x, bool):
        x = int(x)
    if isinstance(x, int):
        if abs(x) < 10 ** 15:
            return str(x)
        x = float(x)
    if math.isnan(x) or math.isinf(x):
        raise CalcError("range")
    if frac and x != int(x) and abs(x) < 1e9:
        fr = Fraction(x).limit_denominator(100000)
        if abs(float(fr) - x) < 1e-11 * max(1.0, abs(x)):
            return "%d/%d" % (fr.numerator, fr.denominator)
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    s = "%.12g" % x
    if "e" in s:
        m, ex = s.split("e")
        s = "%s×10^%d" % (m, int(ex))
    return s


def fmt(x, frac=False):
    try:
        if isinstance(x, str):
            return str(x)
        if isinstance(x, list):
            return "[" + ", ".join(fmt(e, frac) for e in x) + "]"
        if isinstance(x, complex):
            a, b = x.real, x.imag
            if b == 0:
                return _fnum(a, frac)
            ims = _fnum(abs(b), frac)
            ims = "" if ims == "1" else ims
            if a == 0:
                return ("-" if b < 0 else "") + ims + "i"
            return "%s %s %si" % (_fnum(a, frac), "-" if b < 0 else "+", ims)
        return _fnum(x, frac)
    except CalcError:
        raise
    except Exception as ex:
        raise CalcError(str(ex))
# ===== ENGINE END =====

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.stencilview import StencilView

CREATOR = "Abdalla Said Ahmed"

BG = (0.043, 0.047, 0.063, 1)
GOLD = (1.0, 0.82, 0.40, 1)
GRAY = (0.55, 0.60, 0.70, 1)
WHITE = (1, 1, 1, 1)
C_BAR = (0.12, 0.13, 0.17, 1)
C_BAR_ON = (0.16, 0.45, 0.80, 1)
STY = {
    "num": ((0.16, 0.17, 0.21, 1), WHITE),
    "fn": ((0.23, 0.24, 0.29, 1), WHITE),
    "op": ((1.0, 0.58, 0.10, 1), (0.1, 0.07, 0, 1)),
    "eq": ((0.16, 0.52, 0.95, 1), WHITE),
    "clr": ((0.40, 0.13, 0.15, 1), (1, 0.5, 0.5, 1)),
    "sh": ((0.48, 0.32, 0.0, 1), (1, 0.88, 0.63, 1)),
    "alg": ((0.17, 0.18, 0.42, 1), (0.83, 0.85, 1, 1)),
    "cal": ((0.06, 0.29, 0.29, 1), (0.62, 0.95, 0.93, 1)),
    "trg": ((0.07, 0.23, 0.40, 1), (0.68, 0.84, 1, 1)),
    "pow": ((0.16, 0.19, 0.25, 1), (0.87, 0.89, 0.94, 1)),
    "dis": ((0.35, 0.24, 0.04, 1), (1, 0.86, 0.58, 1)),
    "bit": ((0.09, 0.29, 0.17, 1), (0.65, 0.94, 0.75, 1)),
    "mat": ((0.29, 0.15, 0.44, 1), (0.9, 0.77, 1, 1)),
    "con": ((0.42, 0.13, 0.28, 1), (1, 0.75, 0.87, 1)),
}
OPS = ("+", "-", "×", "÷")
POST = ("^2", "^", "!", "%")


def K(a, i=None, b=None, j=None, st="fn"):
    return (a, a if i is None else i, b, b if j is None else j, st)


PANELS = {
    "f(x)": [
        K("sin", "sin(", "asin", "asin(", "trg"), K("cos", "cos(", "acos", "acos(", "trg"),
        K("tan", "tan(", "atan", "atan(", "trg"), K("sinh", "sinh(", "asinh", "asinh(", "trg"),
        K("cosh", "cosh(", "acosh", "acosh(", "trg"), K("tanh", "tanh(", "atanh", "atanh(", "trg"),
        K("sec", "sec(", st="trg"), K("csc", "csc(", st="trg"), K("cot", "cot(", st="trg"),
        K("DEG", "@DEG", st="trg"), K("arg", "arg(", st="trg"), K("abs", "abs(", st="trg"),
        K("x²", "^2", "√", "√(", "pow"), K("x^y", "^", "root", "root(", "pow"),
        K("1/x", "@INV", "n!", "!", "pow"), K("log", "log(", "10^x", "10^(", "pow"),
        K("ln", "ln(", "e^x", "exp(", "pow"), K("logb", "logb(", "log2", "log2(", "pow"),
        K("π", "π", "e", "e", "con"), K("i", "i", "phi", "phi", "con"),
        K("round", "round(", "floor", "floor(", "con"), K("ceil", "ceil(", "sgn", "sgn(", "con"),
        K("rand", "rand(", "randint", "randint(", "con"), K("%", "%", st="con"),
    ],
    "CAS": [
        K("Solve", "solve(", st="alg"), K("Expand", "expand(", st="alg"),
        K("Factor", "factor(", st="alg"), K("Simplify", "simplify(", st="alg"),
        K("Graph", "@GRAPH", st="alg"), K("Table", "@TABLE", st="alg"),
        K("d/dx", "diff(", st="cal"), K("∫", "integ(", st="cal"),
        K("Σ", "sigma(", st="cal"), K("Π", "prod(", st="cal"),
        K("lim", "lim(", st="cal"), K("=", "=", st="cal"),
        K("x", "x"), K("y", "y"), K("z", "z"), K(",", ","), K("[", "["), K("]", "]"),
        K("round", "round(", st="con"), K("floor", "floor(", st="con"),
        K("ceil", "ceil(", st="con"), K("sgn", "sgn(", st="con"),
        K("rand", "rand(", st="con"), K("randint", "randint(", st="con"),
    ],
    "Num": [
        K("n!", "!", st="dis"), K("nCr", "ncr(", "nPr", "npr(", "dis"),
        K("Mod", "mod(", st="dis"), K("GCD", "gcd(", st="dis"),
        K("LCM", "lcm(", st="dis"), K("Prime", "prime(", st="dis"),
        K("AND", "band(", st="bit"), K("OR", "bor(", st="bit"),
        K("XOR", "bxor(", st="bit"), K("NOT", "bnot(", st="bit"),
        K("<<", "shl(", st="bit"), K(">>", "shr(", st="bit"),
        K("BIN", "bin(", st="bit"), K("HEX", "hex(", st="bit"),
        K("OCT", "oct(", st="bit"), K("MC", "@MC", st="clr"),
        K("MR", "@MR", st="sh"), K("M+", "@M+", st="sh"),
        K("M-", "@M-", st="sh"), K("Re", "re(", st="mat"),
        K("Im", "im(", st="mat"), K("conj", "conj(", st="mat"),
    ],
    "Stat": [
        K("[", "["), K("]", "]"), K(",", ","),
        K("mean", "mean(", st="mat"), K("median", "median(", st="mat"),
        K("stdev", "stdev(", st="mat"),
        K("stdevp", "stdevp(", st="mat"), K("var", "var(", st="mat"),
        K("total", "total(", st="mat"), K("min", "min(", st="mat"),
        K("max", "max(", st="mat"), K("reg", "reg(", st="mat"),
        K("det", "det(", st="alg"), K("inv", "inv(", st="alg"),
        K("tr", "tr(", st="alg"), K("mmul", "mmul(", st="alg"),
        K("linsolve", "linsolve(", st="alg"), K("ident", "ident(", st="alg"),
        K("dot", "dot(", st="cal"), K("cross", "cross(", st="cal"),
        K("norm", "norm(", st="cal"), K("normcdf", "normcdf(", st="cal"),
        K("binom", "binom(", st="cal"), K("poisson", "poisson(", st="cal"),
    ],
    "Conv": [
        K("conv", "conv(", st="con"), K("m", '"m"'), K("km", '"km"'),
        K("mi", '"mi"'), K("ft", '"ft"'), K("in", '"in"'),
        K("cm", '"cm"'), K("kg", '"kg"'), K("g", '"g"'),
        K("lb", '"lb"'), K("oz", '"oz"'), K("s", '"s"'),
        K("min", '"min"'), K("h", '"h"'), K("day", '"day"'),
        K("C", '"C"'), K("F", '"F"'), K("K", '"K"'),
        K("L", '"L"'), K("gal", '"gal"'), K("km/h", '"km/h"'),
        K("mph", '"mph"'), K("kcal", '"kcal"'), K("atm", '"atm"'),
    ],
    "Const": [
        K("c", "lightc", st="con"), K("g", "gravg", st="con"),
        K("h", "planckh", st="con"), K("G", "gravG", st="con"),
        K("NA", "avog", st="con"), K("kB", "boltz", st="con"),
        K("qe", "echarge", st="con"), K("R", "gasR", st="con"),
        K("me", "emass", st="con"), K("mp", "pmass", st="con"),
        K("eps0", "permit", st="con"), K("mu0", "permeab", st="con"),
        K("π", "π", st="pow"), K("e", "e", st="pow"), K("phi", "phi", st="pow"),
        K("i", "i", st="pow"), K("Ans", "Ans", st="pow"), K("Mem", "Mem", st="pow"),
    ],
}
TABS = ["f(x)", "CAS", "Num", "Stat", "Conv", "Const"]

PAD = [
    [("2nd", "@2nd", "sh"), ("UNDO", "@UNDO", "fn"), ("S<>D", "@SD", "fn"),
     ("DEL", "@DEL", "clr"), ("AC", "@AC", "clr")],
    [("(", "(", "fn"), (")", ")", "fn"), ("%", "%", "fn"),
     ("√", "√(", "fn"), ("x^y", "^", "fn")],
    [("7", "7", "num"), ("8", "8", "num"), ("9", "9", "num"),
     ("×", "×", "op"), ("÷", "÷", "op")],
    [("4", "4", "num"), ("5", "5", "num"), ("6", "6", "num"),
     ("+", "+", "op"), ("-", "-", "op")],
    [("1", "1", "num"), ("2", "2", "num"), ("3", "3", "num"),
     (",", ",", "fn"), ("x²", "^2", "fn")],
    [("0", "0", "num"), (".", ".", "num"), ("EXP", "×10^(", "fn"),
     ("Ans", "Ans", "fn"), ("=", "@=", "eq")],
]

APPS = [
    ("Calculate", "Everyday and scientific", "close"),
    ("CAS Algebra", "Solve, factor, expand", "tab:CAS"),
    ("Equation", "Type x^2=4 then =", "tab:CAS"),
    ("Matrix", "det, inverse, solve", "tab:Stat"),
    ("Vector", "dot, cross, norm", "tab:Stat"),
    ("Complex", "i, Re, Im, arg", "tab:Num"),
    ("Statistics", "mean, stdev, reg", "tab:Stat"),
    ("Distribution", "normal, binomial", "tab:Stat"),
    ("Graph", "Plot f(x) of x", "graph"),
    ("Table", "Values of f(x)", "table"),
    ("Base-N", "bin, hex, AND, XOR", "tab:Num"),
    ("Convert", "Units, temperature", "tab:Conv"),
    ("Constants", "Physics constants", "tab:Const"),
]

DEL_RE = re.compile(r'(?:[A-Za-z0-9]+\(|√\(|"[^"]*"|Ans|Mem|phi|lightc|gravg|planckh|'
                    r'gravG|avog|boltz|echarge|gasR|emass|pmass|permit|permeab)$')


class Key(ButtonBehavior, Label):
    def __init__(self, bg=STY["num"][0], fg=WHITE, fs=22, **kw):
        kw.setdefault("halign", "center")
        kw.setdefault("valign", "middle")
        kw.setdefault("font_size", sp(fs))
        kw["color"] = fg
        super().__init__(**kw)
        self.bg = bg
        with self.canvas.before:
            self._col = Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(14)])
        self.bind(pos=self._sync, size=self._sync, state=self._sync)
        self.bind(size=lambda w, s: setattr(w, "text_size", s))

    def _sync(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        r, g, b, a = self.bg
        if self.state == "down":
            self._col.rgba = (min(r + .14, 1), min(g + .14, 1), min(b + .14, 1), a)
        else:
            self._col.rgba = self.bg


def make_label(text, fs, color, halign="right", valign="middle",
               bold=False, **kw):
    lbl = Label(text=text, font_size=sp(fs), color=color, halign=halign,
                valign=valign, bold=bold, **kw)
    lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
    return lbl


class GraphView(StencilView):
    def __init__(self, fn, **kw):
        super().__init__(**kw)
        self.fn = fn
        self.xmin, self.xmax = -10.0, 10.0
        self.ymin, self.ymax = -10.0, 10.0
        self.fit()
        self.bind(pos=self.redraw, size=self.redraw)

    def sample(self, n=300):
        pts = []
        for i in range(n + 1):
            x = self.xmin + (self.xmax - self.xmin) * i / n
            try:
                y = self.fn(x)
                if math.isnan(y) or math.isinf(y) or abs(y) > 1e9:
                    y = None
            except Exception:
                y = None
            pts.append((x, y))
        return pts

    def fit(self):
        ys = sorted(y for _, y in self.sample() if y is not None)
        if ys:
            a = int(0.03 * len(ys))
            lo, hi = ys[a], ys[len(ys) - 1 - a]
            if hi - lo < 1e-9:
                lo, hi = lo - 1, hi + 1
            pad = (hi - lo) * 0.15
            self.ymin, self.ymax = lo - pad, hi + pad

    def zoom(self, f):
        cx, cy = (self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2
        hw, hh = (self.xmax - self.xmin) / 2 * f, (self.ymax - self.ymin) / 2 * f
        self.xmin, self.xmax = cx - hw, cx + hw
        self.ymin, self.ymax = cy - hh, cy + hh
        self.redraw()

    def pan(self, d):
        dx = (self.xmax - self.xmin) * 0.25 * d
        self.xmin += dx
        self.xmax += dx
        self.redraw()

    def refit(self):
        self.fit()
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        if self.width < 10 or self.height < 10:
            return
        sx = self.width / (self.xmax - self.xmin)
        sy = self.height / (self.ymax - self.ymin)
        span = self.ymax - self.ymin
        with self.canvas:
            Color(0.07, 0.08, 0.11, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.28, 0.31, 0.38, 1)
            if self.xmin < 0 < self.xmax:
                x0 = self.x + (0 - self.xmin) * sx
                Line(points=[x0, self.y, x0, self.top], width=1.2)
            if self.ymin < 0 < self.ymax:
                y0 = self.y + (0 - self.ymin) * sy
                Line(points=[self.x, y0, self.right, y0], width=1.2)
            Color(0.3, 0.75, 1, 1)
            seg = []
            for x, y in self.sample(int(self.width / 2) + 1):
                if y is None or y < self.ymin - 3 * span or y > self.ymax + 3 * span:
                    if len(seg) >= 4:
                        Line(points=seg, width=1.6)
                    seg = []
                else:
                    seg += [self.x + (x - self.xmin) * sx, self.y + (y - self.ymin) * sy]
            if len(seg) >= 4:
                Line(points=seg, width=1.6)


class CalculatorApp(App):
    def build(self):
        self.title = "Calculator"
        Window.clearcolor = BG
        self.expr = ""
        self.ans = 0.0
        self.mem = 0.0
        self.deg = True
        self.frac = False
        self.just = False
        self.second = False
        self.sto = False
        self.last_val = 0
        self.vars = {n: 0 for n in VARS}
        self.history = []
        self.stack = []
        self.pkeys = []

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(5))

        head = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        names = BoxLayout(orientation="vertical")
        names.add_widget(make_label(CREATOR.upper(), 16, GOLD, halign="left", bold=True))
        names.add_widget(make_label("Creator of this calculator", 11, GRAY, halign="left"))
        head.add_widget(names)
        for t, tok in (("APPS", "@APPS"), ("HIST", "@HIST"), ("DEG", "@DEG")):
            k = self.mk(t, C_BAR, fs=12, tok=tok)
            k.size_hint_x = None
            k.width = dp(54)
            if t == "DEG":
                self.deg_btn = k
            head.add_widget(k)
        root.add_widget(head)

        disp = BoxLayout(orientation="vertical", size_hint_y=3, padding=(dp(8), 0))
        self.info_lbl = make_label("", 12, GRAY, halign="left", size_hint_y=0.18)
        self.expr_lbl = make_label("", 22, (0.70, 0.73, 0.80, 1), valign="bottom",
                                   size_hint_y=0.32, shorten=True, shorten_from="left")
        self.res_lbl = make_label("0", 50, WHITE, bold=True, size_hint_y=0.5)
        for w in (self.info_lbl, self.expr_lbl, self.res_lbl):
            disp.add_widget(w)
        root.add_widget(disp)

        strip = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4))
        for n in VARS:
            strip.add_widget(self.mk(n, C_BAR, fs=14, tok=n))
        self.sto_btn = self.mk("STO", STY["sh"][0], STY["sh"][1], fs=13, tok="@STO")
        strip.add_widget(self.sto_btn)
        root.add_widget(strip)

        tabs = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4))
        self.tab_btns = {}
        for t in TABS:
            b = Key(bg=C_BAR, fs=13, text=t, on_release=lambda w, t=t: self.show_tab(t))
            self.tab_btns[t] = b
            tabs.add_widget(b)
        root.add_widget(tabs)

        self.panel = GridLayout(cols=6, rows=4, spacing=dp(4), size_hint_y=3.4)
        root.add_widget(self.panel)

        pad = GridLayout(cols=5, rows=6, spacing=dp(5), size_hint_y=6)
        for row in PAD:
            for label, tok, st in row:
                bg, fg = STY[st]
                k = self.mk(label, bg, fg, fs=20 if st in ("num", "op", "eq") else 15, tok=tok)
                if tok == "@2nd":
                    self.second_btn = k
                pad.add_widget(k)
        root.add_widget(pad)

        self.show_tab("f(x)")
        self.refresh()
        return root

    # ---------- widgets ----------
    def mk(self, text, bg, fg=WHITE, fs=22, tok=None):
        return Key(bg=bg, fg=fg, fs=fs, text=text,
                   on_release=lambda w, t=tok: self.press(t))

    def show_tab(self, name):
        self.panel.clear_widgets()
        self.pkeys = []
        for spec in PANELS[name]:
            bg, fg = STY[spec[4]]
            k = Key(bg=bg, fg=fg, fs=13, text=spec[0],
                    on_release=lambda w, s=spec: self.on_panel(s))
            self.pkeys.append((k, spec))
            self.panel.add_widget(k)
        for t, b in self.tab_btns.items():
            b.bg = C_BAR_ON if t == name else C_BAR
            b._sync()
        self.relabel()

    def relabel(self):
        for k, spec in self.pkeys:
            k.text = spec[2] if (self.second and spec[2]) else spec[0]
        self.second_btn.bg = C_BAR_ON if self.second else STY["sh"][0]
        self.second_btn._sync()
        self.update_info()

    def on_panel(self, spec):
        tok = spec[3] if (self.second and spec[2]) else spec[1]
        self.press(tok)

    # ---------- display ----------
    def value(self):
        return evaluate(self.expr, self.deg, self.ans, self.mem, self.vars)

    def set_result(self, text, final, error=False):
        n = len(text)
        size = 50 if n <= 9 else 38 if n <= 13 else 28 if n <= 20 else 20 if n <= 40 else 15
        self.res_lbl.font_size = sp(size)
        self.res_lbl.text = text
        self.res_lbl.color = ((1, 0.45, 0.45, 1) if error
                              else WHITE if final else (0.62, 0.66, 0.75, 1))

    def update_info(self, note=None):
        t = "DEG" if self.deg else "RAD"
        t += "   " + ("FRAC" if self.frac else "DEC")
        if self.second:
            t += "   2nd"
        if self.sto:
            t += "   STO: tap x y z A B C"
        if self.mem != 0:
            t += "   M"
        self.info_lbl.text = note or t
        self.deg_btn.text = "DEG" if self.deg else "RAD"

    def refresh(self):
        self.expr_lbl.text = self.expr + (" =" if self.just else "")
        self.update_info()
        if self.just:
            return
        if not self.expr:
            self.set_result("0", True)
            return
        try:
            self.set_result(fmt(self.value(), self.frac), False)
        except CalcError:
            self.set_result("", False)

    # ---------- key handling ----------
    def press(self, t):
        if t == "@2nd":
            self.second = not self.second
            self.relabel()
            return
        if self.second:
            self.second = False
            self.relabel()
        if t in VARS and self.sto:
            self.store(t)
            return
        if t.startswith("@") and t != "@INV":
            self.action(t)
            return
        if len(self.expr) > 200:
            return
        self.stack.append(self.expr)
        del self.stack[:-100]
        follows = t in OPS or t in POST or t == "@INV"
        if self.just:
            self.just = False
            self.expr = "Ans" if follows else ""
        if not self.expr and follows and t not in ("-", "@INV"):
            if t in OPS and self.history:
                self.expr = "Ans"
            else:
                return
        if t == "@INV":
            self.expr = ("1÷(" + self.expr + ")") if self.expr else "1÷("
        elif t in OPS:
            if self.expr and self.expr[-1] in OPS:
                if t == "-" and self.expr[-1] in "×÷":
                    self.expr += t
                else:
                    self.expr = self.expr[:-1] + t
            else:
                self.expr += t
        else:
            self.expr += t
        self.refresh()

    def action(self, t):
        if t == "@AC":
            self.stack.append(self.expr)
            self.expr = ""
            self.just = False
            self.sto = False
            self.refresh()
        elif t == "@DEL":
            self.stack.append(self.expr)
            self.just = False
            m = DEL_RE.search(self.expr)
            self.expr = self.expr[:m.start()] if m else self.expr[:-1]
            self.refresh()
        elif t == "@UNDO":
            if self.stack:
                self.expr = self.stack.pop()
                self.just = False
                self.refresh()
        elif t == "@=":
            self.equals()
        elif t == "@SD":
            self.frac = not self.frac
            if self.just:
                try:
                    self.set_result(fmt(self.last_val, self.frac), True)
                except CalcError:
                    pass
                self.update_info()
            else:
                self.refresh()
        elif t == "@DEG":
            self.deg = not self.deg
            self.refresh()
        elif t == "@STO":
            self.sto = not self.sto
            self.update_info()
        elif t == "@MC":
            self.mem = 0.0
            self.update_info()
        elif t == "@MR":
            self.press("Mem")
        elif t in ("@M+", "@M-"):
            try:
                v = self.ans if (self.just or not self.expr) else self.value()
                v = float(v)
            except Exception:
                return
            self.mem += v if t == "@M+" else -v
            self.update_info()
        elif t == "@HIST":
            self.show_history()
        elif t == "@APPS":
            self.show_apps()
        elif t == "@GRAPH":
            self.open_graph(table=False)
        elif t == "@TABLE":
            self.open_graph(table=True)

    def equals(self):
        if not self.expr or self.just:
            return
        try:
            v = self.value()
            text = fmt(v, self.frac)
        except CalcError:
            self.set_result("Error", True, error=True)
            return
        if not isinstance(v, str):
            self.ans = v
        self.last_val = v
        self.history.insert(0, (self.expr, text))
        del self.history[50:]
        self.just = True
        self.expr_lbl.text = self.expr + " ="
        self.set_result(text, True)

    def store(self, name):
        self.sto = False
        try:
            v = self.ans if (self.just or not self.expr) else self.value()
            if isinstance(v, (str, list)):
                raise CalcError("type")
            self.vars[name] = v
            self.update_info("%s = %s" % (name, fmt(v)))
        except CalcError:
            self.update_info("Cannot store this value")

    # ---------- windows ----------
    def modal(self, title):
        view = ModalView(size_hint=(0.94, 0.85), background="",
                         background_color=(0.09, 0.10, 0.13, 1))
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        box.add_widget(make_label(title, 20, WHITE, halign="left", bold=True,
                                  size_hint_y=None, height=dp(36)))
        view.add_widget(box)
        return view, box

    def show_history(self):
        view, box = self.modal("History")
        scroll = ScrollView()
        lst = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        if not self.history:
            lst.add_widget(make_label("Nothing yet", 16, GRAY, size_hint_y=None,
                                      height=dp(50)))
        for e, r in self.history:
            def load(w, e=e):
                self.expr = e
                self.just = False
                view.dismiss()
                self.refresh()
            lst.add_widget(Key(bg=STY["num"][0], fs=16, text="%s  =  %s" % (e, r),
                               halign="left", padding=(dp(14), 0), shorten=True,
                               shorten_from="right", size_hint_y=None,
                               height=dp(56), on_release=load))
        scroll.add_widget(lst)
        box.add_widget(scroll)
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))

        def clear(w):
            self.history = []
            view.dismiss()

        btns.add_widget(Key(bg=STY["clr"][0], fg=STY["clr"][1], fs=16, text="Clear",
                            on_release=clear))
        btns.add_widget(Key(bg=STY["fn"][0], fs=16, text="Close",
                            on_release=lambda w: view.dismiss()))
        box.add_widget(btns)
        view.open()

    def show_apps(self):
        view, box = self.modal("Apps")
        scroll = ScrollView()
        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for name, sub, act in APPS:
            def go(w, act=act):
                view.dismiss()
                if act.startswith("tab:"):
                    self.show_tab(act[4:])
                elif act == "graph":
                    self.open_graph(table=False)
                elif act == "table":
                    self.open_graph(table=True)
            grid.add_widget(Key(bg=STY["fn"][0], fs=14, text="%s\n%s" % (name, sub),
                                size_hint_y=None, height=dp(74), on_release=go))
        scroll.add_widget(grid)
        box.add_widget(scroll)
        box.add_widget(Key(bg=STY["fn"][0], fs=16, text="Close", size_hint_y=None,
                           height=dp(48), on_release=lambda w: view.dismiss()))
        view.open()

    def open_graph(self, table=False):
        expr = self.expr
        if not expr:
            self.update_info("Type a formula in x first, e.g. x^2-4")
            return
        try:
            fn = compile_fn(expr, self.deg, self.ans, self.mem, self.vars)
        except Exception:
            self.set_result("Error", True, error=True)
            return
        view, box = self.modal(("Table:  " if table else "Graph:  ") + expr)
        if table:
            scroll = ScrollView()
            lst = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
            lst.bind(minimum_height=lst.setter("height"))
            for x in range(-10, 11):
                try:
                    y = fmt(_tidy(fn(float(x)), 1e-9))
                except Exception:
                    y = "undefined"
                lst.add_widget(make_label("x = %d      f = %s" % (x, y), 17, WHITE,
                                          halign="left", size_hint_y=None, height=dp(34)))
            scroll.add_widget(lst)
            box.add_widget(scroll)
        else:
            gv = GraphView(fn)
            box.add_widget(gv)
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
            for t, f in (("+", lambda w: gv.zoom(0.5)), ("-", lambda w: gv.zoom(2.0)),
                         ("<", lambda w: gv.pan(-1)), (">", lambda w: gv.pan(1)),
                         ("Fit", lambda w: gv.refit())):
                row.add_widget(Key(bg=STY["fn"][0], fs=18, text=t, on_release=f))
            box.add_widget(row)
        box.add_widget(Key(bg=STY["fn"][0], fs=16, text="Close", size_hint_y=None,
                           height=dp(46), on_release=lambda w: view.dismiss()))
        view.open()


if __name__ == "__main__":
    CalculatorApp().run()
