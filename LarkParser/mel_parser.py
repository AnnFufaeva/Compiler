from collections.abc import Iterable
from contextlib import suppress

from lark import Lark, Transformer
from lark.lexer import Token

from .mel_ast import *

parser = Lark('''
    %import common.NUMBER
    %import common.ESCAPED_STRING
    %import common.CNAME
    %import common.NEWLINE
    %import common.WS

    %ignore WS

    COMMENT: "/*" /(.|\\n|\\r)+/ "*/"
        |  "//" /(.)+/ NEWLINE
    %ignore COMMENT

    num: NUMBER  -> literal
    str: ESCAPED_STRING  -> literal
    ident: CNAME
    type_: CNAME 
        |  CNAME "[" num "]" 

    ADD:     "+"
    SUB:     "-"
    MUL:     "*"
    DIV:     "/"
    AND:     "&&"
    OR:      "||"
    BIT_AND: "&"
    BIT_OR:  "|"
    GE:      ">="
    LE:      "<="
    NEQUALS: "!="
    EQUALS:  "=="
    GT:      ">"
    LT:      "<"

    call: ident "(" ( expr ( "," expr )* )? ")"

    ?group: num | str
        | call
        | ident 
        | "(" expr ")"
        | arr
        | array_element

    ?mult: group
        | mult ( MUL | DIV ) group  -> bin_op

    ?add: mult
        | add ( ADD | SUB ) mult  -> bin_op

    ?compare1: add
        | compare1 ( GT | LT | GE | LE ) add  -> bin_op

    ?compare2: compare1
        | compare2 ( EQUALS | NEQUALS ) compare1  -> bin_op

    ?logical_and: compare2
        | logical_and AND compare2  -> bin_op

    ?logical_or: logical_and
        | logical_or OR logical_and  -> bin_op

    ?expr: logical_or
    

    ?var_decl_inner: ident
        | ident "=" expr  -> assign
        

        

    vars: type_ var_decl_inner ( "," var_decl_inner )*


    arr : "[" expr ("," expr)* "]" -> arr

    ?simple_stmt: ident "=" arr -> array_update
        |ident "=" expr  -> assign
        | call
        | array_element "=" expr -> array_set_element 

    array_element: ident "[" num "]" -> array_get_element
    
    ?for_stmt_list: vars
        | ( simple_stmt ( "," simple_stmt )* )?  -> stmt_list
    ?cond: expr
        |   -> stmt_list
    ?body: stmt
        | ";"  -> stmt_list

    param: type_ ident
    func_vars: (param ( "," param )* )?
    func_decl: type_ ident "(" func_vars ")" "{" stmt_list? "}" ";" -> func
    
    ?stmt:  "if" "(" expr ")" stmt ("else" stmt)?  -> if
    | "for" "(" for_stmt_list ";" cond ";" for_stmt_list ")" body  -> for
    | "while" "(" cond ")" body -> while
    | "return" expr ";" -> return
    | vars ";"
    | simple_stmt ";"
    | "{" stmt_list "}"
    | func_decl
    
    stmt_list: ( stmt ";"* )*
    
    ?prog: stmt_list

    ?start: prog
''', start='start')  # , parser='lalr')


class MelASTBuilder(Transformer):
    def _call_userfunc(self, tree, new_children=None):
        # Assumes tree is already transformed
        children = new_children if new_children is not None else tree.children
        try:
            f = getattr(self, tree.data)
        except AttributeError:
            return self.__default__(tree.data, children, tree.meta)
        else:
            return f(*children)

    def __getattr__(self, item):
        if isinstance(item, str) and item.upper() == item:
            return lambda x: x

        if item in ('bin_op',):
            def get_bin_op_node(*args):
                op = BinOp(args[1].value)
                return BinOpNode(op, args[0], args[2],
                                 **{'token': args[1], 'line': args[1].line, 'column': args[1].column})

            return get_bin_op_node

        if item in ('stmt_list',):
            def get_node(*args):
                return StmtListNode(*sum(([*n] if isinstance(n, Iterable) else [n] for n in args), []))

            return get_node

        else:
            def get_node(*args):
                props = {}
                if len(args) == 1 and isinstance(args[0], Token):
                    props['token'] = args[0]
                    props['line'] = args[0].line
                    props['column'] = args[0].column
                    args = [args[0].value]
                with suppress(NameError):
                    cls = eval(''.join(x.capitalize() for x in item.split('_')) + 'Node')
                    return cls(*args, **props)
                return args

            return get_node


def parse(prog: str) -> StmtListNode:
    prog = parser.parse(str(prog))
    #print(prog.pretty('  '))
    prog = MelASTBuilder().transform(prog)
    return prog
