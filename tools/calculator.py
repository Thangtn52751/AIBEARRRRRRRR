import math

ALLOWED_NAMES = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "pow": pow,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def calculate(expression: str):
    """
    Evaluate a math expression safely
    """

    try:
        result = eval(
            expression,
            {"__builtins__": {}},
            ALLOWED_NAMES
        )
        return str(result)

    except Exception as e:
        return f"Calculation error: {e}"