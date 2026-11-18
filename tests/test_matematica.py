"""Testes unitários para o módulo de modelagem matemática do HAWK Cross."""

import unittest
from src.hawk.matematica import modelo


class TestMatematica(unittest.TestCase):
    """Bateria de 4 testes fundamentais conforme especificação da entrega."""

    def test_tempo_minimo(self) -> None:
        """1. tempo_minimo(10) ≈ 21.667 s (L = 10m, v_ref = 0.6m/s, margem = 5s)."""
        t_min = modelo.tempo_minimo(10)
        self.assertAlmostEqual(t_min, 21.666666666666668, places=3)
        self.assertAlmostEqual(t_min, 21.667, places=3)

    def test_posicao_e_velocidade_extremidades(self) -> None:
        """2. posicao(T) == L e velocidade(0) == velocidade(T) == 0."""
        L = 10.0
        T = 28.0
        self.assertAlmostEqual(modelo.posicao(T, L, T), L)
        self.assertAlmostEqual(modelo.posicao(0.0, L, T), 0.0)
        self.assertAlmostEqual(modelo.velocidade(0.0, L, T), 0.0)
        self.assertAlmostEqual(modelo.velocidade(T, L, T), 0.0)

    def test_velocidade_maxima(self) -> None:
        """3. velocidade_maxima(10, 28) ≈ 0.5357 m/s (atingida em t = T/2)."""
        v_max = modelo.velocidade_maxima(10, 28)
        self.assertAlmostEqual(v_max, 0.5357, places=4)
        # Confere consistência com v(T/2)
        v_meio = modelo.velocidade(14.0, 10, 28)
        self.assertAlmostEqual(v_meio, v_max, places=5)

    def test_custo_extensao(self) -> None:
        """4. custo_extensao(21.667, 28) ≈ 1.267 veículos (com λ = 0.20 veíc/s)."""
        t_min = 21.666666666666668
        t_ext = 28.0
        custo = modelo.custo_extensao(t_min, t_ext, lam=0.20)
        self.assertAlmostEqual(custo, 1.2666666666666666, places=3)
        self.assertAlmostEqual(custo, 1.267, places=3)


if __name__ == "__main__":
    unittest.main()
