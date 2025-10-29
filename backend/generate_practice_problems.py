import sqlite3
import random
import math
from datetime import datetime
import sympy as sp
from sympy import symbols, integrate, latex, simplify, expand, sin, cos, tan, exp, log, sqrt, atan, asin

x = symbols('x')

class IntegralGenerator:
    def __init__(self, db_name='practice_integrals.db'):
        self.db_name = db_name
        self.create_database()
        
    def create_database(self):
        """Create the practice problems database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS practice_problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_text TEXT NOT NULL,
                problem_latex TEXT NOT NULL,
                solution_text TEXT NOT NULL,
                solution_latex TEXT NOT NULL,
                technique TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                hint TEXT,
                steps TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database {self.db_name} created successfully!")
    
    def generate_basic_polynomials(self, count=15):
        """Generate basic polynomial integrals"""
        problems = []
        
        for _ in range(count):
            degree = random.randint(1, 6)
            coeff = random.randint(1, 10)
            
            if degree == 1:
                expr = coeff * x
                technique = "Power Rule"
                difficulty = 1
                hint = "Use the power rule: ∫x^n dx = x^(n+1)/(n+1) + C"
            else:
                expr = coeff * x**degree
                technique = "Power Rule"
                difficulty = 1
                hint = f"Use the power rule: ∫x^{degree} dx = x^{degree+1}/{degree+1} + C"
            
            solution = integrate(expr, x)
            
            problems.append({
                'expr': expr,
                'solution': solution,
                'technique': technique,
                'difficulty': difficulty,
                'hint': hint
            })
        
        return problems
    
    def generate_basic_trigonometric(self, count=10):
        """Generate basic trigonometric integrals"""
        problems = []
        trig_funcs = [
            (sin(x), "Basic Trigonometric", 2, "∫sin(x) dx = -cos(x) + C"),
            (cos(x), "Basic Trigonometric", 2, "∫cos(x) dx = sin(x) + C"),
            (tan(x), "Basic Trigonometric", 3, "∫tan(x) dx = -ln|cos(x)| + C"),
            (1/cos(x)**2, "Basic Trigonometric", 2, "∫sec²(x) dx = tan(x) + C"),
            (1/sin(x)**2, "Basic Trigonometric", 3, "∫csc²(x) dx = -cot(x) + C"),
        ]
        
        for _ in range(count):
            func, technique, difficulty, hint = random.choice(trig_funcs)
            coeff = random.randint(1, 5)
            expr = coeff * func
            solution = integrate(expr, x)
            
            problems.append({
                'expr': expr,
                'solution': solution,
                'technique': technique,
                'difficulty': difficulty,
                'hint': hint
            })
        
        return problems
    
    
    def generate_exponential_logarithmic(self, count=10):
        """Generate exponential and logarithmic integrals"""
        problems = []
        
        for _ in range(count):
            choice = random.randint(1, 4)
            
            if choice == 1:
                coeff = random.randint(1, 5)
                expr = coeff * exp(x)
                technique = "Exponential"
                difficulty = 2
                hint = "∫e^x dx = e^x + C"
            
            elif choice == 2:
                a = random.randint(2, 5)
                expr = exp(a * x)
                technique = "Exponential with Chain Rule"
                difficulty = 3
                hint = f"∫e^({a}x) dx = (1/{a})e^({a}x) + C"
            
            elif choice == 3:
                expr = 1/x
                technique = "Logarithmic"
                difficulty = 2
                hint = "∫(1/x) dx = ln|x| + C"
            
            else:
                a = random.randint(2, 5)
                expr = a**x
                technique = "Exponential Base a"
                difficulty = 3
                hint = f"∫{a}^x dx = {a}^x/ln({a}) + C"
            
            solution = integrate(expr, x)
            
            problems.append({
                'expr': expr,
                'solution': solution,
                'technique': technique,
                'difficulty': difficulty,
                'hint': hint
            })
        
        return problems
    
    def generate_substitution_problems(self, count=20):
        """Generate u-substitution problems"""
        problems = []
        
        substitution_templates = [
            (2*x * exp(x**2), "u-substitution", 4, "Let u = x², then du = 2x dx"),
            (x * sin(x**2), "u-substitution", 4, "Let u = x², then du = 2x dx"),
            (x * cos(x**2), "u-substitution", 4, "Let u = x², then du = 2x dx"),
            ((2*x + 1) * (x**2 + x)**3, "u-substitution", 4, "Let u = x² + x, then du = (2x + 1) dx"),
            (sin(x) * cos(x), "u-substitution", 4, "Let u = sin(x), then du = cos(x) dx"),
            (tan(x), "u-substitution", 4, "Rewrite as sin(x)/cos(x), let u = cos(x)"),
            (x / sqrt(x**2 + 1), "u-substitution", 4, "Let u = x² + 1, then du = 2x dx"),
            (exp(x) / (exp(x) + 1), "u-substitution", 4, "Let u = e^x + 1, then du = e^x dx"),
        ]
        
        for _ in range(count):
            template = random.choice(substitution_templates)
            expr, technique, difficulty, hint = template
            
            if random.random() < 0.5:
                coeff = random.randint(2, 5)
                expr = coeff * expr
            
            solution = integrate(expr, x)
            
            problems.append({
                'expr': expr,
                'solution': solution,
                'technique': technique,
                'difficulty': difficulty,
                'hint': hint
            })
        
        return problems
    
    def generate_integration_by_parts(self, count=15):
        """Generate integration by parts problems"""
        problems = []
        
        ibp_templates = [
            (x * exp(x), "Integration by Parts", 5, "Let u = x, dv = e^x dx"),
            (x * sin(x), "Integration by Parts", 5, "Let u = x, dv = sin(x) dx"),
            (x * cos(x), "Integration by Parts", 5, "Let u = x, dv = cos(x) dx"),
            (x * log(x), "Integration by Parts", 5, "Let u = ln(x), dv = x dx"),
            (x**2 * exp(x), "Integration by Parts", 6, "Let u = x², dv = e^x dx (may need to apply twice)"),
            (exp(x) * sin(x), "Integration by Parts", 6, "Let u = e^x, dv = sin(x) dx (cyclic method)"),
            (exp(x) * cos(x), "Integration by Parts", 6, "Let u = e^x, dv = cos(x) dx (cyclic method)"),
            (log(x), "Integration by Parts", 5, "Let u = ln(x), dv = dx"),
            (x * atan(x), "Integration by Parts", 6, "Let u = arctan(x), dv = x dx"),
            (x * asin(x), "Integration by Parts", 6, "Let u = arcsin(x), dv = x dx"),
        ]
        
        for _ in range(count):
            template = random.choice(ibp_templates)
            expr, technique, difficulty, hint = template
            
            solution = integrate(expr, x)
            
            problems.append({
                'expr': expr,
                'solution': solution,
                'technique': technique,
                'difficulty': difficulty,
                'hint': hint
            })
        
        return problems
    
    def generate_rational_functions(self, count=15):
        """Generate rational function integrals (partial fractions)"""
        problems = []
        
        rational_templates = [
            (1/(x + 1), "Basic Rational", 3, "Direct integration: ∫1/(x+a) dx = ln|x+a| + C"),
            (1/(x**2 + 1), "Rational/Inverse Trig", 4, "∫1/(x²+1) dx = arctan(x) + C"),
            (1/(x**2 - 1), "Partial Fractions", 5, "Factor denominator and use partial fractions"),
            (1/(x*(x + 1)), "Partial Fractions", 5, "Use partial fractions: A/x + B/(x+1)"),
            (x/(x**2 + 1), "Rational with u-sub", 4, "Let u = x² + 1, then du = 2x dx"),
            ((x + 1)/(x**2 + 1), "Split Rational", 4, "Split into x/(x²+1) + 1/(x²+1)"),
            (1/(x**2 + 4), "Rational/Inverse Trig", 4, "Factor out constant: ∫1/(4(1 + x²/4)) dx"),
            (1/((x + 1)*(x + 2)), "Partial Fractions", 5, "Use partial fractions: A/(x+1) + B/(x+2)"),
        ]
        
        for _ in range(count):
            template = random.choice(rational_templates)
            expr, technique, difficulty, hint = template
            
            if random.random() < 0.3:
                coeff = random.randint(2, 4)
                expr = coeff * expr
            
            solution = integrate(expr, x)
            
            problems.append({
                'expr': expr,
                'solution': solution,
                'technique': technique,
                'difficulty': difficulty,
                'hint': hint
            })
        
        return problems
    
    def generate_advanced_problems(self, count=15):
        """Generate more advanced integration problems"""
        problems = []
        
        advanced_templates = [
            (sqrt(x**2 + 1), "Trigonometric Substitution", 7, "Use x = tan(θ) substitution"),
            (sqrt(1 - x**2), "Trigonometric Substitution", 7, "Use x = sin(θ) substitution"),
            (1/sqrt(x**2 + 1), "Inverse Hyperbolic", 6, "∫1/√(x²+1) dx = sinh⁻¹(x) + C = ln(x + √(x²+1)) + C"),
            (1/sqrt(1 - x**2), "Inverse Trig", 5, "∫1/√(1-x²) dx = arcsin(x) + C"),
            (x * sqrt(x + 1), "Substitution", 5, "Let u = x + 1, then x = u - 1"),
            (sin(x)**2, "Trigonometric Identity", 5, "Use identity: sin²(x) = (1 - cos(2x))/2"),
            (cos(x)**2, "Trigonometric Identity", 5, "Use identity: cos²(x) = (1 + cos(2x))/2"),
            (sin(x)**3, "Trigonometric", 6, "Use sin²(x) = 1 - cos²(x) and substitute"),
            (cos(x)**3, "Trigonometric", 6, "Use cos²(x) = 1 - sin²(x) and substitute"),
            (1/(1 + x**2)**2, "Advanced Rational", 6, "Use reduction formula or trigonometric substitution"),
        ]
        
        for _ in range(count):
            template = random.choice(advanced_templates)
            expr, technique, difficulty, hint = template
            
            solution = integrate(expr, x)
            
            problems.append({
                'expr': expr,
                'solution': solution,
                'technique': technique,
                'difficulty': difficulty,
                'hint': hint
            })
        
        return problems
    
    def format_expression(self, expr):
        """Format expression for display"""
        expr_str = str(expr)
        expr_latex = f"$$\\int {latex(expr)} \\, dx$$"
        return expr_str, expr_latex
    
    def format_solution(self, solution):
        """Format solution for display"""
        simplified = simplify(solution)
        solution_str = f"{simplified} + C"
        solution_latex = f"$${latex(simplified)} + C$$"
        return solution_str, solution_latex
    
    def generate_all_problems(self):
        """Generate all 100 practice problems"""
        print("🔄 Generating integral practice problems...")
        
        all_problems = []
        
        all_problems.extend(self.generate_basic_polynomials(15))
        all_problems.extend(self.generate_basic_trigonometric(10))
        all_problems.extend(self.generate_exponential_logarithmic(10))
        all_problems.extend(self.generate_substitution_problems(20))
        all_problems.extend(self.generate_integration_by_parts(15))
        all_problems.extend(self.generate_rational_functions(15))
        all_problems.extend(self.generate_advanced_problems(15))
        
        print(f"✅ Generated {len(all_problems)} problems")
        return all_problems
    
    def map_difficulty_to_four_levels(self, original_difficulty):
        """Map original difficulty (1-7) to new scale (1-4)"""
        if original_difficulty in [1, 2]:
            return 1
        elif original_difficulty in [3, 4]:
            return 2
        elif original_difficulty in [5, 6]:
            return 3
        else:
            return 4
        
    def save_problems_to_db(self, problems):
        """Save all problems to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM practice_problems')
        
        for i, problem in enumerate(problems, 1):
            expr_str, expr_latex = self.format_expression(problem['expr'])
            solution_str, solution_latex = self.format_solution(problem['solution'])
            
            steps = f"Step 1: Identify the integration technique ({problem['technique']})\n"
            steps += f"Step 2: Apply the technique\n"
            steps += f"Step 3: Simplify and add constant of integration"
            
            cursor.execute('''
                INSERT INTO practice_problems 
                (problem_text, problem_latex, solution_text, solution_latex, 
                 technique, difficulty, hint, steps)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                expr_str, expr_latex, solution_str, solution_latex,
                problem['technique'], self.map_difficulty_to_four_levels(problem['difficulty']), 
                problem['hint'], steps
            ))
            
            if i % 10 == 0:
                print(f"💾 Saved {i} problems...")
        
        conn.commit()
        conn.close()
        print(f"✅ All {len(problems)} problems saved to {self.db_name}")
    
    def display_sample_problems(self, count=5):
        """Display a few sample problems from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT problem_text, solution_text, technique, difficulty, hint
            FROM practice_problems 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (count,))
        
        problems = cursor.fetchall()
        conn.close()
        
        print(f"\n📚 Sample problems from database:")
        print("=" * 80)
        
        for i, (problem, solution, technique, difficulty, hint) in enumerate(problems, 1):
            print(f"\nProblem {i}:")
            print(f"∫ {problem} dx")
            print(f"Solution: {solution}")
            print(f"Technique: {technique} (Difficulty: {difficulty}/7)")
            print(f"Hint: {hint}")
            print("-" * 40) 

def main():
    """Main function to generate and save problems"""
    try:
        generator = IntegralGenerator()
        
        problems = generator.generate_all_problems()
        
        generator.save_problems_to_db(problems)
        
        generator.display_sample_problems(10)
        
        print(f"\n🎉 Successfully generated 100 integral practice problems!")
        print(f"📁 Database saved as: {generator.db_name}")
        print("\nYou can now use this database in your Flask application.")
        
        conn = sqlite3.connect(generator.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM practice_problems')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Total problems in database: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()