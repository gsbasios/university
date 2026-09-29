program	            :   'program' ID programblock
                    ;

programblock        :   '{' declarations functions statements_sequence '}'
                    ;

statements_sequence :   statement ( ';' statement )*
                    |	ε
                    ;

declarations	    :   ( 'declare' varlist ';')*
                    ;

varlist             :   ID ( ',' ID )*
                    |	ε
                    ;

functions           :   ( function )*
                    ;

function            :   'function' ID formalpars
                            programblock
                    ;

formalpars	        : 	'(' formalparlist ')'
                    ;

formalparlist	    :   formalparitem  ( ',' formalparitem )*
                    |	ε
                    ;

formalparitem	    : 	'in' ID | 'inout' ID
                    ;

statements	        :   statement
                    |   '{' statements_sequence '}'
                    ;

statement           :   assignment_stat
			        |   if_stat
      			    |   while_stat
      		        |   switchcase_stat
      		        |   whilecase_stat
      		        |   incase_stat
    			    |   forcase_stat
      		        |   untilcase_stat
      		        |   input_stat
      		        |   print_stat
			        |   return_stat
					;

assignment_stat     :   ID ':=' expression
                    ;

if_stat             :   'if' condition statements elsepart
                    ;

elsepart	        :   'else' statements
                    |	ε
                    ;

while_stat          :   'while' condition statements
                    ;

switchcase_stat     : 	'switchcase'
				                ( 'when' condition ':' statements )*
				                'default' ':' statements
            		;

whilecase_stat      : 	'whilecase'
        				        ( 'when' condition ':' statements )*
        				        'default' ':' statements
        			;

incase_stat         : 	'incase'
        				        ( 'when' condition ':' statements )*
        			;

forcase_stat        : 	'forcase' ID '=' INTEGER
        				        ( 'when' condition ':' statements )*
        			;

untilcase_stat      : 	'untilcase'
        				        ( 'when' condition ':' statements )*
        				        'until' condition
        			;

print_stat	        :   'print' expression
                    ;

input_stat	        :   'input' ID
                    ;

return_stat	        :   'return' expression
                    ;

actualpars	        :   '(' actualparlist ')'
                    ;

actualparlist       :   actualparitem ( ',' actualparitem )*
                    |	ε
                    ;

actualparitem       :   'in' expression 
					|  	'inout'ID
                    ;

condition           :   boolterm ( 'or' boolterm )*
                    ;

boolterm	        :   boolfactor ( 'and' boolfactor )*
                    ;

boolfactor          :   'not' '[' condition ']'
                    |   '[' condition ']'
                    |   expression relational_oper expression
                    ;

expression          :   optional_sign term ( add_oper term )*
                    ;

term                :   factor  ( mul_oper factor )*
                    ;

factor              :   INTEGER
                    |   '(' expression ')'
                    |   ID idtail
                    ;

idtail		        :   actualpars
                    |	ε
                    ;

relational_oper     :   '=' | '<=' | '>=' | '<>' | '<'  | '>'
                    ;

add_oper            :   '+' | '-'
                    ;

mul_oper	        :   '*' | '/'
                    ;

optional_sign 	    :   add_oper
                    |	ε
                    ;

