from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
import sys


class ErroCompilacao(Exception):
    """Erro esperado e legível."""


class ErroLexico(ErroCompilacao):
    pass


class ErroSintatico(ErroCompilacao):
    pass


class ErroSemantico(ErroCompilacao):
    pass


@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linha: int
    coluna: int


@dataclass
class Simbolo:
    nome: str
    endereco: int
    tipo: str
    escopo: str = "Global"


PALAVRAS = {"if": "IF", "while": "WHILE", "begin": "BEGIN", "set": "SET", "print": "PRINT"}
OPERADORES = {"+", "-", "*", "/", "%", ">", "<", "==", "!=", "<=", ">="}
PADRAO_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PADRAO_NUMERO = re.compile(r"(?:\d+\.\d+|\d+)")


def analisar_lexico(fonte: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    linha = coluna = 1

    while i < len(fonte):
        caractere = fonte[i]
        if caractere in " \t\r":
            i += 1
            coluna += 1
            continue
        if caractere == "\n":
            i += 1
            linha += 1
            coluna = 1
            continue
        if caractere == ";":
            while i < len(fonte) and fonte[i] != "\n":
                i += 1
                coluna += 1
            continue
        if caractere in "()":
            tokens.append(Token("LPAR" if caractere == "(" else "RPAR", caractere, linha, coluna))
            i += 1
            coluna += 1
            continue

        inicio = coluna
        operador = next((op for op in sorted(OPERADORES, key=len, reverse=True) if fonte.startswith(op, i)), None)
        if operador:
            tokens.append(Token("OP", operador, linha, inicio))
            i += len(operador)
            coluna += len(operador)
            continue

        numero = PADRAO_NUMERO.match(fonte, i)
        if numero:
            lexema = numero.group()
            tokens.append(Token("FLOAT" if "." in lexema else "INTEGER", lexema, linha, inicio))
            i = numero.end()
            coluna += len(lexema)
            continue

        identificador = PADRAO_ID.match(fonte, i)
        if identificador:
            lexema = identificador.group()
            tokens.append(Token(PALAVRAS.get(lexema, "ID"), lexema, linha, inicio))
            i = identificador.end()
            coluna += len(lexema)
            continue

        raise ErroLexico(f"Erro Léxico: caractere inválido '{caractere}' na linha {linha}, coluna {coluna}.")

    return tokens


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.posicao = 0

    def executar(self):
        if not self.tokens:
            raise ErroSintatico("Erro Sintático: o arquivo está vazio.")
        arvore = self._expressao()
        if self.posicao != len(self.tokens):
            token = self.tokens[self.posicao]
            raise ErroSintatico(f"Erro Sintático: token inesperado '{token.lexema}' na linha {token.linha}.")
        return arvore

    def _expressao(self):
        if self.posicao >= len(self.tokens):
            raise ErroSintatico("Erro Sintático: fim de arquivo inesperado; esperava-se uma expressão ou ')'.")
        token = self.tokens[self.posicao]
        self.posicao += 1
        if token.tipo == "LPAR":
            itens = []
            while self.posicao < len(self.tokens) and self.tokens[self.posicao].tipo != "RPAR":
                itens.append(self._expressao())
            if self.posicao >= len(self.tokens):
                raise ErroSintatico(f"Erro Sintático: parêntese aberto na linha {token.linha} não foi fechado.")
            self.posicao += 1
            return itens
        if token.tipo == "RPAR":
            raise ErroSintatico(f"Erro Sintático: ')' sem abertura correspondente na linha {token.linha}.")
        return token


class Compilador:
    def __init__(self):
        self.simbolos: dict[str, Simbolo] = {}
        self.codigo: list[str] = []
        self.rotulo = 0

    def compilar(self, arvore) -> tuple[list[Simbolo], list[str]]:
        self._validar(arvore, conjunto_definidas=set())
        quantidade = len(self.simbolos)
        self.codigo = ["INPP"]
        if quantidade:
            self.codigo.append(f"AMEM {quantidade}")
        self._gerar(arvore)
        if quantidade:
            self.codigo.append(f"DMEM {quantidade}")
        self.codigo.append("PARA")
        return list(self.simbolos.values()), self.codigo

    def _novo_rotulo(self) -> str:
        self.rotulo += 1
        return f"R{self.rotulo}"

    @staticmethod
    def _cabeca(no) -> str:
        if not isinstance(no, list) or not no or not isinstance(no[0], Token):
            raise ErroSintatico("Erro Sintático: toda lista não vazia precisa iniciar com comando ou operador.")
        return no[0].lexema

    def _validar(self, no, conjunto_definidas: set[str]) -> str:
        if isinstance(no, Token):
            if no.tipo == "ID":
                if no.lexema not in conjunto_definidas:
                    raise ErroSemantico(f"Erro Semântico: variável '{no.lexema}' não foi inicializada (linha {no.linha}).")
                return self.simbolos[no.lexema].tipo
            if no.tipo == "INTEGER":
                return "Inteiro"
            if no.tipo == "FLOAT":
                return "Real"
            raise ErroSintatico(f"Erro Sintático: símbolo '{no.lexema}' usado fora de uma expressão válida.")

        comando = self._cabeca(no)
        argumentos = no[1:]
        if comando in OPERADORES:
            if len(argumentos) != 2:
                raise ErroSintatico(f"Erro Sintático: operador '{comando}' exige exatamente 2 argumentos.")
            tipos = [self._validar(arg, conjunto_definidas) for arg in argumentos]
            return "Real" if "Real" in tipos else "Inteiro"
        if comando == "print":
            self._exigir_quantidade(comando, argumentos, 1)
            return self._validar(argumentos[0], conjunto_definidas)
        if comando == "set":
            self._exigir_quantidade(comando, argumentos, 2)
            alvo = argumentos[0]
            if not isinstance(alvo, Token) or alvo.tipo != "ID":
                raise ErroSemantico("Erro Semântico: 'set' exige um identificador como primeiro argumento.")
            tipo = self._validar(argumentos[1], conjunto_definidas)
            if alvo.lexema not in self.simbolos:
                self.simbolos[alvo.lexema] = Simbolo(alvo.lexema, len(self.simbolos), tipo)
            conjunto_definidas.add(alvo.lexema)
            return tipo
        if comando == "begin":
            if not argumentos:
                raise ErroSintatico("Erro Sintático: 'begin' precisa conter ao menos uma expressão.")
            tipo = "Inteiro"
            for argumento in argumentos:
                tipo = self._validar(argumento, conjunto_definidas)
            return tipo
        if comando == "if":
            self._exigir_quantidade(comando, argumentos, 3)
            self._validar(argumentos[0], conjunto_definidas)
            self._validar(argumentos[1], set(conjunto_definidas))
            self._validar(argumentos[2], set(conjunto_definidas))
            return "Inteiro"
        if comando == "while":
            self._exigir_quantidade(comando, argumentos, 2)
            self._validar(argumentos[0], conjunto_definidas)
            self._validar(argumentos[1], set(conjunto_definidas))
            return "Inteiro"
        raise ErroSemantico(f"Erro Semântico: comando ou função '{comando}' não existe no Mini-Lisp.")

    @staticmethod
    def _exigir_quantidade(comando: str, argumentos: list, quantidade: int):
        if len(argumentos) != quantidade:
            raise ErroSintatico(
                f"Erro Sintático: estrutura '{comando}' malformada; esperava {quantidade} argumento(s), recebeu {len(argumentos)}."
            )

    def _gerar(self, no):
        if isinstance(no, Token):
            if no.tipo in {"INTEGER", "FLOAT"}:
                self.codigo.append(f"CRCT {no.lexema}")
            else:
                self.codigo.append(f"CRVL {self.simbolos[no.lexema].endereco}")
            return

        comando, argumentos = self._cabeca(no), no[1:]
        instrucoes = {
            "+": "SOMA", "-": "SUBT", "*": "MULT", "/": "DIVI", "%": "MODI",
            ">": "CMMA", "<": "CMME", "==": "CMIG", "!=": "CMDG", "<=": "CMEG", ">=": "CMAG",
        }
        if comando in instrucoes:
            self._gerar(argumentos[0]); self._gerar(argumentos[1])
            self.codigo.append(instrucoes[comando]); return
        if comando == "print":
            self._gerar(argumentos[0]); self.codigo.append("IMPR"); return
        if comando == "set":
            self._gerar(argumentos[1])
            self.codigo.append(f"ARMZ {self.simbolos[argumentos[0].lexema].endereco}"); return
        if comando == "begin":
            for argumento in argumentos: self._gerar(argumento)
            return
        if comando == "if":
            senao, fim = self._novo_rotulo(), self._novo_rotulo()
            self._gerar(argumentos[0]); self.codigo.append(f"DSVF {senao}")
            self._gerar(argumentos[1]); self.codigo.extend([f"DSVS {fim}", f"{senao}: NADA"])
            self._gerar(argumentos[2]); self.codigo.append(f"{fim}: NADA"); return
        if comando == "while":
            inicio, fim = self._novo_rotulo(), self._novo_rotulo()
            self.codigo.append(f"{inicio}: NADA"); self._gerar(argumentos[0]); self.codigo.append(f"DSVF {fim}")
            self._gerar(argumentos[1]); self.codigo.extend([f"DSVS {inicio}", f"{fim}: NADA"])


def mostrar_resultado(tokens: list[Token], simbolos: list[Simbolo], codigo: list[str]):
    print("\nLISTA DE TOKENS/LEXEMAS")
    print(f"{'NUM':<5} {'TOKEN':<10} {'LEXEMA':<15} {'LINHA':<5}")
    for numero, token in enumerate(tokens, 1):
        print(f"{numero:<5} {token.tipo:<10} {token.lexema:<15} {token.linha:<5}")
    print("\nTABELA DE SÍMBOLOS")
    if not simbolos:
        print("(vazia)")
    else:
        print(f"{'IDENTIFICADOR':<18} {'ENDEREÇO':<10} {'TIPO':<10} {'ESCOPO':<10}")
        for simbolo in simbolos:
            print(f"{simbolo.nome:<18} {simbolo.endereco:<10} {simbolo.tipo:<10} {simbolo.escopo:<10}")
    print("\nCÓDIGO MEPA")
    print("\n".join(codigo))


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python compilador.py caminho_do_programa.lisp")
        return 1
    try:
        fonte = Path(sys.argv[1]).read_text(encoding="utf-8")
        tokens = analisar_lexico(fonte)
        arvore = Parser(tokens).executar()
        simbolos, codigo = Compilador().compilar(arvore)
        mostrar_resultado(tokens, simbolos, codigo)
        return 0
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {sys.argv[1]}")
        return 1
    except ErroCompilacao as erro:
        print(erro)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
