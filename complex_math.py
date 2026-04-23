from __future__ import annotations

from typing import Literal

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)

Z = sp.Symbol("z")
T = sp.Symbol("t", real=True)
X = sp.Symbol("x", real=True)
Y = sp.Symbol("y", real=True)

SAFE_LOCALS = {
    "I": sp.I,
    "i": sp.I,
    "j": sp.I,
    "pi": sp.pi,
    "e": sp.E,
    "E": sp.E,
    "oo": sp.oo,
    "inf": sp.oo,
    "infinity": sp.oo,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "sec": sp.sec,
    "csc": sp.csc,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "asinh": sp.asinh,
    "acosh": sp.acosh,
    "atanh": sp.atanh,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "Abs": sp.Abs,
    "re": sp.re,
    "im": sp.im,
    "arg": sp.arg,
    "conj": sp.conjugate,
    "conjugate": sp.conjugate,
}


class MathInputError(ValueError):
    pass


def analyze_complex_function(
    *,
    function_text: str,
    contour_text: str,
    t_min_text: str,
    t_max_text: str,
    component: Literal["abs", "real", "imag"],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    resolution: int,
    integral_samples: int,
) -> dict:
    if x_max <= x_min:
        raise MathInputError("x_max must be greater than x_min.")
    if y_max <= y_min:
        raise MathInputError("y_max must be greater than y_min.")

    function_expr = _parse_expression(function_text, {"z": Z})
    contour_expr = _parse_expression(contour_text, {"t": T})
    t_min = _parse_real_number(t_min_text)
    t_max = _parse_real_number(t_max_text)

    if t_max <= t_min:
        raise MathInputError("t_max must be greater than t_min.")

    integral_payload = _build_integral_payload(
        function_expr=function_expr,
        contour_expr=contour_expr,
        t_min=t_min,
        t_max=t_max,
        integral_samples=integral_samples,
    )
    plot_payload = _build_plot_payload(
        function_expr=function_expr,
        contour_expr=contour_expr,
        component=component,
        t_min=t_min,
        t_max=t_max,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        resolution=resolution,
    )

    return {
        "function_display": sp.sstr(function_expr),
        "contour_display": sp.sstr(contour_expr),
        "parameter_interval": [t_min, t_max],
        "component": component,
        "integral": integral_payload,
        "plot": plot_payload,
    }


def _parse_expression(text: str, allowed_symbols: dict[str, sp.Symbol]) -> sp.Expr:
    cleaned = text.strip()
    if not cleaned:
        raise MathInputError("Input cannot be empty.")

    local_dict = dict(SAFE_LOCALS)
    local_dict.update(allowed_symbols)

    try:
        expr = parse_expr(
            cleaned,
            local_dict=local_dict,
            transformations=TRANSFORMATIONS,
            evaluate=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise MathInputError(f"Could not parse `{text}`.") from exc

    unknown_symbols = sorted(str(symbol) for symbol in expr.free_symbols if symbol not in allowed_symbols.values())
    if unknown_symbols:
        joined = ", ".join(unknown_symbols)
        raise MathInputError(f"Unsupported variable(s): {joined}.")

    return sp.simplify(expr)


def _parse_real_number(text: str) -> float:
    expr = _parse_expression(text, {})
    numeric_value = complex(sp.N(expr, 30))
    if abs(numeric_value.imag) > 1e-10:
        raise MathInputError(f"Expected a real value for `{text}`.")
    return float(numeric_value.real)


def _component_expr(function_expr: sp.Expr, component: Literal["abs", "real", "imag"]) -> sp.Expr:
    cartesian_expr = function_expr.subs(Z, X + sp.I * Y)
    if component == "real":
        return sp.simplify(sp.re(cartesian_expr))
    if component == "imag":
        return sp.simplify(sp.im(cartesian_expr))
    return sp.simplify(sp.Abs(cartesian_expr))


def _curve_component_expr(
    function_expr: sp.Expr,
    contour_expr: sp.Expr,
    component: Literal["abs", "real", "imag"],
) -> sp.Expr:
    curve_expr = function_expr.subs(Z, contour_expr)
    if component == "real":
        return sp.simplify(sp.re(curve_expr))
    if component == "imag":
        return sp.simplify(sp.im(curve_expr))
    return sp.simplify(sp.Abs(curve_expr))


def _build_integral_payload(
    *,
    function_expr: sp.Expr,
    contour_expr: sp.Expr,
    t_min: float,
    t_max: float,
    integral_samples: int,
) -> dict:
    contour_derivative = sp.diff(contour_expr, T)
    integrand_expr = sp.simplify(function_expr.subs(Z, contour_expr) * contour_derivative)

    symbolic_result = None
    try:
        candidate = sp.simplify(sp.integrate(integrand_expr, (T, t_min, t_max)))
        if not candidate.has(sp.Integral):
            symbolic_result = sp.sstr(candidate)
    except Exception:  # noqa: BLE001
        symbolic_result = None

    numeric_func = sp.lambdify(T, integrand_expr, modules=["numpy"])
    t_values = np.linspace(t_min, t_max, integral_samples, dtype=float)
    with np.errstate(all="ignore"):
        numeric_values = _ensure_complex_array(numeric_func(t_values), t_values.shape)

    if not np.isfinite(numeric_values.real).all() or not np.isfinite(numeric_values.imag).all():
        raise MathInputError("The contour integral hits a non-finite value on the chosen path.")

    numeric_result = np.trapezoid(numeric_values, t_values)

    return {
        "integrand_display": sp.sstr(integrand_expr),
        "symbolic_result": symbolic_result,
        "numeric_rectangular": _format_complex(numeric_result),
        "numeric_polar": _format_polar(numeric_result),
        "real_part": float(np.real(numeric_result)),
        "imag_part": float(np.imag(numeric_result)),
        "magnitude": float(np.abs(numeric_result)),
    }


def _build_plot_payload(
    *,
    function_expr: sp.Expr,
    contour_expr: sp.Expr,
    component: Literal["abs", "real", "imag"],
    t_min: float,
    t_max: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    resolution: int,
) -> dict:
    x_values = np.linspace(x_min, x_max, resolution, dtype=float)
    y_values = np.linspace(y_min, y_max, resolution, dtype=float)
    x_grid, y_grid = np.meshgrid(x_values, y_values)

    surface_expr = _component_expr(function_expr, component)
    surface_func = sp.lambdify((X, Y), surface_expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        surface_values = _ensure_real_array(surface_func(x_grid, y_grid), x_grid.shape)
    finite_surface = np.isfinite(surface_values)
    surface_values = np.where(finite_surface, surface_values, np.nan)
    surface_values = _clip_for_display(surface_values, component)

    t_curve = np.linspace(t_min, t_max, max(300, resolution * 6), dtype=float)
    contour_func = sp.lambdify(T, contour_expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        contour_values = _ensure_complex_array(contour_func(t_curve), t_curve.shape)

    curve_component = _curve_component_expr(function_expr, contour_expr, component)
    curve_height_func = sp.lambdify(T, curve_component, modules=["numpy"])
    with np.errstate(all="ignore"):
        contour_heights = _ensure_real_array(curve_height_func(t_curve), t_curve.shape)
    contour_heights = _clip_for_display(contour_heights, component)

    return {
        "surface": {
            "x": x_values.tolist(),
            "y": y_values.tolist(),
            "z": surface_values.tolist(),
        },
        "contour": {
            "x": np.real(contour_values).tolist(),
            "y": np.imag(contour_values).tolist(),
            "z": contour_heights.tolist(),
        },
        "surface_label": _surface_label(component),
        "z_cap": _display_cap(surface_values, component),
    }


def _ensure_complex_array(values: object, target_shape: tuple[int, ...]) -> np.ndarray:
    array = np.asarray(values, dtype=np.complex128)
    if array.shape == ():
        array = np.full(target_shape, array.item(), dtype=np.complex128)
    return array


def _ensure_real_array(values: object, target_shape: tuple[int, ...]) -> np.ndarray:
    array = np.asarray(values, dtype=np.complex128)
    if array.shape == ():
        array = np.full(target_shape, array.item(), dtype=np.complex128)
    array = np.real_if_close(array, tol=1000)
    return np.asarray(array, dtype=float)


def _clip_for_display(values: np.ndarray, component: Literal["abs", "real", "imag"]) -> np.ndarray:
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return values

    if component == "abs":
        cap = max(float(np.nanpercentile(finite_values, 97)), 1.0)
        return np.clip(values, 0.0, cap)

    cap = max(float(np.nanpercentile(np.abs(finite_values), 97)), 1.0)
    return np.clip(values, -cap, cap)


def _display_cap(values: np.ndarray, component: Literal["abs", "real", "imag"]) -> float:
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return 0.0
    if component == "abs":
        return float(np.max(finite_values))
    return float(np.max(np.abs(finite_values)))


def _surface_label(component: Literal["abs", "real", "imag"]) -> str:
    if component == "real":
        return "Re(f(z))"
    if component == "imag":
        return "Im(f(z))"
    return "|f(z)|"


def _format_complex(value: complex) -> str:
    real_part = np.real(value)
    imag_part = np.imag(value)
    sign = "+" if imag_part >= 0 else "-"
    return f"{real_part:.8f} {sign} {abs(imag_part):.8f}i"


def _format_polar(value: complex) -> str:
    magnitude = np.abs(value)
    angle = np.angle(value)
    return f"{magnitude:.8f} * exp(i {angle:.8f})"
