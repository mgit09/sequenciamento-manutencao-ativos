"""
Simulated Annealing (Têmpera Simulada) para sequenciamento de manutenção de ativos.

A partir de uma solução aleatória, sorteia sucessores por inversão (2-opt).
Movimentos que melhoram a solução são sempre aceitos. Movimentos que pioram
são aceitos com probabilidade baseada na distribuição de Gibbs (e^(-Δh / T)).
A temperatura T decresce geometricamente (T <- α * T) até o fim do orçamento.
"""

import math
from dataclasses import dataclass, field

from src.algoritmos.resultado_busca import ResultadoBusca
from src.problema_manutencao import INVERSAO, ProblemaManutencao

# ========================================================================
# TEMPERATURAS PADRÃO CALIBRADAS POR INSTÂNCIA
#
# A escala de T depende da magnitude típica de Δh = h(π') - h(π) sob o operador
# de inversão, que varia de centenas (instância pequena) a dezenas de milhares
# (instância grande).
#
# Para cada instância, T0 foi calibrada para aceitar ~80% das pioras no início
# (comportamento próximo a random walk) e Tf para aceitar menos de 0.1% no final
# (comportamento próximo a greedy descent).
TEMPERATURAS_PADRAO: dict[int, tuple[float, float]] = {
    12: (3500.0, 1.0),
    50: (27000.0, 5.0),
    150: (90000.0, 10.0),
}

# ========================================================================

@dataclass
class ResultadoSimulatedAnnealing(ResultadoBusca):
    """
    Resultado do simulated annealing, com informações específicas da têmpera.
    """

    temperatura_inicial: float = 0.0
    temperatura_final: float = 0.0
    taxa_resfriamento_alpha: float = 0.0

    quantidade_movimentos_aceitos: int = 0
    quantidade_piores_gerados: int = 0
    quantidade_piores_aceitos: int = 0

    # Histórico periódico da taxa de aceitação de movimentos piores:
    # cada elemento é uma tupla (avaliações gastas, temperatura atual, taxa na janela)
    historico_taxa_aceitacao: list[tuple[int, float, float]] = field(default_factory=list)

    def obter_metricas_adicionais(self) -> dict:
        """
        Devolve métricas da execução para inclusão nos relatórios e tabelas.
        """
        taxa_global_piores = (
            self.quantidade_piores_aceitos / self.quantidade_piores_gerados
            if self.quantidade_piores_gerados > 0
            else 0.0
        )
        return {
            "temperatura_inicial": self.temperatura_inicial,
            "temperatura_final": self.temperatura_final,
            "alpha": self.taxa_resfriamento_alpha,
            "movimentos_aceitos": self.quantidade_movimentos_aceitos,
            "piores_gerados": self.quantidade_piores_gerados,
            "piores_aceitos": self.quantidade_piores_aceitos,
            "taxa_aceitacao_piores_global": taxa_global_piores,
        }

# ========================================================================

def executar_simulated_annealing(
    problema: ProblemaManutencao,
    orcamento_avaliacoes: int,
    temperatura_inicial: float | None = None,
    temperatura_final: float | None = None,
    taxa_resfriamento: float | None = None,
    tamanho_janela_taxa: int = 500,
) -> ResultadoSimulatedAnnealing:
    """
    Executa o simulated annealing até esgotar o orçamento de avaliações.

    Utiliza obrigatoriamente a vizinhança de inversão e avaliação incremental
    para maximizar a eficiência de processamento.
    """
    if orcamento_avaliacoes <= 0:
        raise ValueError("O orçamento de avaliações deve ser positivo.")

    # O Simulated Annealing opera sobre a vizinhança de inversão
    problema.tipo_vizinhanca = INVERSAO
    problema.zerar_contador_avaliacoes()
    resultado = ResultadoSimulatedAnnealing()

    # Gera a solução inicial aleatória e calcula seu custo
    solucao_corrente = problema.gerar_solucao_aleatoria()
    custo_corrente = problema.avaliar(solucao_corrente)
    resultado.registrar_se_melhor(
        solucao_corrente,
        custo_corrente,
        problema.quantidade_avaliacoes,
    )

    # Constrói os dados intermediários para viabilizar avaliação incremental
    estado_corrente = problema.construir_estado(solucao_corrente)

    # Define as temperaturas inicial e final
    t_inicial, t_final = _definir_temperaturas(
        problema,
        temperatura_inicial,
        temperatura_final,
    )

    # Calcula o fator de resfriamento geométrico α para cobrir o orçamento
    passos_disponiveis = max(1, orcamento_avaliacoes - problema.quantidade_avaliacoes)
    if taxa_resfriamento is not None:
        if not (0.0 < taxa_resfriamento < 1.0):
            raise ValueError("A taxa de resfriamento deve estar entre 0 e 1.")
        alpha = float(taxa_resfriamento)
    else:
        alpha = (t_final / t_inicial) ** (1.0 / passos_disponiveis)

    resultado.temperatura_inicial = t_inicial
    resultado.temperatura_final = t_final
    resultado.taxa_resfriamento_alpha = alpha

    temperatura_atual = t_inicial
    piores_na_janela = 0
    aceitos_na_janela = 0

    while problema.quantidade_avaliacoes < orcamento_avaliacoes:
        # Sorteia um sucessor da vizinhança de inversão
        sucessor = problema.gerar_sucessor_aleatorio(solucao_corrente)

        # Avalia o sucessor reaproveitando o prefixo inalterado
        custo_sucessor = problema.avaliar_sucessor(estado_corrente, sucessor)
        resultado.registrar_se_melhor(
            sucessor,
            custo_sucessor,
            problema.quantidade_avaliacoes,
        )

        delta_h = custo_sucessor - custo_corrente
        movimento_aceito = False

        if delta_h <= 0:
            # Melhora ou empate: aceitação incondicional
            movimento_aceito = True
        else:
            # Piora: critério de aceitação de Gibbs / Metropolis
            resultado.quantidade_piores_gerados += 1
            piores_na_janela += 1

            expoente = -delta_h / temperatura_atual
            probabilidade_aceite = math.exp(expoente) if expoente > -700 else 0.0

            if problema.gerador_aleatorio.random() < probabilidade_aceite:
                movimento_aceito = True
                resultado.quantidade_piores_aceitos += 1
                aceitos_na_janela += 1

        if movimento_aceito:
            solucao_corrente = sucessor
            custo_corrente = custo_sucessor
            estado_corrente = problema.construir_estado(solucao_corrente)
            resultado.quantidade_movimentos_aceitos += 1

        # Resfriamento geométrico contínuo
        temperatura_atual = max(t_final, temperatura_atual * alpha)

        # Registra a taxa de aceitação de movimentos piores por janela
        if problema.quantidade_avaliacoes % tamanho_janela_taxa == 0:
            taxa_janela = (
                aceitos_na_janela / piores_na_janela
                if piores_na_janela > 0
                else 0.0
            )
            resultado.historico_taxa_aceitacao.append(
                (problema.quantidade_avaliacoes, temperatura_atual, taxa_janela)
            )
            piores_na_janela = 0
            aceitos_na_janela = 0

    # Registra o resíduo da última janela, se houver
    if piores_na_janela > 0:
        taxa_janela = aceitos_na_janela / piores_na_janela
        resultado.historico_taxa_aceitacao.append(
            (problema.quantidade_avaliacoes, temperatura_atual, taxa_janela)
        )

    resultado.quantidade_avaliacoes_utilizadas = problema.quantidade_avaliacoes
    return resultado

# ========================================================================

def _definir_temperaturas(
    problema: ProblemaManutencao,
    temperatura_inicial: float | None,
    temperatura_final: float | None,
) -> tuple[float, float]:
    """
    Determina T0 e Tf a partir dos argumentos ou da calibração da instância.
    """
    quantidade_ativos = problema.instancia.quantidade_ativos

    if temperatura_inicial is not None:
        t0 = float(temperatura_inicial)
    elif quantidade_ativos in TEMPERATURAS_PADRAO:
        t0 = TEMPERATURAS_PADRAO[quantidade_ativos][0]
    else:
        # Estimativa empírica para outras quantidades de ativos
        t0 = float(300.0 * (quantidade_ativos ** 1.1))

    if temperatura_final is not None:
        tf = float(temperatura_final)
    elif quantidade_ativos in TEMPERATURAS_PADRAO:
        tf = TEMPERATURAS_PADRAO[quantidade_ativos][1]
    else:
        tf = max(1.0, float(0.08 * quantidade_ativos))

    if t0 <= 0 or tf <= 0:
        raise ValueError("As temperaturas devem ser estritamente positivas.")

    if tf >= t0:
        raise ValueError("A temperatura inicial deve ser estritamente maior que a final.")

    return t0, tf

