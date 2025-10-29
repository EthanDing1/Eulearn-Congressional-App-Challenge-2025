import numpy as np
import sympy as sp
from scipy.integrate import dblquad, quad
from scipy.optimize import brentq
import warnings
import logging

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class PolarIntegrationError(Exception):
    """Custom exception for polar integration errors"""
    pass


def safe_lambdify(expr, var, modules="numpy"):
    """
    Safely convert a SymPy expression to a numerical function with error handling.
    """
    try:
        return sp.lambdify(var, expr, modules)
    except Exception as e:
        logger.error(f"Failed to lambdify expression {expr}: {e}")
        raise PolarIntegrationError(f"Could not convert expression to numerical function: {e}")


def safe_evaluate(func, value, default=0.0):
    """
    Safely evaluate a function at a given value with fallback.
    """
    try:
        result = float(func(value))
        if np.isnan(result) or np.isinf(result):
            logger.warning(f"Function returned {result} at value {value}")
            return default
        return result
    except Exception as e:
        logger.debug(f"Function evaluation failed at {value}: {e}")
        return default


def has_no_intersections(inner_expr, outer_expr, theta_var, theta_start, theta_end):
    """
    Check if two polar curves intersect in the given theta range.
    Returns True if NO intersections exist, False if intersections are found.
    """
    try:
        f_in = safe_lambdify(inner_expr, theta_var)
        f_out = safe_lambdify(outer_expr, theta_var)
        
        def difference(theta):
            """Returns r_inner - r_outer at given theta"""
            val_in = safe_evaluate(f_in, theta, 0.0)
            val_out = safe_evaluate(f_out, theta, 0.0)
            return val_in - val_out
        
        try:
            thetas = np.linspace(float(theta_start), float(theta_end), 2000)
        except Exception as e:
            logger.error(f"Failed to create theta range: {e}")
            return True
        
        diff_vals = np.array([difference(t) for t in thetas])
        
        if np.any(np.isnan(diff_vals)) or np.any(np.isinf(diff_vals)):
            logger.warning("NaN or Inf values detected in difference calculation")
            return True
        
        if np.all(diff_vals >= -1e-10) or np.all(diff_vals <= 1e-10):
            return True
        
        sign_changes = np.where(np.diff(np.sign(diff_vals)))[0]
        
        if len(sign_changes) == 0:
            return True
        
        for idx in sign_changes:
            theta_left = thetas[idx]
            theta_right = thetas[idx + 1]
            
            val_left = difference(theta_left)
            val_right = difference(theta_right)
            
            if val_left * val_right < 0:
                try:
                    root = brentq(difference, theta_left, theta_right, xtol=1e-10)
                    return False
                except Exception as e:
                    logger.debug(f"Root finding failed: {e}")
                    return False
        
        return True
        
    except PolarIntegrationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in has_no_intersections: {e}")
        return True


def adjust_integration_bounds(expr, theta_var, theta_start, theta_end):
    """
    Adjust integration bounds for curves that cross the pole (r=0).
    For curves like r=cos(theta) that are only defined on one side,
    integrate over the natural range to avoid double-counting.
    """
    try:
        if abs(theta_start - 0) > 0.01 or abs(theta_end - 2*np.pi) > 0.01:
            return theta_start, theta_end
        
        f = safe_lambdify(expr, theta_var)
        
        try:
            thetas = np.linspace(0, 2*np.pi, 1000)
        except Exception as e:
            logger.error(f"Failed to create theta range for bounds adjustment: {e}")
            return theta_start, theta_end
        
        vals = np.array([safe_evaluate(f, t, 0.0) for t in thetas])
        
        if np.any(np.isnan(vals)) or np.any(np.isinf(vals)):
            logger.warning("Invalid values detected in bounds adjustment")
            return theta_start, theta_end
        
        zero_crossings = []
        for i in range(len(vals) - 1):
            if vals[i] * vals[i+1] < 0:
                try:
                    crossing = brentq(lambda t: safe_evaluate(f, t, 0.0), thetas[i], thetas[i+1])
                    zero_crossings.append(crossing)
                except Exception as e:
                    logger.debug(f"Root finding failed in bounds adjustment: {e}")
                    zero_crossings.append(thetas[i])
        
        if len(zero_crossings) >= 2:
            return zero_crossings[0], zero_crossings[1]
            
    except PolarIntegrationError:
        raise
    except Exception as e:
        logger.error(f"Error in adjust_integration_bounds: {e}")
    
    return theta_start, theta_end


def solve_polar(inner_expr, outer_expr, theta_var,
                theta_start=0.0, theta_end=2 * np.pi, method='auto'):
    """
    Area inside `inner_expr` and outside `outer_expr` in polar coords.
    Semantics: compute area of points that lie inside the region traced by
    r = inner_expr(θ) and not inside r = outer_expr(θ).
    
    Raises:
        PolarIntegrationError: If integration fails
        ValueError: If input parameters are invalid
    """
    try:
        if not isinstance(theta_start, (int, float)) or not isinstance(theta_end, (int, float)):
            raise ValueError("theta_start and theta_end must be numeric values")
        
        if theta_start >= theta_end:
            if not (theta_start >= 0 and theta_end == 0):
                raise ValueError(f"theta_start ({theta_start}) must be less than theta_end ({theta_end})")
        
        if method not in ['auto', 'cartesian', 'polar']:
            raise ValueError(f"method must be 'auto', 'cartesian', or 'polar', got '{method}'")
        
        if has_no_intersections(inner_expr, outer_expr, theta_var, theta_start, theta_end):
            try:
                f_in = safe_lambdify(inner_expr, theta_var)
                f_out = safe_lambdify(outer_expr, theta_var)
                
                adj_start_in, adj_end_in = adjust_integration_bounds(inner_expr, theta_var, theta_start, theta_end)
                adj_start_out, adj_end_out = adjust_integration_bounds(outer_expr, theta_var, theta_start, theta_end)
                
                area_inner, err_in = quad(
                    lambda t: 0.5 * safe_evaluate(f_in, t, 0.0)**2, 
                    adj_start_in, adj_end_in,
                    epsabs=1e-8, epsrel=1e-8
                )
                area_outer, err_out = quad(
                    lambda t: 0.5 * safe_evaluate(f_out, t, 0.0)**2, 
                    adj_start_out, adj_end_out,
                    epsabs=1e-8, epsrel=1e-8
                )
                
                if err_in > 1e-6 or err_out > 1e-6:
                    logger.warning(f"High integration error: inner={err_in}, outer={err_out}")
                
                res = area_inner - area_outer
                return max(res, 0)
                
            except Exception as e:
                logger.error(f"Error in no-intersection case: {e}")
                raise PolarIntegrationError(f"Failed to compute area for non-intersecting curves: {e}")

        try:
            if not isinstance(inner_expr, sp.Expr):
                inner_expr = sp.sympify(inner_expr)
            if not isinstance(outer_expr, sp.Expr):
                outer_expr = sp.sympify(outer_expr)
        except Exception as e:
            raise ValueError(f"Could not convert expressions to SymPy format: {e}")

        try:
            diff_eq = sp.Eq(sp.simplify(inner_expr**2 - outer_expr**2), 0)
            sols = sp.solveset(diff_eq, theta_var,
                               domain=sp.Interval(theta_start, theta_end))

            if getattr(sols, "is_empty", False) or sols == sp.EmptySet:
                f_in = safe_lambdify(inner_expr, theta_var)
                f_out = safe_lambdify(outer_expr, theta_var)

                thetas = np.linspace(theta_start, theta_end, 2000)
                inner_sq = np.array([safe_evaluate(f_in, t, 0.0)**2 for t in thetas])
                outer_sq = np.array([safe_evaluate(f_out, t, 0.0)**2 for t in thetas])

                if np.all(inner_sq >= outer_sq - 1e-8):
                    A_inner = _compute_single_area(inner_expr, theta_var, theta_start, theta_end)
                    A_outer = _compute_single_area(outer_expr, theta_var, theta_start, theta_end)
                    return A_inner - A_outer
                else:
                    return 0.0
        except Exception as e:
            logger.warning(f"Symbolic intersection check failed, continuing with numerical methods: {e}")

        try:
            if sp.simplify(inner_expr - outer_expr) == 0:
                return 0.0
        except Exception as e:
            logger.debug(f"Could not check for trivial equality: {e}")

        if abs(theta_end - theta_start - 2 * np.pi) < 1e-10:
            theta_end = theta_start + 2 * np.pi - 1e-10

        symmetry_factor, reduced_start, reduced_end = _detect_symmetry(
            inner_expr, outer_expr, theta_var, theta_start, theta_end
        )

        if method == 'auto':
            method = _choose_method(inner_expr, outer_expr)

        try:
            if method == 'cartesian':
                area = _cartesian_area(inner_expr, outer_expr, theta_var,
                                       reduced_start, reduced_end)
            else:
                area = _polar_area(inner_expr, outer_expr, theta_var,
                                   reduced_start, reduced_end)
            
            if np.isnan(area) or np.isinf(area):
                raise PolarIntegrationError(f"Integration resulted in {area}")
            
            return area * symmetry_factor
            
        except Exception as e:
            logger.error(f"Integration method '{method}' failed: {e}")
            raise PolarIntegrationError(f"Integration failed using {method} method: {e}")

    except (PolarIntegrationError, ValueError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in solve_polar: {e}")
        raise PolarIntegrationError(f"Unexpected error during polar integration: {e}")


def _detect_symmetry(expr1, expr2, theta_var, theta_start, theta_end):
    """Detect symmetry in expressions (placeholder for now)"""
    return 1, theta_start, theta_end


def _choose_method(expr1, expr2):
    """Choose integration method based on expression complexity"""
    try:
        ops1 = sp.count_ops(expr1)
        ops2 = sp.count_ops(expr2)
        return 'cartesian' if ops1 + ops2 > 15 else 'polar'
    except Exception as e:
        logger.warning(f"Could not count operations, defaulting to polar: {e}")
        return 'polar'


def _cartesian_area(inner_expr, outer_expr, theta_var,
                    theta_start, theta_end):
    """
    Fallback Cartesian double integral over bounding circle.
    Uses absolute magnitudes for radii comparisons.
    """
    try:
        inner_func = safe_lambdify(inner_expr, theta_var)
        outer_func = safe_lambdify(outer_expr, theta_var)

        theta_samples = np.linspace(theta_start, theta_end, 1000)
        all_inner = [abs(safe_evaluate(inner_func, t, 0.0)) for t in theta_samples]
        all_outer = [abs(safe_evaluate(outer_func, t, 0.0)) for t in theta_samples]
        
        if not all_inner or not all_outer:
            raise PolarIntegrationError("Could not sample curve values")
        
        max_radius = max(max(all_inner), max(all_outer)) * 1.1
        
        if max_radius <= 0 or np.isnan(max_radius) or np.isinf(max_radius):
            logger.warning("Invalid max_radius, returning 0")
            return 0.0

        def point_in_intersection(x, y):
            try:
                r = np.sqrt(x**2 + y**2)
                if r < 1e-12:
                    return 1.0
                theta_point = np.arctan2(y, x)
                if theta_point < 0:
                    theta_point += 2 * np.pi

                if theta_start <= theta_end:
                    if not (theta_start <= theta_point <= theta_end):
                        return 0.0
                else:
                    if not (theta_point >= theta_start or theta_point <= theta_end):
                        return 0.0

                inner_val = safe_evaluate(inner_func, theta_point, 0.0)
                outer_val = safe_evaluate(outer_func, theta_point, 0.0)
                
                inside_inner = r <= abs(inner_val) + 1e-12 and abs(inner_val) > 1e-12
                inside_outer = r <= abs(outer_val) + 1e-12 and abs(outer_val) > 1e-12
                return 1.0 if (inside_inner and not inside_outer) else 0.0
            except Exception:
                return 0.0

        def integrand(r_coord, theta_coord):
            try:
                x = r_coord * np.cos(theta_coord)
                y = r_coord * np.sin(theta_coord)
                return r_coord * point_in_intersection(x, y)
            except Exception:
                return 0.0

        area, error = dblquad(
            integrand, 0, 2 * np.pi,
            lambda t: 0, lambda t: max_radius,
            epsabs=1e-8, epsrel=1e-8
        )
        
        if error > 1e-6:
            logger.warning(f"High integration error in Cartesian method: {error}")
        
        return max(area, 0.0)
        
    except Exception as e:
        logger.error(f"Cartesian area calculation failed: {e}")
        raise PolarIntegrationError(f"Cartesian integration failed: {e}")


def _polar_area(inner_expr, outer_expr, theta_var,
               theta_start, theta_end):
    """
    Robust polar integrator with proper handling of negative r values.
    """
    try:
        inner_func = safe_lambdify(inner_expr, theta_var)
        outer_func = safe_lambdify(outer_expr, theta_var)

        tol = 1e-12

        def radial_candidates(f, theta):
            """Get non-negative radial distances where curve intersects ray"""
            candidates = []
            
            v = safe_evaluate(f, theta, None)
            if v is not None and v >= -tol:
                candidates.append(max(0.0, v))
            
            v2 = safe_evaluate(f, theta - np.pi, None)
            if v2 is not None and v2 < -tol:
                candidates.append(abs(v2))
            
            return candidates

        def integrand(theta):
            try:
                rin_list = radial_candidates(inner_func, theta)
                rout_list = radial_candidates(outer_func, theta)

                r_in = max(rin_list) if len(rin_list) > 0 else 0.0
                r_out = max(rout_list) if len(rout_list) > 0 else 0.0

                if r_in > r_out + 1e-14:
                    result = 0.5 * (r_in * r_in - r_out * r_out)
                    if np.isnan(result) or np.isinf(result):
                        return 0.0
                    return result
                else:
                    return 0.0
            except Exception:
                return 0.0

        area, error = quad(
            integrand, theta_start, theta_end,
            epsabs=1e-8, epsrel=1e-8, limit=400
        )
        
        if error > 1e-6:
            logger.warning(f"High integration error in polar method: {error}")
        
        if np.isnan(area) or np.isinf(area):
            raise PolarIntegrationError(f"Integration resulted in {area}")
        
        return max(area, 0.0)
        
    except Exception as e:
        logger.error(f"Polar area calculation failed: {e}")
        raise PolarIntegrationError(f"Polar integration failed: {e}")


def _compute_single_area(expr, theta_var, theta_start, theta_end):
    """
    Simple area of a single polar curve over [theta_start, theta_end].
    """
    try:
        r_func = safe_lambdify(expr, theta_var)

        def integrand(theta):
            rv = safe_evaluate(r_func, theta, 0.0)
            result = 0.5 * (rv * rv)
            if np.isnan(result) or np.isinf(result):
                return 0.0
            return result

        area, error = quad(
            integrand, theta_start, theta_end, 
            epsabs=1e-8, epsrel=1e-8, limit=400
        )
        
        if error > 1e-6:
            logger.warning(f"High integration error in single area: {error}")
        
        if np.isnan(area) or np.isinf(area):
            raise PolarIntegrationError(f"Single area integration resulted in {area}")
        
        return max(area, 0.0)
        
    except Exception as e:
        logger.error(f"Single area calculation failed: {e}")
        raise PolarIntegrationError(f"Failed to compute single curve area: {e}")


def area_inside_outside(inner_expr, outer_expr, theta_var, 
                       theta_start=0.0, theta_end=2*np.pi, method='auto'):
    """
    Wrapper function for solve_polar with consistent API.
    
    Returns:
        float: The area value, or raises PolarIntegrationError
    """
    return solve_polar(inner_expr, outer_expr, theta_var, theta_start, theta_end, method)


if __name__ == "__main__":
    theta = sp.symbols('theta', real=True)
    
    try:
        result = solve_polar(sp.sin(2*theta), 0, theta)
        print(f"sin(2θ) vs 0 -> {result} (expected π/2 ≈ 1.571)")
    except PolarIntegrationError as e:
        print(f"Integration failed: {e}")
    except ValueError as e:
        print(f"Invalid input: {e}")