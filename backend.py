from flask_cors import CORS
from flask import Flask, request, jsonify
from sympy import symbols, Eq, solve, sin, cos, tan, sec, csc, cot, sqrt, N, pi, nsimplify, Rational, simplify, I
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor

app = Flask(__name__)
CORS(app)

x = symbols('x')
transformations = standard_transformations + (implicit_multiplication_application, convert_xor)

def preprocess_input(inp):
    inp = inp.replace('x²', 'x**2').replace('x³', 'x**3')
    inp = inp.replace('√(', 'sqrt(')
    inp = inp.replace('^', '**')
    return inp

def get_fraction(expr):
    try:
        rat = nsimplify(expr, rational=True)
        if rat.is_number and rat.is_rational:
            return str(Rational(rat).limit_denominator())
        return str(simplify(expr))
    except Exception:
        return str(expr)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    expr_input = data.get('expression', '')
    expr_input = preprocess_input(expr_input)
    local_dict = {
        'x': x, 'pi': pi, 'sqrt': sqrt, 'sin': sin, 'cos': cos, 'tan': tan,
        'sec': sec, 'csc': csc, 'cot': cot, 'I': I,
    }
    if expr_input.count('=') == 0:
        # Evaluation
        try:
            expr = parse_expr(expr_input, transformations=transformations, local_dict=local_dict)
            val = N(expr, 8)
            frac = get_fraction(expr)
            return jsonify({
                'result': f"{frac}\n≈ {val}" if frac != str(expr) else f"{val}",
                'solutions': []
            })
        except Exception as e:
            return jsonify({'error': str(e), 'result': '', 'solutions': []})
    else:
        try:
            left, right = expr_input.split('=', 1)
            left_expr = parse_expr(left, transformations=transformations, local_dict=local_dict)
            right_expr = parse_expr(right, transformations=transformations, local_dict=local_dict)
            eq = Eq(left_expr, right_expr)
            solutions = solve(eq, x)
            solution_arr = []
            for sol in solutions:
                frac_val = get_fraction(sol)
                try:
                    num_val = float(N(sol, 6).evalf())
                    num_str = f"{num_val:.6f}"
                except Exception:
                    num_str = str(N(sol, 6))
                # If answer is symbolic/contains pi
                if getattr(sol, "has", lambda *a: False)(pi):
                    deg_val = N(180*sol/pi, 6)
                    try:
                        deg_float = float(deg_val)
                        deg_str = f"{deg_float:.6f}"
                    except Exception:
                        deg_str = str(deg_val)
                    deg_frac = get_fraction(180*sol/pi)
                    solution_arr.append(f"{frac_val} rad ≈ {num_str} rad ≈ {deg_frac}° ≈ {deg_str}°")
                else:
                    solution_arr.append(f"{frac_val} ≈ {num_str}")
            return jsonify({'result': '', 'solutions': solution_arr})
        except Exception as e:
            return jsonify({'error': str(e), 'result': '', 'solutions': []})

if __name__ == '__main__':
    app.run(debug=True)
