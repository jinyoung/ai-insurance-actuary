import math

class MCPCalculator:
    def evaluate(self, formula_ast, context=None):
        """
        Evaluates a formula AST with the given context (variable values).
        AST structure matches the PRD: {"lhs": "P", "rhs": ["I/N"], ...}
        
        This is a simplified Python evaluator. Real MCP would be a server.
        """
        if context is None:
            context = {}

        # Simplified: assume 'rhs' contains a string expression like "I/N"
        # We will use python's eval() with safety precautions for this MVP demo
        # In production, use a proper math parser library.
        
        expression = formula_ast.get("rhs", [None])[0]
        if not expression:
            return {"error": "No RHS expression found"}

        try:
            # Safe eval context
            allowed_names = {k: v for k, v in context.items()}
            allowed_names.update({"__builtins__": None, "math": math})
            
            result = eval(expression, allowed_names)
            return {
                "formula": expression,
                "context": context,
                "result": result
            }
        except Exception as e:
            return {"error": str(e)}

# Tool wrapper
def evaluate_formula_tool(formula_str: str, variables: dict):
    """
    Evaluates a mathematical formula given a dictionary of variables.
    """
    calc = MCPCalculator()
    # meaningful wrap for the tool
    ast = {"rhs": [formula_str]}
    return calc.evaluate(ast, variables)

