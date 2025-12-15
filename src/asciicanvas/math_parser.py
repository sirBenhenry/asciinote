import re
from typing import List, Tuple, Union

# A very simple recursive descent parser for basic math expressions.
# This is not a full-fledged math parser, but it can handle simple cases.

class ASTNode:
    pass

class Number(ASTNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Number({self.value})"

class Fraction(ASTNode):
    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator
    def __repr__(self):
        return f"Fraction({self.numerator}, {self.denominator})"

class Exponent(ASTNode):
    def __init__(self, base, power):
        self.base = base
        self.power = power
    def __repr__(self):
        return f"Exponent({self.base}, {self.power})"

class Root(ASTNode):
    def __init__(self, content):
        self.content = content
    def __repr__(self):
        return f"Root({self.content})"

def parse_math(expression: str) -> Union[ASTNode, None]:
    """
    Parses a math expression and returns an AST.
    This is a very simplified parser.
    """
    expression = expression.strip()

    # Fraction
    match = re.fullmatch(r"(.+)/(.+)", expression)
    if match:
        num = parse_math(match.group(1))
        den = parse_math(match.group(2))
        if num and den:
            return Fraction(num, den)

    # Exponent
    match = re.fullmatch(r"(.+)\^(.+)", expression)
    if match:
        base = parse_math(match.group(1))
        power = parse_math(match.group(2))
        if base and power:
            return Exponent(base, power)

    # Root
    match = re.fullmatch(r"r/(.+)", expression)
    if match:
        content = parse_math(match.group(1))
        if content:
            return Root(content)

    # Number (or variable)
    if re.fullmatch(r"[\w\d]+", expression):
        return Number(expression)
    
    # Parentheses (for grouping, not fully implemented)
    if expression.startswith('(') and expression.endswith(')'):
        return parse_math(expression[1:-1])

    return Number(expression) # Fallback for complex content
