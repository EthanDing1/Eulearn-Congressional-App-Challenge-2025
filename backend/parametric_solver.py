import sympy as sp
from sympy import diff, Symbol
from sympy.parsing.sympy_parser import parse_expr
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.integral_solver import solve_integral

base_local_dict = {
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
    'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
    'exp': sp.exp, 'ln': sp.log, 'log': sp.log,
    'sqrt': sp.sqrt, 'pi': sp.pi, 'e': sp.E,
    'abs': sp.Abs, 'floor': sp.floor, 'ceiling': sp.ceiling,
    'sec': sp.sec, 'csc': sp.csc, 'cot': sp.cot
}

s = "\\quad"

steps_log = []

def latex_format(expr):
    """Convert sympy expression to LaTeX format"""
    try:
        return sp.latex(expr)
    except Exception:
        return str(expr)

def wrap_latex(step: str, block: bool = True) -> str:
    """
    Wrap a step in $$ ... $$ for block LaTeX rendering, unless it's already wrapped.
    If step already appears to contain TeX delimiters, leave it alone.
    """
    if step is None:
        return ""
    stripped = step.strip()
    if (stripped.startswith("$$") and stripped.endswith("$$")) or \
       (stripped.startswith("$") and stripped.endswith("$")):
        return step
    if block:
        return "$$ " + step + " $$"
    else:
        return "$ " + step + " $"

def log_step(step, is_math=False, block_math=True):
    """Add a step to the global steps log. If is_math True, wrap for LaTeX rendering."""
    global steps_log
    if is_math:
        steps_log.append(wrap_latex(step, block=block_math))
    else:
        if any(tok in step for tok in ["\\int", "\\frac", "\\sqrt", "\\cdot", "_", "^", "\\("]):
            steps_log.append(wrap_latex(step, block=block_math))
        else:
            steps_log.append(step)

def clear_steps():
    """Clear the global steps log"""
    global steps_log
    steps_log = []

def get_steps():
    """Get the current steps log"""
    global steps_log
    return steps_log.copy()

def ensure_symbol(var):
    """Ensure var is a Symbol object"""
    if isinstance(var, str):
        return Symbol(var)
    return var

def solve_parametric(xt, yt, var):
    """
    Solve parametric curve integration: ∫ y dx = ∫ y(t) * x'(t) dt
    Uses the main solve_integral function for detailed integration steps
    """
    clear_steps()
    
    var = ensure_symbol(var)
    local_dict = dict(base_local_dict)
    local_dict[str(var)] = var
    
    try:
        expr_x = parse_expr(xt, evaluate=False, local_dict=local_dict)
        expr_y = parse_expr(yt, evaluate=False, local_dict=local_dict)

        log_step(r"\text{Solving parametric curve integration:}"+s, is_math=True)
        log_step(f"x({latex_format(var)}) = {latex_format(expr_x)}"+s, is_math=True)
        log_step(f"y({latex_format(var)}) = {latex_format(expr_y)}"+s, is_math=True)
        
        dx_dt = diff(expr_x, var)
        log_step(r"\text{For parametric integration: } \int y \, dx = \int y(t) \cdot \frac{dx}{dt} \, dt", is_math=True)
        log_step(s, is_math=True)
        log_step(f"\\frac{{dx}}{{d{latex_format(var)}}} = \\frac{{d}}{{d{latex_format(var)}}}\\left[{latex_format(expr_x)}\\right] = {latex_format(dx_dt)}", is_math=True)
        log_step(s, is_math=True)

        integrand = sp.simplify(expr_y * dx_dt)
        log_step(f"\\text{{Set up the integral: }} \\int y \\frac{{dx}}{{d{latex_format(var)}}} \\, d{latex_format(var)} = "
                 f"\\int {latex_format(expr_y)} \\cdot {latex_format(dx_dt)} \\, d{latex_format(var)}", is_math=True)

        log_step(f"\\text{{Simplify the integrand: }} {latex_format(expr_y)} \\cdot {latex_format(dx_dt)} = {latex_format(integrand)}"+s, is_math=True)

        parametric_steps = get_steps().copy()
        
        integrand_str = str(integrand)
        res = solve_integral(integrand_str, str(var))
        
        if isinstance(res, tuple) and len(res) == 2:
            result_str, solver_steps = res
        else:
            result_str = str(res)
            solver_steps = []

        clear_steps()
        for step in parametric_steps:
            log_step(step)
        for step in solver_steps:
            log_step(step)

        return result_str, get_steps()
        
    except Exception as e:
        error_msg = f"Error: Unable to solve parametric integral. Details: {str(e)}"
        log_step(error_msg)
        return error_msg, get_steps()