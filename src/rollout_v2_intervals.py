"""Directed binary64 intervals using MPFR-192 operations (64-bit ABI).

New v2 code, not the missing historical implementation. Single-threaded scratch
MPFR values; MPFR is dynamically linked, not redistributed. Every exported
endpoint is rounded outwards to binary64, so JSON preserves the enclosure.
"""
import ctypes.util
import math
from fractions import Fraction
from cffi import FFI

ffi = FFI()
ffi.cdef("""
typedef struct { long _mpfr_prec; int _mpfr_sign; long _mpfr_exp;
                 unsigned long *_mpfr_d; } mpfr_s;
void mpfr_init2(mpfr_s *, long);
int mpfr_set_d(mpfr_s *, double, int);
double mpfr_get_d(const mpfr_s *, int);
int mpfr_set_str(mpfr_s *, const char *, int, int);
int mpfr_add(mpfr_s *, const mpfr_s *, const mpfr_s *, int);
int mpfr_sub(mpfr_s *, const mpfr_s *, const mpfr_s *, int);
int mpfr_mul(mpfr_s *, const mpfr_s *, const mpfr_s *, int);
int mpfr_div(mpfr_s *, const mpfr_s *, const mpfr_s *, int);
int mpfr_div_ui(mpfr_s *, const mpfr_s *, unsigned long, int);
int mpfr_exp(mpfr_s *, const mpfr_s *, int);
int mpfr_log(mpfr_s *, const mpfr_s *, int);
int mpfr_sqrt(mpfr_s *, const mpfr_s *, int);
int mpfr_erfc(mpfr_s *, const mpfr_s *, int);
int mpfr_const_pi(mpfr_s *, int);
int mpfr_nan_p(const mpfr_s *);
const char *mpfr_get_version(void);
long mpfr_get_prec(const mpfr_s *);
""")
assert ffi.sizeof("long") == 8 and ffi.sizeof("double") == 8
lib = ffi.dlopen(ctypes.util.find_library("mpfr"))
scratch = [ffi.new("mpfr_s *") for _ in range(6)]
for number in scratch:
    lib.mpfr_init2(number, 192)
assert lib.mpfr_get_prec(scratch[0]) == 192
VERSION = ffi.string(lib.mpfr_get_version()).decode()
DOWN, UP = 3, 2


def op(name, a, b=None, upward=False):
    mode = UP if upward else DOWN
    lib.mpfr_set_d(scratch[0], float(a), 0)
    if b is None:
        getattr(lib, "mpfr_"+name)(scratch[2], scratch[0], mode)
    else:
        lib.mpfr_set_d(scratch[1], float(b), 0)
        getattr(lib, "mpfr_"+name)(scratch[2], scratch[0], scratch[1], mode)
    if lib.mpfr_nan_p(scratch[2]):
        raise ArithmeticError("NaN interval operation")
    return float(lib.mpfr_get_d(scratch[2], mode))


class I:
    __slots__ = ("lo", "hi")

    def __init__(self, value=0., high=None):
        if isinstance(value, I):
            self.lo, self.hi = value.lo, value.hi
            return
        if high is None and isinstance(value, (tuple, list)):
            value, high = value
        self.lo = float(value)
        self.hi = float(value if high is None else high)
        if math.isnan(self.lo) or math.isnan(self.hi) or self.lo > self.hi:
            raise ValueError("Invalid interval")

    def __add__(self, other):
        other = I(other)
        return I(op("add", self.lo, other.lo), op("add", self.hi, other.hi, True))

    __radd__ = __add__

    def __neg__(self):
        return I(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + -I(other)

    def __rsub__(self, other):
        return I(other) - self

    def __mul__(self, other):
        other = I(other)
        pairs = [(x, y) for x in (self.lo, self.hi) for y in (other.lo, other.hi)]
        return I(min(op("mul", x, y) for x, y in pairs),
                 max(op("mul", x, y, True) for x, y in pairs))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = I(other)
        if other.lo <= 0 <= other.hi:
            raise ZeroDivisionError("Interval denominator contains zero")
        pairs = [(x, y) for x in (self.lo, self.hi) for y in (other.lo, other.hi)]
        return I(min(op("div", x, y) for x, y in pairs),
                 max(op("div", x, y, True) for x, y in pairs))

    def __rtruediv__(self, other):
        return I(other) / self

    def square(self):
        if self.lo <= 0 <= self.hi:
            return I(0, max(op("mul", self.lo, self.lo, True),
                            op("mul", self.hi, self.hi, True)))
        a, b = sorted((abs(self.lo), abs(self.hi)))
        return I(op("mul", a, a), op("mul", b, b, True))

    def exp(self):
        return I(op("exp", self.lo), op("exp", self.hi, upward=True))

    def log(self):
        if self.lo <= 0:
            raise ValueError("Nonpositive logarithm")
        return I(op("log", self.lo), op("log", self.hi, upward=True))

    def sqrt(self):
        if self.lo < 0:
            raise ValueError("Negative square root")
        return I(op("sqrt", self.lo), op("sqrt", self.hi, upward=True))

    def clipped(self, low, high):
        # Intersection only when the exact quantity is independently in range.
        return I(max(low, self.lo), min(high, self.hi))

    def minimum(self, other):
        other = I(other)
        return I(min(self.lo, other.lo), min(self.hi, other.hi))

    def hull(self, other):
        other = I(other)
        return I(min(self.lo, other.lo), max(self.hi, other.hi))

    def intersect(self, other):
        other = I(other)
        return I(max(self.lo, other.lo), min(self.hi, other.hi))

    def pair(self):
        return [self.lo, self.hi]

    def width(self):
        return op("sub", self.hi, self.lo, upward=True)

    def mid(self):
        return self.lo/2+self.hi/2

    def __repr__(self):
        return f"I({self.lo!r}, {self.hi!r})"


def fraction_interval(value):
    value = Fraction(value)
    ends = []
    for mode in (DOWN, UP):
        lib.mpfr_set_str(scratch[0], str(value.numerator).encode(), 10, mode)
        lib.mpfr_set_str(scratch[1], str(value.denominator).encode(), 10,
                         UP if mode == DOWN else DOWN)
        # Numerator sign changes which denominator endpoint is conservative.
        if value < 0:
            lib.mpfr_set_str(scratch[1], str(value.denominator).encode(), 10, mode)
        lib.mpfr_div(scratch[2], scratch[0], scratch[1], mode)
        ends.append(float(lib.mpfr_get_d(scratch[2], mode)))
    return I(*ends)


def pi():
    ends = []
    for mode in (DOWN, UP):
        lib.mpfr_const_pi(scratch[2], mode)
        ends.append(float(lib.mpfr_get_d(scratch[2], mode)))
    return I(*ends)


SQRT2 = I(2).sqrt()
SQRT2PI = (2*pi()).sqrt()


def cdf(x):
    x = I(x)
    if x.lo == x.hi == math.inf:
        return I(1)
    if x.lo == x.hi == -math.inf:
        return I(0)
    arg = -x/SQRT2
    return I(op("erfc", arg.hi), op("erfc", arg.lo, upward=True))/2


def density(x):
    return (-I(x).square()/2).exp()/SQRT2PI


def probability(low, high):
    low, high = I(low), I(high)
    result = (cdf(-low)-cdf(-high) if low.lo >= 0 else cdf(high)-cdf(low))
    return result.clipped(0., 1.)


def exp_times_cdf(logm, cutoff):
    """Avoid binary64 underflow/overflow between exp and the normal CDF."""
    logm, cutoff = I(logm), I(cutoff)
    arg = -cutoff/SQRT2
    ends = []
    for mode, lm, ar in ((DOWN, logm.lo, arg.hi), (UP, logm.hi, arg.lo)):
        lib.mpfr_set_d(scratch[0], lm, 0)
        lib.mpfr_exp(scratch[3], scratch[0], mode)
        lib.mpfr_set_d(scratch[1], ar, 0)
        lib.mpfr_erfc(scratch[4], scratch[1], mode)
        lib.mpfr_div_ui(scratch[4], scratch[4], 2, mode)
        lib.mpfr_mul(scratch[2], scratch[3], scratch[4], mode)
        if lib.mpfr_nan_p(scratch[2]):
            raise ArithmeticError("Invalid truncated expectation")
        ends.append(float(lib.mpfr_get_d(scratch[2], mode)))
    return I(*ends)
