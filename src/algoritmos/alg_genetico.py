"""
Algoritmo Genético (AG) para sequenciamento de manutenção de ativos.

Utiliza codificação por permutação, amostragem aleatória inicial,
seleção por torneio (minimização direta de h), Order Crossover (OX),
mutação por operador de vizinhança de inversão (2-opt) e elitismo.
"""

from dataclasses import dataclass, field
import numpy as np

from src.algoritmos.resultado_busca import ResultadoBusca
from src.problema_manutencao import (
    ProblemaManutencao,
    aplicar_cruzamento_ox,
    aplicar_inversao,
)

# ========================================================================

@dataclass
class ResultadoAlgoritmoGenetico(ResultadoBusca):
    """
    Resultado do algoritmo genético, com informações da evolução da população.
    """

    tamanho_populacao: int = 50
    taxa_cruzamento: float = 0.85
    taxa_mutacao: float = 0.15
    tamanho_torneio: int = 3
    quantidade_elites: int = 1
    geracoes_concluidas: int = 0

    # Histórico da média de h(π) da população: (avaliações gastas, custo médio)
    historico_media_populacao: list[tuple[int, float]] = field(default_factory=list)

    # Histórico de diversidade (quantidade de cromossomos distintos): (avaliações gastas, distintos)
    historico_diversidade: list[tuple[int, int]] = field(default_factory=list)

    def obter_metricas_adicionais(self) -> dict:
        """
        Devolve métricas da execução para inclusão nos relatórios e tabelas.
        """
        return {
            "geracoes_concluidas": self.geracoes_concluidas,
            "tamanho_populacao": self.tamanho_populacao,
            "taxa_cruzamento": self.taxa_cruzamento,
            "taxa_mutacao": self.taxa_mutacao,
            "tamanho_torneio": self.tamanho_torneio,
            "quantidade_elites": self.quantidade_elites,
        }

# ========================================================================
# OPERADORES INTERNOS DO ALGORITMO GENÉTICO

def _selecionar_por_torneio(
    populacao: list[list[int]],
    custos: list[int],
    tamanho_torneio: int,
    gerador_aleatorio: np.random.Generator,
) -> list[int]:
    """
    Seleciona um indivíduo por torneio (menor custo h vence).
    """
    tamanho_pop = len(populacao)
    k = min(tamanho_torneio, tamanho_pop)
    indices_participantes = gerador_aleatorio.choice(
        tamanho_pop,
        size=k,
        replace=False,
    )
    melhor_indice = min(indices_participantes, key=lambda idx: custos[idx])
    return populacao[melhor_indice]


def _mutar_por_inversao(
    individuo: list[int],
    gerador_aleatorio: np.random.Generator,
) -> list[int]:
    """
    Aplica mutação sorteando dois índices distintos e invertendo o trecho (2-opt).
    """
    n = len(individuo)
    if n < 2:
        return list(individuo)
    pos_a, pos_b = gerador_aleatorio.choice(n, size=2, replace=False)
    return aplicar_inversao(individuo, min(pos_a, pos_b), max(pos_a, pos_b))


def _cruzamento_ox(
    pai_a: list[int],
    pai_b: list[int],
    gerador_aleatorio: np.random.Generator,
) -> tuple[list[int], list[int]]:
    """
    Aplica o Order Crossover (OX) sorteando dois pontos de corte aleatórios.
    """
    n = len(pai_a)
    if n < 2:
        return list(pai_a), list(pai_b)
    pos_a, pos_b = gerador_aleatorio.choice(n, size=2, replace=False)
    return aplicar_cruzamento_ox(pai_a, pai_b, pos_a, pos_b)

# ========================================================================

def executar_algoritmo_genetico(
    problema: ProblemaManutencao,
    orcamento_avaliacoes: int,
    tamanho_populacao: int = 50,
    taxa_cruzamento: float = 0.85,
    taxa_mutacao: float = 0.15,
    tamanho_torneio: int = 3,
    quantidade_elites: int = 1,
) -> ResultadoAlgoritmoGenetico:
    """
    Executa o Algoritmo Genético até esgotar o orçamento de avaliações.

    Segue estritamente o protocolo da Seção 2.5 e Seção 3:
    - População inicial aleatória
    - Seleção por torneio
    - Order Crossover (OX)
    - Mutação por inversão (2-opt)
    - Elitismo
    - Parada exata ao esgotar o orçamento
    """
    if orcamento_avaliacoes <= 0:
        raise ValueError("O orçamento de avaliações deve ser positivo.")
    if tamanho_populacao <= 0:
        raise ValueError("O tamanho da população deve ser positivo.")
    if quantidade_elites < 0 or quantidade_elites >= tamanho_populacao:
        raise ValueError("Quantidade de elites deve ser entre 0 e tamanho_populacao - 1.")

    problema.zerar_contador_avaliacoes()
    resultado = ResultadoAlgoritmoGenetico(
        tamanho_populacao=tamanho_populacao,
        taxa_cruzamento=taxa_cruzamento,
        taxa_mutacao=taxa_mutacao,
        tamanho_torneio=tamanho_torneio,
        quantidade_elites=quantidade_elites,
    )
    gerador = problema.gerador_aleatorio

    # 1. População inicial
    populacao: list[list[int]] = []
    custos: list[int] = []

    while len(populacao) < tamanho_populacao and problema.quantidade_avaliacoes < orcamento_avaliacoes:
        ind = problema.gerar_solucao_aleatoria()
        custo = problema.avaliar(ind)
        populacao.append(ind)
        custos.append(custo)
        resultado.registrar_se_melhor(ind, custo, problema.quantidade_avaliacoes)

    if not populacao or problema.quantidade_avaliacoes >= orcamento_avaliacoes:
        if populacao:
            resultado.historico_media_populacao.append(
                (problema.quantidade_avaliacoes, float(np.mean(custos)))
            )
            resultado.historico_diversidade.append(
                (problema.quantidade_avaliacoes, len({tuple(ind) for ind in populacao}))
            )
        resultado.quantidade_avaliacoes_utilizadas = problema.quantidade_avaliacoes
        return resultado

    # Métricas da geração 0
    resultado.historico_media_populacao.append(
        (problema.quantidade_avaliacoes, float(np.mean(custos)))
    )
    resultado.historico_diversidade.append(
        (problema.quantidade_avaliacoes, len({tuple(ind) for ind in populacao}))
    )

    # 2. Laço evolutivo
    while problema.quantidade_avaliacoes < orcamento_avaliacoes:
        # Separação dos indivíduos de elite
        indices_ordenados = np.argsort(custos)
        nova_populacao: list[list[int]] = [
            list(populacao[i]) for i in indices_ordenados[:quantidade_elites]
        ]
        novos_custos: list[int] = [
            custos[i] for i in indices_ordenados[:quantidade_elites]
        ]

        # Gera descendentes até completar a nova população ou esgotar orçamento
        while len(nova_populacao) < tamanho_populacao:
            if problema.quantidade_avaliacoes >= orcamento_avaliacoes:
                break

            pai_1 = _selecionar_por_torneio(populacao, custos, tamanho_torneio, gerador)
            pai_2 = _selecionar_por_torneio(populacao, custos, tamanho_torneio, gerador)

            # Recombinação (cruzamento)
            if gerador.random() < taxa_cruzamento:
                filho_1, filho_2 = _cruzamento_ox(pai_1, pai_2, gerador)
            else:
                filho_1, filho_2 = list(pai_1), list(pai_2)

            # Mutação por inversão e avaliação dos descendentes
            for filho in (filho_1, filho_2):
                if len(nova_populacao) >= tamanho_populacao:
                    break
                if problema.quantidade_avaliacoes >= orcamento_avaliacoes:
                    break

                if gerador.random() < taxa_mutacao:
                    filho = _mutar_por_inversao(filho, gerador)

                custo_filho = problema.avaliar(filho)
                resultado.registrar_se_melhor(
                    filho,
                    custo_filho,
                    problema.quantidade_avaliacoes,
                )
                nova_populacao.append(filho)
                novos_custos.append(custo_filho)

        # Atualiza a população se completou a geração
        if len(nova_populacao) == tamanho_populacao:
            populacao = nova_populacao
            custos = novos_custos
            resultado.geracoes_concluidas += 1
            resultado.historico_media_populacao.append(
                (problema.quantidade_avaliacoes, float(np.mean(custos)))
            )
            resultado.historico_diversidade.append(
                (problema.quantidade_avaliacoes, len({tuple(ind) for ind in populacao}))
            )
        else:
            break

    resultado.quantidade_avaliacoes_utilizadas = problema.quantidade_avaliacoes
    return resultado

