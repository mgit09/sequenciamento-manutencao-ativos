"""
Descida gulosa (greedy descent) com reinício aleatório (random restart).

A partir de uma solução aleatória, move-se sempre para um sucessor que
melhora o custo, até chegar a um ótimo local. Ao chegar, recomeça de uma
nova solução aleatória, guardando a melhor solução já vista, até esgotar
o orçamento de avaliações.
"""

from dataclasses import dataclass, field

from src.algoritmos.resultado_busca import ResultadoBusca
from src.problema_manutencao import ProblemaManutencao

# Varre toda a vizinhança e se move para o melhor sucessor
MELHOR_MELHORIA = "melhor_melhoria"

# Se move para o primeiro sucessor encontrado que melhora o custo
PRIMEIRA_MELHORIA = "primeira_melhoria"

# ========================================================================

@dataclass
class ResultadoDescidaGulosa(ResultadoBusca):
    """
    Resultado da descida gulosa, com informações específicas do algoritmo.
    """

    # Quantidade de movimentos que melhoraram a solução corrente
    quantidade_passos_melhoria: int = 0

    # Cada ótimo local confirmado (nenhum sucessor melhora), um por reinício
    otimos_locais: list[tuple[int, ...]] = field(default_factory=list)

# ========================================================================

def executar_descida_gulosa(
    problema: ProblemaManutencao,
    orcamento_avaliacoes: int,
    variante: str = MELHOR_MELHORIA,
) -> ResultadoDescidaGulosa:
    """
    Executa a descida gulosa com reinício aleatório até esgotar o orçamento.
    """
    if variante not in (MELHOR_MELHORIA, PRIMEIRA_MELHORIA):
        raise ValueError(f"Variante desconhecida: {variante}")

    problema.zerar_contador_avaliacoes()
    resultado = ResultadoDescidaGulosa()

    while problema.quantidade_avaliacoes < orcamento_avaliacoes:
        # Cada volta do laço é um reinício a partir de uma solução aleatória
        solucao_corrente = problema.gerar_solucao_aleatoria()
        custo_corrente = problema.avaliar(solucao_corrente)
        resultado.registrar_se_melhor(
            solucao_corrente,
            custo_corrente,
            problema.quantidade_avaliacoes,
        )

        solucao_corrente, chegou_a_otimo_local = _descer_ate_otimo_local(
            problema,
            solucao_corrente,
            custo_corrente,
            orcamento_avaliacoes,
            variante,
            resultado,
        )

        # Se o orçamento acabou no meio da varredura, o ótimo local não foi confirmado
        if chegou_a_otimo_local:
            resultado.otimos_locais.append(tuple(solucao_corrente))

    resultado.quantidade_avaliacoes_utilizadas = problema.quantidade_avaliacoes
    return resultado

# ========================================================================

def _descer_ate_otimo_local(
    problema: ProblemaManutencao,
    solucao_corrente: list[int],
    custo_corrente: int,
    orcamento_avaliacoes: int,
    variante: str,
    resultado: ResultadoDescidaGulosa,
) -> tuple[list[int], bool]:
    """
    Move-se para sucessores melhores até não haver nenhum.

    Retorna a solução em que parou e se ela é um ótimo local confirmado
    (False quando o orçamento esgotou antes de terminar a varredura).
    """
    while True:
        melhor_sucessor = None
        melhor_custo_sucessor = custo_corrente

        for sucessor in problema.gerar_sucessores(solucao_corrente):
            if problema.quantidade_avaliacoes >= orcamento_avaliacoes:
                return solucao_corrente, False

            custo_sucessor = problema.avaliar(sucessor)
            resultado.registrar_se_melhor(
                sucessor,
                custo_sucessor,
                problema.quantidade_avaliacoes,
            )

            # Só uma melhora estrita é aceita (evita ciclos em platôs)
            if custo_sucessor < melhor_custo_sucessor:
                melhor_sucessor = sucessor
                melhor_custo_sucessor = custo_sucessor

                if variante == PRIMEIRA_MELHORIA:
                    break

        # Nenhum sucessor melhora: a solução corrente é um ótimo local
        if melhor_sucessor is None:
            return solucao_corrente, True

        solucao_corrente = melhor_sucessor
        custo_corrente = melhor_custo_sucessor
        resultado.quantidade_passos_melhoria += 1
