# CASE++ COMPILER - version 1.0 : Intermediate Code

## SYSTEM REQUIREMENTS
- Python 3+

## INSTALLATION
To install the necessary library for colored output:
```
> python3 -m pip install colorama
```

## USAGE
```
[NIX]
> ./casepp.py <filename>.c++ [options]

[WINDOWS]
> python3 casepp.py <filename>.c++ [options]

Options:
    --print-tokens          Display identifying tokens before syntax check
    --no-color              Disable colored output
```
***Note:*** *If colorama is not installed, the program defaults to no-color mode
      automatically*

## TECHNICAL SPECIFICATIONS
- **Integers:** 16-bit signed range (-32767 to 32767)
- **Identifier Limit:** 30 characters (longer names are automatically trimmed)
- **Nested Functions:** Supports unlimited depth
- **Nested Comments:** Not allowed and will be treated as syntax error
- **Error Handling:** Typo-prediction and visual '^' pointer
- **Output:** Compiler creates a .int file in current directory, containing the intermediate code

## DEVELOPERS INFO
***Developed by:*** 	
- BASIOS GEORGIOS
- PAPPAS VIKTOR
