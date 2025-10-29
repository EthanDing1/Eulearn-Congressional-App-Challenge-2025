from sympy import (
    symbols, integrate, diff, simplify, Mul, fraction, Poly, Integral, solve,
    Add, Pow, Function, Number, Symbol, sympify, expand, factor, cancel,
    Integer, Rational
)
from sympy import sin, cos, tan, cot, sec, csc
from sympy import asin, acos, atan
from sympy import sinh, cosh, tanh
from sympy import exp, log, sqrt, pi, E, oo, Wild
from sympy.functions import erf, erfc, erfi, Ei, Si, Ci, Shi, Chi, fresnelc, fresnels, polylog
from sympy.parsing.sympy_parser import parse_expr
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
from sympy.core.traversal import preorder_traversal
import threading
import time
import traceback

s = "\\quad"

base_local_dict = {
    "sin": sin, "cos": cos, "tan": tan,
    "cot": cot, "sec": sec, "csc": csc,
    "asin": asin, "acos": acos, "atan": atan,
    "sinh": sinh, "cosh": cosh, "tanh": tanh,
    "exp": exp, "ln": log, "log": log,
    "sqrt": sqrt,
    "pi": pi, "e": E, "oo": oo
}

non_elem_funcs = (erf, erfc, erfi, Ei, Si, Ci, Shi, Chi, fresnelc, fresnels, polylog)

steps_log = []

def latex_format(expr):
    """Convert sympy expression to LaTeX format"""
    from sympy import latex
    try:
        return latex(expr)
    except:
        return str(expr)

def log_step(step):
    """Add a step to the global steps log with spacing"""
    global steps_log
    if not step.endswith(s):
        step = step + s
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
    if not hasattr(var, "is_Symbol"):
        var = symbols(str(var))
    return var

def safe_parse_expr(expr_str):
    """Safely parse an expression string with error handling"""
    try:
        expr_str = str(expr_str).strip()
        
        expr_str = expr_str.replace('^', '**')
        expr_str = expr_str.replace('âˆš', 'sqrt')
        
        transformations = (standard_transformations + (implicit_multiplication_application,))
        expr = parse_expr(expr_str, evaluate=False, 
                         local_dict=base_local_dict,
                         transformations=transformations)
        return expr, None
    except Exception as e:
        error_msg = f"Could not parse the expression. Please check your input format. Error: {str(e)}"
        return None, error_msg


def extract_inner_functions(expr, var):
    """Extract all possible inner functions for u-substitution"""
    candidates = []
    seen = set()
    
    def add_if_nontrivial(candidate):
        cand_str = str(candidate)
        if (candidate != var and candidate.has(var) and 
            not candidate.is_Number and cand_str not in seen):
            candidates.append(candidate)
            seen.add(cand_str)
    
    for atom in expr.atoms():
        if atom.is_Function and atom.has(var) and atom.args:
            add_if_nontrivial(atom.args[0])
    
    for atom in expr.atoms(Pow):
        if atom.has(var):
            add_if_nontrivial(atom)
            if atom.base.has(var) and atom.base != var:
                add_if_nontrivial(atom.base)
    
    num, denom = fraction(expr)
    if denom != 1 and denom.has(var):
        add_if_nontrivial(denom)
    
    for sub in preorder_traversal(expr):
        if sub.is_Pow and sub.exp == -1:
            if sub.base.has(var):
                add_if_nontrivial(sub.base)
        elif sub.is_Mul:
            _, d = fraction(sub)
            if d != 1 and d.has(var):
                add_if_nontrivial(d)
    
    for atom in expr.atoms(Add):
        if atom.has(var):
            try:
                deg = atom.as_poly(var).degree() if atom.is_polynomial(var) else -1
                if 1 <= deg <= 2:
                    add_if_nontrivial(atom)
            except:
                pass
    
    return candidates

def can_express_in_terms_of_u(expr, u_candidate, var):
    """Check if expression can be expressed in terms of u and du/dx"""
    try:
        du = diff(u_candidate, var)
        if du == 0:
            return False, None, None

        u_sym = symbols('u_temp', real=True)
        num, denom = fraction(expr)

        test_constants = [Integer(1), Integer(-1), Integer(2), Integer(-2),
                          Rational(1,2), Rational(-1,2)]

        if denom != 1 and denom.has(var):
            test_denom = denom.xreplace({u_candidate: u_sym})
            if not test_denom.has(var):
                for c in test_constants:
                    if simplify(num - c * du).equals(0):
                        du_term = c * du
                        expr_in_u_over_du = c / denom
                        return True, du_term, expr_in_u_over_du
                
                try:
                    ratio = cancel(num / du)
                    ratio_simplified = simplify(ratio)
                    if ratio_simplified.is_number:
                        du_term = ratio_simplified * du
                        expr_in_u_over_du = ratio_simplified / denom
                        return True, du_term, expr_in_u_over_du
                    from sympy import trigsimp
                    ratio_trig = trigsimp(ratio)
                    if ratio_trig.is_number:
                        du_term = ratio_trig * du
                        expr_in_u_over_du = ratio_trig / denom
                        return True, du_term, expr_in_u_over_du
                except:
                    pass

        test_expr = expr.xreplace({u_candidate: u_sym})
        remaining_var = test_expr.free_symbols.intersection({var})

        if not remaining_var:
            try:
                quotient = cancel(expr / du)
                test_quotient = quotient.xreplace({u_candidate: u_sym})
                if not test_quotient.has(var):
                    return True, du, quotient
            except Exception:
                pass

        for const in test_constants:
            try:
                quotient = cancel(expr / (const * du))
                test_quotient = quotient.xreplace({u_candidate: u_sym})
                if not test_quotient.has(var):
                    return True, const * du, quotient
            except Exception:
                pass

        if expr.is_Mul:
            factors = expr.as_ordered_factors()
            du_factors = []
            other_factors = []

            for factor in factors:
                try:
                    ratio = simplify(factor / du)
                    if ratio.is_number:
                        du_factors.append(factor)
                        continue
                except Exception:
                    pass

                if not factor.has(var):
                    other_factors.append(factor)
                else:
                    test_factor = factor.xreplace({u_candidate: u_sym})
                    if not test_factor.has(var):
                        other_factors.append(factor)
                    else:
                        return False, None, None

            if du_factors:
                du_part = Mul(*du_factors) if du_factors else Integer(1)
                other_part = Mul(*other_factors) if other_factors else Integer(1)
                test_other = other_part.xreplace({u_candidate: u_sym})
                if not test_other.has(var):
                    quotient = simplify(other_part / du_part)
                    return True, du_part, quotient

        return False, None, None

    except Exception:
        return False, None, None

def attempt_u_substitution(expr, u_candidate, var):
    """Attempt to perform u-substitution with given candidate"""
    can_substitute, du_term, expr_in_u_over_du = can_express_in_terms_of_u(expr, u_candidate, var)
    
    if not can_substitute:
        return False
    
    try:
        u_sym = symbols('u')
        du = diff(u_candidate, var)
        
        if expr_in_u_over_du is not None:
            integrand_u = expr_in_u_over_du.xreplace({u_candidate: u_sym})
        else:
            integrand_u = cancel(expand(expr) / expand(du))
            integrand_u = integrand_u.xreplace({u_candidate: u_sym})
        
        integrand_u = simplify(integrand_u)
        
        if var in integrand_u.free_symbols:
            try:
                test = simplify(integrand_u.subs(var, Integer(1)))
                if test != integrand_u:
                    return False
            except:
                return False
        
        log_step(f"\\text{{Identified u-substitution opportunity}}")
        log_step(f"\\text{{Let }} u = {latex_format(u_candidate)}")
        log_step(f"\\text{{Then }} du = {latex_format(du)} \\, d{latex_format(var)}")
        
        if du_term != du:
            factor = simplify(du_term / du)
            log_step(f"\\text{{Adjusting for factor: }} {latex_format(factor)}")
            integrand_u = simplify(integrand_u * factor)
            if var in integrand_u.free_symbols:
                return False
        
        log_step(f"\\text{{After substitution: }} \\int {latex_format(integrand_u)} \\, du")
        
        result_u = integrate(integrand_u, u_sym)
        
        if isinstance(result_u, Integral):
            return False
        
        result = result_u.xreplace({u_sym: u_candidate})
        result = simplify(result)
        
        log_step(f"\\text{{After integrating: }} {latex_format(result_u)}")
        log_step(f"\\text{{Substituting back }} u = {latex_format(u_candidate)}")
        log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
        
        return result
        
    except Exception as e:
        return False

def try_u_substitution(expr, var):
    """Main u-substitution handler with multiple strategies"""
    
    candidates = extract_inner_functions(expr, var)
    
    common_patterns = []
    
    for atom in expr.atoms():
        if atom.is_Add and atom.has(var):
            try:
                if atom.is_polynomial(var) and atom.as_poly(var).degree() == 1:
                    common_patterns.append(atom)
            except:
                pass
    
    for atom in expr.atoms():
        if atom.is_Add and atom.has(var):
            try:
                if atom.is_polynomial(var) and atom.as_poly(var).degree() == 2:
                    common_patterns.append(atom)
            except:
                pass
    
    for atom in expr.atoms():
        if atom.is_Pow and atom.base == var and atom.exp.is_number:
            common_patterns.append(atom)
    
    for pattern in common_patterns:
        if pattern not in candidates and pattern != var:
            candidates.append(pattern)
    
    candidates = candidates[:10]
    
    for u_candidate in candidates:
        result = attempt_u_substitution(expr, u_candidate, var)
        if result is not False:
            return result
    
    if expr.is_Function and expr.has(var) and expr.args:
        result = attempt_u_substitution(expr, expr.args[0], var)
        if result is not False:
            return result
    
    num, denom = fraction(expr)
    if denom != 1 and denom.has(var):
        result = attempt_u_substitution(expr, denom, var)
        if result is not False:
            return result
    
    sqrt_atoms = [atom for atom in expr.atoms() if atom.is_Pow and atom.exp == Rational(1,2)]
    for sqrt_atom in sqrt_atoms[:3]:
        base = sqrt_atom.base
        if base.has(var) and base != var:
            result = attempt_u_substitution(expr, base, var)
            if result is not False:
                return result
    
    return False


def check_sin_cos_exp(expr, var):
    expr = simplify(expr)
    
    has_sin_or_cos = expr.has(sin) or expr.has(cos)
    has_exp = expr.has(exp)
    
    if not (has_sin_or_cos and has_exp):
        return False
    
    C = Wild('C')
    a = Wild('a')
    
    pattern_sin = C*sin(a*var)*exp(a*var)
    match = expr.match(pattern_sin)
    if match and match[C] != 0 and match[a] != 0:
        return ('s', match[a], match[C])
    
    pattern_cos = C*cos(a*var)*exp(a*var)  
    match = expr.match(pattern_cos)
    if match and match[C] != 0 and match[a] != 0:
        return ('c', match[a], match[C])
    
    if expr.is_Mul:
        factors = expr.as_ordered_factors()
        sin_factor = None
        cos_factor = None
        exp_factor = None
        coeff = 1
        
        for factor in factors:
            if factor.has(sin):
                sin_factor = factor
            elif factor.has(cos):
                cos_factor = factor  
            elif factor.has(exp):
                exp_factor = factor
            elif factor.is_number:
                coeff *= factor
        
        if sin_factor and exp_factor:
            sin_arg = sin_factor.args[0] if sin_factor.func == sin else None
            if exp_factor.func == exp:
                exp_arg = exp_factor.args[0]
                if sin_arg == var and exp_arg == var:
                    return ('s', 1, coeff)
                elif sin_arg == var and exp_arg.is_Mul and exp_arg.has(var):
                    exp_coeff = exp_arg.coeff(var)
                    if exp_coeff:
                        return ('s', exp_coeff, coeff)
        
        if cos_factor and exp_factor:
            cos_arg = cos_factor.args[0] if cos_factor.func == cos else None  
            if exp_factor.func == exp:
                exp_arg = exp_factor.args[0]
                if cos_arg == var and exp_arg == var:
                    return ('c', 1, coeff)
                elif cos_arg == var and exp_arg.is_Mul and exp_arg.has(var):
                    exp_coeff = exp_arg.coeff(var)
                    if exp_coeff:
                        return ('c', exp_coeff, coeff)
    
    return False

def special_integral(expr, var):
    log_step(r"\text{Identified special integral of the form } \sin(" + latex_format(var) + r")e^{a" + latex_format(var) + r"} \text{ or } \cos(" + latex_format(var) + r")e^{a" + latex_format(var) + r"}")
    log_step(r"\text{These integrals require integration by parts applied twice}")
    
    info = check_sin_cos_exp(expr, var)
    if not info:
        result = integrate(expr, var)
        log_step(f"\\text{{Final result: }} \\boxed{{{latex_format(result)} + C}}")
        return result
    
    c_or_s, a_val, C_val = info
    log_step(r"\text{Applying integration by parts twice and solving for the integral}")
    
    result = integrate(expr, var)
    log_step(f"\\text{{The answer is }} \\boxed{{{latex_format(result)} + C}}")
    log_step(r"\text{Check out the special integrals section on the techniques page for more details!}")
    return result

def is_elementary_integrable(expr, var):
    if expr.has(*non_elem_funcs):
        return False
    
    try:
        result = integrate(expr, var, conds='none')
        if result.has(*non_elem_funcs):
            return False
        if any(isinstance(atom, Integral) for atom in result.atoms(Integral)):
            return False
        return True
    except Exception:
        return True

def is_generalized_polynomial(expr, var):
    if expr.is_Atom:
        return expr.is_Number or expr == var
    if expr.is_Pow:
        base, expn = expr.args
        return base == var and expn.is_number
    if expr.is_Mul:
        return all(is_generalized_polynomial(f, var) for f in expr.args)
    if expr.is_Add:
        return all(is_generalized_polynomial(f, var) for f in expr.args)
    return False

def basic(expr, var):
    if is_generalized_polynomial(expr, var):
        log_step(r"\text{Identified polynomial expression}")
        log_step(r"\text{Apply power rule for integration: } \int " + latex_format(var) + r"^n \, d" + latex_format(var) + r" = \frac{" + latex_format(var) + r"^{n+1}}{n+1} + C")
        result = integrate(expr, var)
        log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
        return result
    
    funcs = [sin, cos, tan, sec, csc, cot,
             sinh, cosh, tanh,
             asin, acos, atan,
             exp, log, sqrt]
    basic_exprs = [f(var) for f in funcs]
    basic_derivatives = [diff(f(var), var) for f in funcs]
    known_exprs = basic_exprs + basic_derivatives
    simplified_expr = simplify(expr)
    
    if any(simplified_expr.equals(e) for e in known_exprs):
        log_step(r"\text{Identified basic function with known antiderivative}")
        result = integrate(expr, var)
        log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
        return result
    
    if expr.is_Mul:
        coeff, rest = expr.as_coeff_Mul()
        if coeff.is_number and any(simplify(rest - e).equals(0) for e in known_exprs):
            log_step(f"\\text{{Identified basic function with constant coefficient }} {latex_format(coeff)}")
            result = integrate(expr, var)
            log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
            return result
    
    if expr.is_polynomial(var):
        log_step(r"\text{Identified polynomial expression}")
        log_step(r"\text{Apply power rule for integration}")
        result = integrate(expr, var)
        log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
        return result
    return False

def liate_priority(expr, var):
    s = str(expr)
    if "log" in s or "ln" in s:
        return 0
    for inv_trig in ["asin", "acos", "atan", "arcsin", "arccos", "arctan"]:
        if inv_trig in s:
            return 1
    if (expr.is_polynomial(var) or expr == var) and not expr.is_Number:
        return 2
    for trig in ["sin", "cos", "tan", "cot", "sec", "csc"]:
        if trig in s:
            return 3
    if expr.func.__name__ == "exp":
        return 4
    if expr.is_Pow and expr.base.is_number and expr.exp == var:
        return 4
    return 5

def ibp(expr, var):
    unsorted_terms = expr.as_ordered_factors()
    sorted_terms = sorted(unsorted_terms, key=lambda e: liate_priority(e, var))
    if len(sorted_terms) >= 2:
        u = sorted_terms[0]
        dv = Mul(*sorted_terms[1:])
    else:
        return False
    
    v = integrate(dv, var)
    if v is None or isinstance(v, Integral):
        return False
    if u == 1:
        return False
    
    log_step(r"\text{Using integration by parts: } \int u \, dv = uv - \int v \, du")
    log_step(f"\\text{{Let }} u = {latex_format(u)}, \\, dv = {latex_format(dv)} \\, d{latex_format(var)}")
    du = diff(u, var)
    log_step(f"\\text{{Then }} du = {latex_format(du)} \\, d{latex_format(var)}, \\, v = {latex_format(v)}")
    log_step(f"\\int {latex_format(expr)} \\, d{latex_format(var)} = {latex_format(u)} \\cdot {latex_format(v)} - \\int {latex_format(v)} \\cdot {latex_format(du)} \\, d{latex_format(var)}")
    
    res = u*v - solve_integral_internal(v*du, var)
    if isinstance(res, Integral) or res == Integral(expr, var):
        return False
    result = simplify(res)
    log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
    return result

def is_rational_function(expr, var):
    num, denom = fraction(expr)
    return num.is_polynomial(var) and denom.is_polynomial(var)

def check_trig_sub(expr, var):
    squared = simplify(expr**2)
    if is_rational_function(squared, var) and not is_rational_function(expr, var):
        log_step(r"\text{Identified expression suitable for trigonometric substitution}")
        result = integrate(expr, var)
        log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
        return result
    return False

def get_pfd_coeffs(expr, var):
    from sympy import apart
    
    log_step(r"\text{Using partial fraction decomposition}")
    log_step(r"\text{Decomposing rational function into simpler fractions}")
    
    try:
        pfd = apart(expr, var)
        log_step(f"\\text{{Partial fraction decomposition: }} {latex_format(expr)} = {latex_format(pfd)}")
    except Exception:
        log_step(f"\\text{{Computing partial fractions for: }} {latex_format(expr)}")
    
    result = integrate(expr, var)
    log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
    return result

def solve_integral_internal(expr, var):
    """Internal solver that doesn't clear steps or handle the main parsing"""
    try:
        if check_sin_cos_exp(expr, var):
            return special_integral(expr, var)
        
        basic_result = basic(expr, var)
        if basic_result is not False:
            return basic_result
        
        u_sub_result = try_u_substitution(expr, var)
        if u_sub_result is not False:
            return u_sub_result
        
        trig_sub = check_trig_sub(expr, var)
        if trig_sub is not False:
            return trig_sub
        
        if is_rational_function(expr, var):
            pfd_result = get_pfd_coeffs(expr, var)
            if pfd_result is not None:
                return pfd_result
        
        ibp_result = ibp(expr, var)
        if ibp_result is not False:
            return ibp_result
        
        log_step(r"\text{Using direct integration}")
        result = integrate(expr, var)
        log_step(f"\\text{{Final result: }} \\boxed{{{latex_format(result)} + C}}")
        return result
        
    except Exception as e:
        try:
            log_step(r"\text{Using direct integration method}")
            result = integrate(expr, var)
            log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
            return result
        except:
            raise

def solve_integral(expr_str, var_str='x'):
    """Main function that returns (solution, steps) tuple with comprehensive error handling"""
    clear_steps()
    
    if not expr_str or expr_str.strip() == '':
        return "Error: Empty input. Please enter an expression to integrate.", []
    
    try:
        var = ensure_symbol(var_str)
    except Exception as e:
        return f"Error: Invalid variable '{var_str}'. Please use a valid variable name.", []
    
    result_container = [None]
    exception_container = [None]
    
    def solve_with_timeout():
        try:
            if not hasattr(expr_str, "is_Atom"):
                expr, error = safe_parse_expr(expr_str)
                if error:
                    exception_container[0] = Exception(error)
                    return
            else:
                expr = expr_str
            
            log_step(f"\\text{{Integrating: }} \\int {latex_format(expr)} \\, d{latex_format(var)}")
            
            try:
                expr = simplify(expr)
                log_step(f"\\text{{Simplified to: }} {latex_format(expr)}")
            except Exception:
                pass
            
            if not is_elementary_integrable(expr, var):
                log_step(r"\text{This integral does not have an elementary solution}")
                log_step(r"\text{It may involve special functions like error functions or exponential integrals}")
                result = integrate(expr, var)
                log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
                result_container[0] = (str(result), get_steps())
                return
            
            if expr.is_Add:
                log_step(r"\text{Breaking down sum into individual terms}")
                results = []
                for term in expr.args:
                    term_result = solve_integral_internal(term, var)
                    results.append(term_result)
                result = sum(results)
                log_step(f"\\text{{Combining results: }} \\boxed{{{latex_format(result)} + C}}")
                result_container[0] = (str(result), get_steps())
                return
            
            result = solve_integral_internal(expr, var)
            result_container[0] = (str(result), get_steps())
            
        except Exception as e:
            exception_container[0] = e
    
    solver_thread = threading.Thread(target=solve_with_timeout)
    solver_thread.daemon = True
    solver_thread.start()
    solver_thread.join(timeout=60)
    
    if solver_thread.is_alive():
        log_step(r"\text{Integration exceeded time limit, using direct method}")
        try:
            expr, error = safe_parse_expr(expr_str) if not hasattr(expr_str, "is_Atom") else (expr_str, None)
            if error:
                return f"Error: {error}", []
            
            result = integrate(expr, var)
            log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
            return str(result), get_steps()
        except Exception as e:
            error_msg = "The integral is too complex to solve within the time limit. "
            error_msg += "This might be a non-elementary integral or require special techniques."
            log_step(f"\\text{{{error_msg}}}")
            return f"Error: {error_msg}", get_steps()
    
    if exception_container[0] is not None:
        e = exception_container[0]
        error_type = type(e).__name__
        error_str = str(e)
        
        if "could not parse" in error_str.lower() or "parse" in error_type.lower():
            log_step(r"\text{Error: Could not parse the expression}")
            log_step(r"\text{Please check:}")
            log_step(r"\text{Use * for multiplication (e.g., 2*x instead of 2x)}")
            log_step(r"\text{Use ** or ^ for exponents (e.g., x**2 or x^2)}")
            log_step(r"\text{Check parentheses are balanced}")
            log_step(r"\text{Use standard function names (sin, cos, log, exp, sqrt)}")
            return "Error: Could not parse expression. Please check the format.", get_steps()
        
        elif "sympy" in error_str.lower() or "attribute" in error_str.lower():
            try:
                log_step(r"\text{Attempting alternative method...}")
                expr, parse_error = safe_parse_expr(expr_str) if not hasattr(expr_str, "is_Atom") else (expr_str, None)
                if parse_error:
                    return f"Error: {parse_error}", get_steps()
                
                result = integrate(expr, var)
                log_step(f"\\text{{Result: }} \\boxed{{{latex_format(result)} + C}}")
                return str(result), get_steps()
            except Exception as e2:
                log_step(f"\\text{{Integration failed: The expression may be too complex or contain unsupported functions}}")
                return "Error: Cannot solve this integral. The expression may contain unsupported operations.", get_steps()
        
        else:
            try:
                log_step(r"\text{Primary method failed, attempting direct integration...}")
                expr, parse_error = safe_parse_expr(expr_str) if not hasattr(expr_str, "is_Atom") else (expr_str, None)
                if parse_error:
                    return f"Error: {parse_error}", get_steps()
                
                result = integrate(expr, var)
                log_step(f"\\text{{Final result: }} \\boxed{{{latex_format(result)} + C}}")
                return str(result), get_steps()
            except Exception as e2:
                log_step(r"\text{Unable to solve this integral}")
                error_msg = "Cannot solve this integral. "
                
                if "log(0)" in str(e2) or "division by zero" in str(e2).lower():
                    error_msg += "The integral may have singularities or undefined points."
                elif "factorial" in str(e2).lower():
                    error_msg += "The expression may involve factorial or gamma functions that cannot be integrated."
                else:
                    error_msg += "It may be non-elementary or require advanced techniques beyond this solver's capabilities."
                
                log_step(f"\\text{{{error_msg}}}")
                return f"Error: {error_msg}", get_steps()
    
    if result_container[0]:
        return result_container[0]
    else:
        return "Error: Unexpected error occurred. Please try again.", get_steps()