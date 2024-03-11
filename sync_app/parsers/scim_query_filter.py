"""
Rules from https://datatracker.ietf.org/doc/html/rfc7644
ABNF rules from RFC5234
"""

from abnf.parser import Rule as _Rule
from abnf.parser import Rule as _Rule
from abnf.grammars.misc import load_grammar_rulelist
from abnf.grammars import rfc3986, rfc5234


@load_grammar_rulelist(
    [
        ("URI", rfc3986.Rule("URI")),
        ("ALPHA", rfc5234.Rule("ALPHA")),
        ("SP", rfc5234.Rule("SP")),
        ("DIGIT", rfc5234.Rule("DIGIT")),
    ]
)
class Rule(_Rule):
    grammar = r"""
filter = infixLogicalExpression / expression

expression = precedenceGroup / attributeGroup / prefixLogicalExpression / postfixAssertion / infixAssertion

precedenceGroup = "(" [SP] filter [SP] ")"

attributeGroup = attributePath "[" filter "]"

prefixLogicalExpression = prefixLogicalExpressionOperator [SP] precedenceGroup
prefixLogicalExpressionOperator = "not"

infixLogicalExpression = expression 1*infixLogicalExpressionPredicate
infixLogicalExpressionPredicate = (SP infixLogicalExpressionOperator SP expression)
infixLogicalExpressionOperator = "and" / "or"

postfixAssertion = attributePath SP postfixAssertionOperator
postfixAssertionOperator = "pr"

infixAssertion = attributePath SP infixAssertionOperator SP infixAssertionValue
infixAssertionOperator = "eq" / "ne" / "co" / "sw" / "ew" / "gt" / "lt" / "ge" / "le"
infixAssertionValue = null / true / false / number / string

attributePath = [URI ":"] attributePathSegment *("." attributePathSegment)
attributePathSegment  = ALPHA *("-" / "_" / DIGIT / ALPHA)

; rfc7159
false         = %x66.61.6c.73.65               ; false
null          = %x6e.75.6c.6c                  ; null
true          = %x74.72.75.65                  ; true
number        = [ minus ] int [ frac ] [ exp ]
decimal-point = %x2E                           ; .
digit1-9      = %x31-39                        ; 1-9
e             = %x65 / %x45                    ; e E
exp           = e [ minus / plus ] 1*DIGIT
frac          = decimal-point 1*DIGIT
int           = zero / ( digit1-9 *DIGIT )
minus         = %x2D                           ; -
plus          = %x2B                           ; +
zero          = %x30                           ; 0
string = quotation-mark *char quotation-mark
char = unescaped /
    escape (
        %x22 /          ; "    quotation mark  U+0022
        %x5C /          ; \    reverse solidus U+005C
        %x2F /          ; /    solidus         U+002F
        %x62 /          ; b    backspace       U+0008
        %x66 /          ; f    form feed       U+000C
        %x6E /          ; n    line feed       U+000A
        %x72 /          ; r    carriage return U+000D
        %x74 /          ; t    tab             U+0009
        %x75 4HEXDIG )  ; uXXXX                U+XXXX

escape = %x5C              ; \
quotation-mark = %x22      ; "
unescaped = %x20-21 / %x23-5B / %x5D-10FFFF
    """
