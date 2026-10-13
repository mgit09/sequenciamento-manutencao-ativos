"""
Estrutura que guarda o resultado de uma execução de qualquer 
algoritmo de busca.
"""

import math
from dataclasses import dataclass, field

# ========================================================================

@dataclass
class ResultadoBusca:
    """
    Melhor solução encontrada e histórico de convergência de uma execução.
    """

    melhor_solucao: list[int] | None = None
    melhor_custo: float = math.inf

    # Um par (avaliações gastas, melhor custo até então) a cada melhoria
    historico_convergencia: list[tuple[int, int]] = field(default_factory=list)

    quantidade_avaliacoes_utilizadas: int = 0

    def registrar_se_melhor(
        self,
        solucao,
        custo: int,
        quantidade_avaliacoes: int,
    ):
        """
        Guarda a solução avaliada se ela for a melhor encontrada até agora.
        """
        if custo < self.melhor_custo:
            self.melhor_solucao = list(solucao)
            self.melhor_custo = custo
            self.historico_convergencia.append(
                (quantidade_avaliacoes, custo)
            )
