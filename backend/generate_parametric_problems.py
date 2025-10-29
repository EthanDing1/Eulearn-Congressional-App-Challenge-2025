import sqlite3
import random
from datetime import datetime
import sympy as sp
from sympy import symbols, integrate, latex, simplify, sin, cos, tan, exp, log, sqrt

t = symbols('t')

class ParametricIntegralGenerator:
    def __init__(self, db_name='practice_integrals.db'):
        self.db_name = db_name
        self.ensure_parametric_table()
        
    def ensure_parametric_table(self):
        """Create the parametric practice problems table if it doesn't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parametric_practice_problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                x_t_text TEXT NOT NULL,
                x_t_latex TEXT NOT NULL,
                y_t_text TEXT NOT NULL,
                y_t_latex TEXT NOT NULL,
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
        print(f"✅ Parametric table created/verified in {self.db_name}")
    
    def generate_difficulty_1(self, count=25):
        """Generate easiest parametric integrals - basic polynomials"""
        problems = []
        
        templates = [
            (t, t, "Both linear"),
            (t, t**2, "Linear and quadratic"),
            (t**2, t, "Quadratic and linear"),
            (2*t, 3*t, "Linear with coefficients"),
            (t, 2*t**2, "Linear and quadratic with coefficient"),
            (3*t, t, "Linear with coefficient"),
            (t**2, t**2, "Both quadratic"),
            (t, t**3, "Linear and cubic"),
            (t**3, t, "Cubic and linear"),
            (2*t**2, t, "Quadratic with coefficient and linear"),
        ]
        
        for _ in range(count):
            x_t, y_t, desc = random.choice(templates)
            
            if random.random() < 0.5:
                coeff = random.randint(2, 5)
                y_t = coeff * y_t
            
            x_prime = sp.diff(x_t, t)
            
            integrand = y_t * x_prime
            solution = integrate(integrand, t)
            
            hint = f"Calculate x'(t) = {x_prime}, then integrate y(t)·x'(t) = ({y_t})·({x_prime})"
            
            problems.append({
                'x_t': x_t,
                'y_t': y_t,
                'solution': solution,
                'difficulty': 1,
                'hint': hint
            })
        
        return problems
    
    def generate_difficulty_2(self, count=25):
        """Generate easy parametric integrals - basic trig and exponentials"""
        problems = []
        
        templates = [
            (sin(t), cos(t), "Trig: sin and cos"),
            (cos(t), sin(t), "Trig: cos and sin"),
            (t, sin(t), "Linear and sin"),
            (sin(t), t, "Sin and linear"),
            (t, cos(t), "Linear and cos"),
            (cos(t), t, "Cos and linear"),
            (t, exp(t), "Linear and exponential"),
            (exp(t), t, "Exponential and linear"),
            (t**2, exp(t), "Quadratic and exponential"),
            (exp(t), t**2, "Exponential and quadratic"),
        ]
        
        for _ in range(count):
            x_t, y_t, desc = random.choice(templates)
            
            x_prime = sp.diff(x_t, t)
            
            integrand = y_t * x_prime
            solution = integrate(integrand, t)
            
            hint = f"Calculate x'(t) = {x_prime}, then integrate y(t)·x'(t)"
            
            problems.append({
                'x_t': x_t,
                'y_t': y_t,
                'solution': solution,
                'difficulty': 2,
                'hint': hint
            })
        
        return problems
    
    def generate_difficulty_3(self, count=25):
        """Generate medium parametric integrals - products and compositions"""
        problems = []
        
        templates = [
            (t * sin(t), cos(t), "Product with trig"),
            (sin(t), t * cos(t), "Trig and product"),
            (t**2, sin(t) * cos(t), "Quadratic with trig product"),
            (exp(t), sin(t), "Exponential and trig"),
            (sin(t), exp(t), "Trig and exponential"),
            (t**3, t**2, "Cubic and quadratic"),
            (t**2, t**3, "Quadratic and cubic"),
            (t**4, t, "Fourth degree and linear"),
            (t * exp(t), t, "Product with exp and linear"),
            (t, t * exp(t), "Linear and product with exp"),
        ]
        
        for _ in range(count):
            x_t, y_t, desc = random.choice(templates)
            
            x_prime = sp.diff(x_t, t)
            
            integrand = y_t * x_prime
            solution = integrate(integrand, t)
            
            hint = f"Calculate x'(t) using product/chain rule, then integrate y(t)·x'(t)"
            
            problems.append({
                'x_t': x_t,
                'y_t': y_t,
                'solution': solution,
                'difficulty': 3,
                'hint': hint
            })
        
        return problems
    
    def generate_difficulty_4(self, count=25):
        """Generate hardest parametric integrals - complex compositions"""
        problems = []
        
        templates = [
            (sin(t)**2, cos(t), "Trig squared"),
            (cos(t), sin(t)**2, "Trig and trig squared"),
            (t * sin(t), t * cos(t), "Products with trig"),
            (exp(t) * sin(t), cos(t), "Exp-trig product"),
            (sin(t), exp(t) * cos(t), "Trig and exp-trig product"),
            (t**2 * exp(t), t, "Poly-exp product"),
            (t, t**2 * sin(t), "Linear and poly-trig product"),
            (exp(2*t), sin(t), "Exp with coefficient and trig"),
            (sin(2*t), cos(t), "Trig with coefficient"),
            (t * exp(t), sin(t), "Poly-exp and trig"),
        ]
        
        for _ in range(count):
            x_t, y_t, desc = random.choice(templates)
            
            x_prime = sp.diff(x_t, t)
            
            integrand = y_t * x_prime
            solution = integrate(integrand, t)
            
            hint = f"This requires careful application of product rule for x'(t), then integration"
            
            problems.append({
                'x_t': x_t,
                'y_t': y_t,
                'solution': solution,
                'difficulty': 4,
                'hint': hint
            })
        
        return problems
    
    def format_expression(self, expr):
        """Format expression for display"""
        expr_str = str(expr)
        expr_latex = f"$${latex(expr)}$$"
        return expr_str, expr_latex
    
    def format_solution(self, solution):
        """Format solution for display"""
        simplified = simplify(solution)
        solution_str = f"{simplified} + C"
        solution_latex = f"$${latex(simplified)} + C$$"
        return solution_str, solution_latex
    
    def generate_all_problems(self):
        """Generate all 100 parametric practice problems"""
        print("🔄 Generating parametric integral practice problems...")
        
        all_problems = []
        
        all_problems.extend(self.generate_difficulty_1(25))
        all_problems.extend(self.generate_difficulty_2(25))
        all_problems.extend(self.generate_difficulty_3(25))
        all_problems.extend(self.generate_difficulty_4(25))
        
        print(f"✅ Generated {len(all_problems)} parametric problems")
        return all_problems
    
    def save_problems_to_db(self, problems):
        """Save all problems to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM parametric_practice_problems')
        
        for i, problem in enumerate(problems, 1):
            x_t_str, x_t_latex = self.format_expression(problem['x_t'])
            y_t_str, y_t_latex = self.format_expression(problem['y_t'])
            solution_str, solution_latex = self.format_solution(problem['solution'])
            
            x_prime = sp.diff(problem['x_t'], t)
            steps = f"Step 1: Calculate x'(t) = {x_prime}\n"
            steps += f"Step 2: Form the integrand y(t)·x'(t) = ({problem['y_t']})·({x_prime})\n"
            steps += f"Step 3: Integrate with respect to t\n"
            steps += f"Step 4: Add constant of integration C"
            
            cursor.execute('''
                INSERT INTO parametric_practice_problems 
                (x_t_text, x_t_latex, y_t_text, y_t_latex, 
                 solution_text, solution_latex, difficulty, hint, steps)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                x_t_str, x_t_latex, y_t_str, y_t_latex,
                solution_str, solution_latex, problem['difficulty'], 
                problem['hint'], steps
            ))
            
            if i % 10 == 0:
                print(f"💾 Saved {i} parametric problems...")
        
        conn.commit()
        conn.close()
        print(f"✅ All {len(problems)} parametric problems saved to {self.db_name}")
    
    def display_sample_problems(self, count=5):
        """Display a few sample problems from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT x_t_text, y_t_text, solution_text, difficulty, hint
            FROM parametric_practice_problems 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (count,))
        
        problems = cursor.fetchall()
        conn.close()
        
        print(f"\n📚 Sample parametric problems from database:")
        print("=" * 80)
        
        for i, (x_t, y_t, solution, difficulty, hint) in enumerate(problems, 1):
            print(f"\nProblem {i}:")
            print(f"x(t) = {x_t}")
            print(f"y(t) = {y_t}")
            print(f"∫ y dx = ?")
            print(f"Solution: {solution}")
            print(f"Difficulty: {difficulty}/4")
            print(f"Hint: {hint}")
            print("-" * 40)

def main():
    """Main function to generate and save parametric problems"""
    try:
        generator = ParametricIntegralGenerator()
        problems = generator.generate_all_problems()
        generator.save_problems_to_db(problems)
        generator.display_sample_problems(10)
        
        print(f"\n🎉 Successfully generated 100 parametric integral practice problems!")
        print(f"📁 Database saved as: {generator.db_name}")
        
        conn = sqlite3.connect(generator.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM parametric_practice_problems')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Total parametric problems in database: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()