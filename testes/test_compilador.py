import unittest

from compilador import Compilador, ErroLexico, ErroSemantico, ErroSintatico, Parser, analisar_lexico


def compilar_texto(fonte: str):
    tokens = analisar_lexico(fonte)
    arvore = Parser(tokens).executar()
    return Compilador().compilar(arvore)


class TestesCompilador(unittest.TestCase):
    def test_operacao_e_variavel(self):
        simbolos, codigo = compilar_texto("(begin (set lote 3) (print (* lote 10)))")
        self.assertEqual(simbolos[0].nome, "lote")
        self.assertIn("MULT", codigo)
        self.assertIn("IMPR", codigo)

    def test_if_e_while(self):
        _, codigo = compilar_texto(
            "(begin (set x 2) (if (> x 0) (print 1) (print 0)) "
            "(while (> x 0) (set x (- x 1))))"
        )
        self.assertTrue(any(item.startswith("DSVF") for item in codigo))
        self.assertTrue(any(item.startswith("DSVS") for item in codigo))

    def test_erro_lexico(self):
        with self.assertRaises(ErroLexico):
            analisar_lexico("(print @)")

    def test_erro_sintatico(self):
        with self.assertRaises(ErroSintatico):
            Parser(analisar_lexico("(print 10")).executar()

    def test_erro_semantico(self):
        with self.assertRaises(ErroSemantico):
            compilar_texto("(print ausente)")


if __name__ == "__main__":
    unittest.main()
