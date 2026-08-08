# Compilador Mini-Lisp para MEPA

Projeto acadêmico em Python que lê um arquivo `.lisp`, realiza as análises léxica, sintática e semântica e gera código intermediário MEPA.

## Requisitos

- Python 3.10 ou superior

## Como executar no Windows

1. Baixe ou clone este repositório.
2. Instale o Python pelo site oficial 
3. Dê dois cliques em `executar_testes.bat`.
4. O script abre cada exemplo individualmente e pausa para permitir conferência.

Também é possível executar um arquivo específico pelo Prompt de Comando:

```bat
python compilador.py exemplos\positivo_calculo.lisp
```

## Exemplos incluídos

| Arquivo | Resultado esperado |
| --- | --- |
| `positivo_calculo.lisp` | Tokens, tabela com duas variáveis e código MEPA |
| `positivo_controle.lisp` | Tokens, tabela de símbolos e MEPA com `if` e `while` |
| `negativo_lexico.lisp` | Mensagem de caractere inválido |
| `negativo_sintatico.lisp` | Mensagem de parêntese não fechado |
| `negativo_semantico.lisp` | Mensagem de variável não inicializada |

## Estrutura implementada

- analisador léxico com linha e coluna;
- parser de S-expressions e criação da AST;
- validação de comandos e quantidade de argumentos;
- tabela de símbolos com endereço, tipo presumido e escopo;
- números inteiros e reais;
- operadores `+`, `-`, `*`, `/`, `%`, `>`, `<`, `==`, `!=`, `<=` e `>=`;
- comandos `print`, `set`, `begin`, `if` e `while`;
- geração de instruções MEPA;
- tratamento legível de erros léxicos, sintáticos e semânticos.

