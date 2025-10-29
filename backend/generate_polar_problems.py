import sqlite3
import random
from datetime import datetime
import sympy as sp
from sympy import symbols, integrate, latex, simplify, sin, cos, exp, pi, sqrt, solve
import time

theta = symbols('theta', real=True)

class PolarIntegralGenerator:
    def __init__(self, db_name='practice_integrals.db'):
        self.db_name = db_name
        self.intersection_count = 0
        self.ensure_polar_table()

    def find_intersections(self, inner, outer, lower, upper):
        """Find intersection points between inner and outer curves in [lower, upper]"""
        try:
            equation = inner**2 - outer**2
            solutions = solve(equation, theta)
            
            valid_intersections = []
            for sol in solutions:
                try:
                    val = complex(sol.evalf())
                    if abs(val.imag) < 1e-6:
                        real_val = float(val.real)
                        if lower <= real_val <= upper:
                            valid_intersections.append(real_val)
                except:
                    continue
            
            return sorted(set(valid_intersections))
        except:
            return []

    def is_valid_problem(self, inner, outer, lower, upper):
        """Check if one curve is consistently >= the other in [lower, upper]"""
        try:
            test_points = [lower + i * (upper - lower) / 30 for i in range(31)]
            
            mid_point = (lower + upper) / 2
            inner_mid = abs(float(inner.subs(theta, mid_point)))
            outer_mid = abs(float(outer.subs(theta, mid_point)))
            
            if inner_mid > outer_mid + 1e-6:
                inner, outer = outer, inner
            
            for t in test_points:
                inner_val = abs(float(inner.subs(theta, t)))
                outer_val = abs(float(outer.subs(theta, t)))
                if outer_val < inner_val - 1e-6:
                    return False
            return True
        except:
            return False
    
    def generate_valid_problem(self, templates, difficulty, lower_bound=0, upper_bound=None):
        """Generate a valid problem with proper bounds checking"""
        if upper_bound is None:
            upper_bound = 2 * float(pi)
        
        max_attempts = 50
        for attempt in range(max_attempts):
            if attempt % 10 == 0 and attempt > 0:
                print(f"   Attempt {attempt}/{max_attempts} for difficulty {difficulty}...")
            
            inner, outer, desc = random.choice(templates)
            
            current_upper = upper_bound
            current_lower = lower_bound
            
            if "3 petals" in desc or "5 petals" in desc:
                current_upper = float(pi)
            
            use_intersections = False
            if difficulty == 3:
                use_intersections = random.random() < 0.7
            elif difficulty == 4:
                use_intersections = random.random() < 0.9

            if use_intersections:
                intersections = self.find_intersections(inner, outer, current_lower, current_upper)
                if len(intersections) >= 2:
                    idx = random.randint(0, len(intersections) - 2)
                    current_lower = intersections[idx]
                    current_upper = intersections[idx + 1]
                    use_intersections = True
                else:
                    use_intersections = False
            
            if not self.is_valid_problem(inner, outer, current_lower, current_upper):
                continue
            
            try:
                integrand = (outer**2 - inner**2) / 2
                definite_integral = integrate(integrand, (theta, current_lower, current_upper))
                solution = simplify(definite_integral)
                
                numerical_value = float(solution.evalf())
                if numerical_value <= 0 or abs(numerical_value) > 1000:
                    continue
                
                hint = f"Calculate (1/2)∫ (r_outer² - r_inner²) dθ. Remember to square both functions first."
                if use_intersections and current_lower != lower_bound:
                    self.intersection_count += 1
                    hint = f"Find intersection points to determine integration bounds, then calculate (1/2)∫ (r_outer² - r_inner²) dθ."
                
                return {
                    'inner': inner,
                    'outer': outer,
                    'lower_bound': current_lower,
                    'upper_bound': current_upper,
                    'solution': solution,
                    'difficulty': difficulty,
                    'hint': hint
                }
            except Exception as e:
                continue
        
        print(f"⚠️  Using fallback problem for difficulty {difficulty}")
        fallback_templates = [
            (1 + cos(theta), 2 + cos(theta)),
            (1 + sin(theta), 2 + sin(theta)),
            (1 + cos(theta), 3 + cos(theta)),
            (2 + cos(theta), 3 + cos(theta)),
        ]
        inner, outer = random.choice(fallback_templates)
        
        fallback_upper = 2 * float(pi)
        integrand = (outer**2 - inner**2) / 2
        definite_integral = integrate(integrand, (theta, lower_bound, fallback_upper))
        solution = simplify(definite_integral)

        return {
            'inner': inner,
            'outer': outer,
            'lower_bound': lower_bound,
            'upper_bound': fallback_upper,
            'solution': solution,
            'difficulty': difficulty,
            'hint': f"Calculate (1/2)∫ (r_outer² - r_inner²) dθ"
        }    
    
    def ensure_polar_table(self):
        """Create the polar practice problems table if it doesn't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS polar_practice_problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inner_function_text TEXT NOT NULL,
                inner_function_latex TEXT NOT NULL,
                outer_function_text TEXT NOT NULL,
                outer_function_latex TEXT NOT NULL,
                lower_bound REAL NOT NULL,
                upper_bound REAL NOT NULL,
                solution_text TEXT NOT NULL,
                solution_latex TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                hint TEXT,
                steps TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Polar table created/verified in {self.db_name}")
    
    def generate_difficulty_1(self, count=25):
        """Generate easiest polar integrals - phase-shifted curves"""
        problems = []
        print(f"🔄 Generating {count} difficulty 1 problems...")
        
        templates = [
            (1 + cos(theta), 2 + sin(theta), "Phase-shifted cardioids"),
            (1 + sin(theta), 2 + cos(theta), "Phase-shifted cardioids"),
            (1.5 + cos(theta), 2 + sin(theta), "Asymmetric phase shift"),
            (1.5 + sin(theta), 2 + cos(theta), "Asymmetric phase shift"),
            (1 + 0.8*cos(theta), 1.5 + 0.8*sin(theta), "Small phase shift"),
            (1 + 0.8*sin(theta), 1.5 + 0.8*cos(theta), "Small phase shift"),
            (1 + 0.5*cos(2*theta), 1.8 + 0.3*cos(theta), "Frequency mix low amp"),
            (1 + 0.5*sin(2*theta), 1.8 + 0.3*sin(theta), "Frequency mix low amp"),
            (1.2 + 0.4*cos(2*theta), 1.8 + 0.2*cos(theta), "Subtle frequency mix"),
            (1.2 + 0.4*sin(2*theta), 1.8 + 0.2*sin(theta), "Subtle frequency mix"),
        ]
        
        for i in range(count):
            if i % 5 == 0:
                print(f"   Generated {i}/{count}...")
            problem = self.generate_valid_problem(templates, 1)
            problems.append(problem)
        
        print(f"✅ Completed difficulty 1")
        return problems

    def generate_difficulty_2(self, count=25):
        """Generate easy polar integrals - using old difficulty 4 templates"""
        problems = []
        print(f"🔄 Generating {count} difficulty 2 problems...")
        
        templates = [
            (1.2 + cos(theta), 2.2 + sin(theta), "Strong phase shift"),
            (1.2 + sin(theta), 2.2 + cos(theta), "Strong phase shift"),
            (1.5 + cos(theta), 2.5 + sin(theta), "Large phase shift"),
            (1.5 + sin(theta), 2.5 + cos(theta), "Large phase shift"),
            (1 + 0.9*cos(theta), 1.6 + 0.9*sin(theta), "High amplitude phase"),
            (1 + 0.9*sin(theta), 1.6 + 0.9*cos(theta), "High amplitude phase"),
            (1.2 + 0.4*cos(2*theta), 1.9 + 0.3*cos(theta), "Safe frequency mix"),
            (1.2 + 0.4*sin(2*theta), 1.9 + 0.3*sin(theta), "Safe frequency mix"),
            (1.3 + 0.5*cos(2*theta), 2 + 0.2*sin(theta), "Mixed freq and phase"),
            (1.3 + 0.5*sin(2*theta), 2 + 0.2*cos(theta), "Mixed freq and phase"),
        ]
        
        for i in range(count):
            if i % 5 == 0:
                print(f"   Generated {i}/{count}...")
            problem = self.generate_valid_problem(templates, 2)
            problems.append(problem)
        
        print(f"✅ Completed difficulty 2")
        return problems

    def generate_difficulty_3(self, count=25):
        """Generate medium polar integrals - specific intersection problems"""
        problems = []
        print(f"🔄 Loading difficulty 3 problems...")
        
        known_problems = [
            (1 + cos(theta), 1 + 2*cos(theta), 0.187322, "Cardioid variations"),
            (2 + sin(2*theta), cos(theta), 13.351769, "Rose and circle"),
            (2*cos(2*theta), sp.sympify('1'), 3.826446, "Four-petal rose and circle"),
            (1 - cos(theta), 2 + cos(theta), 2.0545602, "Inverted cardioid pair"),
            (2 + 2*cos(theta), 2*cos(theta), 15.707963, "Cardioid and circle"),
            (sin(3*theta), cos(2*theta), 0.320592, "Three-petal and four-petal roses"),
            (2*sin(theta), 1 - sin(theta), 2.972502, "Circle and limacon"),
            (sqrt(cos(2*theta)), sp.Rational(1, 2), 0.638717, "Lemniscate and circle"),
            (2*cos(3*theta), 1 + cos(theta), 1.830232, "Six-petal rose and cardioid"),
            (3*sin(2*theta), 2 + cos(theta), 5.399537, "Large rose and limacon"),
            (4*cos(theta), theta, 2.288096, "Circle and spiral"),
            (1 + sin(theta), 2*cos(2*theta), 1.935856, "Cardioid and rose"),
            (sp.sympify('2'), 3 + 2*sin(theta), 2.196, "Circle and limacon"),
            (3 + 2*sin(theta), sp.sympify('2'), 24.287, "Limacon and circle"),
            (3 + 3*sin(theta), sp.sympify('2'), 33.7074, "Cardioid and circle"),
            (sp.sympify('2'), 3 + 3*sin(theta), 3.8622, "Circle and cardioid"),
            (4 - 2*cos(theta), 6 + 2*cos(theta), 13.6971, "Two limacons"),
            (3*sin(theta), 2 - sin(theta), 5.196, "Circle and limacon"),
            (sp.sympify('4'), 2 + 2*cos(theta), 31.416, "Circle and cardioid"),
            (4*cos(2*theta), sp.sympify('2'), 15.306, "Four-petal rose and circle"),
            (3*sin(theta), 1 + sin(theta), 3.142, "Circle and cardioid"),
            (1 + sin(theta), 1 - sin(theta), 4.000, "Two cardioids"),
            (sp.sympify('2'), 3 + 3*sin(theta), 33.7074, "Circle and cardioid"),
            (3 + 3*sin(theta), sp.sympify('2'), 3.8622, "Cardioid and circle"),
            (6 + 2*cos(theta), 4 - 2*cos(theta), 13.6971, "Two limacons"),
        ]
        
        for i in range(count):
            problem_data = known_problems[i % len(known_problems)]
            inner, outer, known_area, desc = problem_data
            
            current_lower = 0
            current_upper = 2 * float(pi)
            
            hint = f"Find intersection points to determine integration bounds, then calculate (1/2)∫ (r_outer² - r_inner²) dθ."
            
            problems.append({
                'inner': inner,
                'outer': outer,
                'lower_bound': current_lower,
                'upper_bound': current_upper,
                'solution': known_area,
                'difficulty': 3,
                'hint': hint
            })
        
        print(f"✅ Loaded difficulty 3 ({len(problems)} problems)")
        return problems

    def generate_difficulty_4(self, count=25):
        """Generate hardest polar integrals - complex combinations with known answers"""
        problems = []
        print(f"🔄 Loading difficulty 4 problems...")
        
        known_problems = [
            (1 + 2*sin(theta), 3 + cos(theta), 21.350159, "Complex limacon pair"),
            (2*cos(theta), 1 + sin(theta), 3.52437, "Circle and cardioid"),
            (1 + cos(2*theta), 2*sin(theta), 2.453101, "Rose and circle"),
            (1 + cos(theta), 3*sin(theta), 5.547137, "Cardioid and circle"),
            (1 + sin(theta), 2 - cos(theta), 10.068583, "Cardioid and limacon"),
            (sin(4*theta), cos(3*theta), 0.319469, "Four-petal and three-petal roses"),
            (1 - cos(theta), sp.sympify('1'), 1.2146, "Cardioid and circle"),
            (1 + 2*sin(theta), 2 + cos(theta), 8.995182, "Complex limacon pair"),
            (cos(5*theta), sin(2*theta), 1.103809, "Five-petal and four-petal roses"),
            (1 + sin(theta), 3*cos(2*theta), 10.586401, "Cardioid and rose"),
            (2*sin(3*theta), 1 + cos(2*theta), 3.271097, "Three-petal rose and rose"),
            (3*sin(3*theta), 1 + cos(theta), 2.934053, "Three-petal rose and cardioid"),
            (1 + 2*cos(theta), 2 - 2*sin(theta), 14.277261, "Two cardioids"),
            (2 - cos(2*theta), 4*sin(theta), 5.693601, "Rose and circle"),
            (cos(3*theta), 1 + sin(2*theta), 4.196987, "Three-petal rose and rose"),
            (1 + sin(theta), 3*sin(theta), 3.14159, "Cardioid and circle"),
            (sp.sympify('1'), 2*sin(theta), 1.91322, "Circle and circle"),
            (1 + cos(theta), 3*cos(theta), 3.14159, "Cardioid and circle"),
            (1 + cos(3*theta), sin(2*theta), 0.537466, "Three-petal rose and four-petal rose"),
            (3*sin(theta), 2*cos(3*theta), 2.001981, "Circle and six-petal rose"),
            (1 + sin(3*theta), 2 + cos(3*theta), 10.068583, "Three-petal variations"),
            (sp.Rational(1, 2), cos(theta), 0.478, "Circle and circle"),
            (1 + cos(theta), 2*sin(2*theta), 3.373539, "Cardioid and rose"),
            (sp.Rational(1, 2), cos(4*theta), 0.956611, "Circle and eight-petal rose"),
            (3 - sin(theta), 1 + 2*cos(theta), 0.386291, "Limacon pair"),
        ]
        
        for i in range(count):
            problem_data = known_problems[i % len(known_problems)]
            inner, outer, known_area, desc = problem_data
            
            current_lower = 0
            current_upper = 2 * float(pi)
            
            hint = f"Find intersection points to determine integration bounds, then calculate (1/2)∫ (r_outer² - r_inner²) dθ. This is a challenging problem with complex curves."
            
            problems.append({
                'inner': inner,
                'outer': outer,
                'lower_bound': current_lower,
                'upper_bound': current_upper,
                'solution': known_area,
                'difficulty': 4,
                'hint': hint
            })
        
        print(f"✅ Loaded difficulty 4 ({len(problems)} problems)")
        return problems
    
    def format_expression(self, expr):
        """Format expression for display"""
        expr_str = str(expr).replace('theta', 'θ')
        expr_latex = f"$${latex(expr)}$$"
        return expr_str, expr_latex
    
    def format_solution(self, solution):
        """Format solution for display (no +C for definite integrals)"""
        simplified = simplify(solution)
        
        try:
            numerical_value = float(simplified.evalf())
            rounded_value = round(numerical_value, 3)
            solution_str = str(rounded_value)
            solution_latex = str(rounded_value)
        except:
            solution_str = str(simplified)
            solution_latex = latex(simplified)
        
        return solution_str, solution_latex
    
    def generate_all_problems(self):
        """Generate all 100 polar practice problems"""
        print("\n" + "="*80)
        print("🔄 Starting polar area practice problem generation...")
        print("="*80 + "\n")
        start_time = time.time()
        
        all_problems = []
        
        all_problems.extend(self.generate_difficulty_1(25))
        all_problems.extend(self.generate_difficulty_2(25))
        all_problems.extend(self.generate_difficulty_3(25))
        all_problems.extend(self.generate_difficulty_4(25))
        
        elapsed = time.time() - start_time
        print(f"\n✅ Generated {len(all_problems)} polar problems in {elapsed:.1f} seconds")
        print(f"🎯 Problems with intersection-based bounds: {self.intersection_count}")
        return all_problems
    
    def save_problems_to_db(self, problems):
        """Save all problems to the database"""
        print(f"\n💾 Saving problems to database...")
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM polar_practice_problems')
        
        for i, problem in enumerate(problems, 1):
            inner_str, inner_latex = self.format_expression(problem['inner'])
            outer_str, outer_latex = self.format_expression(problem['outer'])
            solution_str, solution_latex = self.format_solution(problem['solution'])
            
            lower_display, upper_display = self.format_bounds_for_display(
                problem['lower_bound'], 
                problem['upper_bound']
            )
            
            steps = f"Step 1: Identify inner function r₁ = {inner_str} and outer function r₂ = {outer_str}\n"
            if problem['difficulty'] >= 3 and abs(problem['lower_bound']) > 0.01:
                steps += f"Step 2: Find intersection points by solving r₁ = r₂\n"
                steps += f"Step 3: Set up integral: A = (1/2)∫[{lower_display},{upper_display}] (r₂² - r₁²) dθ\n"
                steps += f"Step 4: Expand (r₂² - r₁²) and simplify\n"
                steps += f"Step 5: Integrate with respect to θ\n"
                steps += f"Step 6: Evaluate at bounds and simplify"
            else:
                steps += f"Step 2: Set up integral: A = (1/2)∫[{lower_display},{upper_display}] (r₂² - r₁²) dθ\n"
                steps += f"Step 3: Expand (r₂² - r₁²) and simplify\n"
                steps += f"Step 4: Integrate with respect to θ\n"
                steps += f"Step 5: Evaluate at bounds and simplify"
            
            cursor.execute('''
                INSERT INTO polar_practice_problems 
                (inner_function_text, inner_function_latex, outer_function_text, outer_function_latex,
                lower_bound, upper_bound, solution_text, solution_latex, difficulty, hint, steps)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                inner_str, inner_latex, outer_str, outer_latex,
                problem['lower_bound'], problem['upper_bound'],
                solution_str, solution_latex, problem['difficulty'], 
                problem['hint'], steps
            ))
            
            if i % 25 == 0:
                print(f"   Saved {i}/{len(problems)} problems...")
        
        conn.commit()
        conn.close()
        print(f"✅ All {len(problems)} polar problems saved to {self.db_name}")
    
    def display_sample_problems(self, count=5):
        """Display a few sample problems from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT inner_function_text, outer_function_text, lower_bound, upper_bound,
                   solution_text, difficulty, hint
            FROM polar_practice_problems 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (count,))
        
        problems = cursor.fetchall()
        conn.close()
        
        print(f"\n📚 Sample polar problems from database:")
        print("=" * 80)
        
        for i, (inner, outer, lower, upper, solution, difficulty, hint) in enumerate(problems, 1):
            lower_disp, upper_disp = self.format_bounds_for_display(lower, upper)
            print(f"\nProblem {i}:")
            print(f"Inner function: r₁ = {inner}")
            print(f"Outer function: r₂ = {outer}")
            print(f"Bounds: θ ∈ [{lower_disp}, {upper_disp}]")
            print(f"Find the area of the region")
            print(f"Solution: {solution}")
            print(f"Difficulty: {difficulty}/4")
            print(f"Hint: {hint}")
            print("-" * 40)

    def format_bounds_for_display(self, lower_bound, upper_bound):
        """Format bounds in terms of π for better readability"""
        import math
        
        def format_single_bound(bound):
            if abs(bound) < 1e-9:
                return "0"
            
            pi_multiple = bound / math.pi
            tolerance = 1e-6
            
            if abs(pi_multiple - round(pi_multiple)) < tolerance:
                multiple = int(round(pi_multiple))
                if multiple == 1:
                    return "π"
                elif multiple == -1:
                    return "-π"
                else:
                    return f"{multiple}π"
            
            half_multiple = pi_multiple * 2
            if abs(half_multiple - round(half_multiple)) < tolerance:
                numerator = int(round(half_multiple))
                if numerator == 1:
                    return "π/2"
                elif numerator == -1:
                    return "-π/2"
                else:
                    return f"{numerator}π/2"
            
            third_multiple = pi_multiple * 3
            if abs(third_multiple - round(third_multiple)) < tolerance:
                numerator = int(round(third_multiple))
                if numerator == 1:
                    return "π/3"
                elif numerator == -1:
                    return "-π/3"
                else:
                    return f"{numerator}π/3"
            
            fourth_multiple = pi_multiple * 4
            if abs(fourth_multiple - round(fourth_multiple)) < tolerance:
                numerator = int(round(fourth_multiple))
                if numerator == 1:
                    return "π/4"
                elif numerator == -1:
                    return "-π/4"
                else:
                    return f"{numerator}π/4"
            
            return f"{bound:.4f}"
        
        lower_str = format_single_bound(lower_bound)
        upper_str = format_single_bound(upper_bound)
        
        return lower_str, upper_str        

def main():
    """Main function to generate and save polar problems"""
    try:
        generator = PolarIntegralGenerator()
        problems = generator.generate_all_problems()
        generator.save_problems_to_db(problems)
        generator.display_sample_problems(10)
        
        print(f"\n" + "="*80)
        print(f"🎉 Successfully generated 100 polar area practice problems!")
        print(f"📁 Database saved as: {generator.db_name}")
        
        conn = sqlite3.connect(generator.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM polar_practice_problems')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Total polar problems in database: {count}")
        print(f"🎯 Problems using intersection bounds: {generator.intersection_count}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()