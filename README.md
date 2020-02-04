# eva_gen

Mini language targeting EVA assembly.

## Structure

```
├── LICENSE
├── README.md
└── eva_gen                   ; Main package
    ├── common                ; Common package
    │   ├── __init__.py
    │   ├── ast               ; Ast manipulation sub package
    │   │   ├── __init__.py
    │   │   └── nodes.py
    │   ├── back_end          ; Code generation sub package
    │   │   └── __init__.py
    │   └── front_end         ; Lexing/Parsing sub package
    │       ├── __init__.py
    │       ├── lexer.py
    │       └── parser.py
    ├── debug.py              ; Executables
    └── test.py
```

