"""
Testes automáticos do projeto. Da raiz do projeto, execute no terminal o seguinte comando: 

python -m tests.testes
"""

from src.problema_manutencao import (
    ler_instancia, 
    calcular_atraso_ponderado_total,
    ProblemaManutencao,
)

from src.algoritmos.alg_desc_gulosa import (
    MELHOR_MELHORIA,
    PRIMEIRA_MELHORIA,
    executar_descida_gulosa,
)

# ========================================================================
# FUNÇÕES AUXILIARES

def contar_posicoes_diferentes(sequencia_a, sequencia_b) -> int:
    """Conta em quantas posições duas sequências têm ativos diferentes."""
    return sum(
        ativo_a != ativo_b
        for ativo_a, ativo_b in zip(sequencia_a, sequencia_b)
    )

# ========================================================================
# TESTES

def teste1_sequencia_identidade_instancia_pequena():
    """
    Verifica os dados da instância pequena e o custo de uma sequência conhecida.
    """
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    # Confere se a instância foi carregada com os dados esperados
    assert instancia.quantidade_ativos == 12
    assert instancia.duracoes_servico.sum() == 55

    # Avalia a sequência que visita os ativos na ordem numérica
    sequencia_identidade = list(range(1, instancia.quantidade_ativos + 1))
    atraso_ponderado = calcular_atraso_ponderado_total(
        instancia,
        sequencia_identidade,
    )

    # Compara o resultado com o valor esperado para essa instância
    assert atraso_ponderado == 4366

# ------------------------------------------------------------------------
def teste2_solucao_aleatoria_e_permutacao_valida():
    """Verifica se soluções aleatórias são permutações válidas dos ativos."""
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )

    for _ in range(100):
        solucao = problema.gerar_solucao_aleatoria()

        # Toda solução deve conter cada ativo de 1 a 12 exatamente uma vez
        assert sorted(solucao) == list(range(1, 13))

# ------------------------------------------------------------------------
def teste3_mesma_semente_gera_mesma_solucao():
    """Verifica se a mesma semente gera soluções aleatórias idênticas."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    primeira = ProblemaManutencao(
        instancia,
        semente=42,
    ).gerar_solucao_aleatoria()

    segunda = ProblemaManutencao(
        instancia, 
        semente=42
    ).gerar_solucao_aleatoria()

    assert primeira == segunda

# ------------------------------------------------------------------------
def teste4_contador_conta_cada_avaliacao():
    """Verifica se o contador registra avaliações e pode ser zerado."""
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )

    for _ in range(5):
        problema.avaliar(problema.gerar_solucao_aleatoria())

    assert problema.quantidade_avaliacoes == 5

    problema.zerar_contador_avaliacoes()
    assert problema.quantidade_avaliacoes == 0

# ------------------------------------------------------------------------
def teste5_gerar_sucessores_cobre_toda_a_vizinhanca():
    """
    Verifica se todos os sucessores da vizinhança de troca 
    são gerados corretamente.
    """
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )
    solucao = problema.gerar_solucao_aleatoria()

    sucessores = list(problema.gerar_sucessores(solucao))

    # Para n = 12, a vizinhança de troca tem 12 * 11 / 2 = 66 sucessores
    assert len(sucessores) == 66

    # Todos os sucessores devem ser distintos entre si
    assert len({tuple(sucessor) for sucessor in sucessores}) == 66

    for sucessor in sucessores:
        # Cada sucessor deve continuar sendo uma permutação válida
        assert sorted(sucessor) == list(range(1, 13))

        # Cada sucessor difere da solução original em exatamente 2 posições
        assert contar_posicoes_diferentes(solucao, sucessor) == 2

# ------------------------------------------------------------------------
def teste6_gerar_sucessores_nao_altera_solucao_nem_conta_avaliacoes():
    """
    Verifica se gerar sucessores não altera a solução original 
    nem o contador.
    """
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )
    solucao = problema.gerar_solucao_aleatoria()
    copia_da_solucao = list(solucao)

    list(problema.gerar_sucessores(solucao))
    problema.gerar_sucessor_aleatorio(solucao)

    # A solução original deve permanecer intacta
    assert solucao == copia_da_solucao

    # Gerar sucessores não é avaliar: o contador deve continuar em zero
    assert problema.quantidade_avaliacoes == 0

# ------------------------------------------------------------------------
def teste7_sucessor_aleatorio_e_permutacao_valida_com_duas_trocas():
    """
    Verifica se sucessores aleatórios são permutações válidas 
    com duas posições trocadas.
    """
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )
    solucao = problema.gerar_solucao_aleatoria()

    for _ in range(100):
        sucessor = problema.gerar_sucessor_aleatorio(solucao)

        assert sorted(sucessor) == list(range(1, 13))
        assert contar_posicoes_diferentes(solucao, sucessor) == 2

# ------------------------------------------------------------------------
def teste8_descida_gulosa_respeita_orcamento_exato():
    """Verifica se o algoritmo para exatamente ao atingir o orçamento."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    for variante in (MELHOR_MELHORIA, PRIMEIRA_MELHORIA):
        problema = ProblemaManutencao(instancia, semente=1)
        resultado = executar_descida_gulosa(problema, 5000, variante)

        assert resultado.quantidade_avaliacoes_utilizadas == 5000
        assert problema.quantidade_avaliacoes == 5000

# ------------------------------------------------------------------------
def teste9_descida_gulosa_resultado_e_consistente():
    """Verifica solução, custo e histórico de convergência do resultado."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    for variante in (MELHOR_MELHORIA, PRIMEIRA_MELHORIA):
        problema = ProblemaManutencao(instancia, semente=2)
        resultado = executar_descida_gulosa(problema, 5000, variante)

        # A melhor solução deve ser uma permutação válida
        assert sorted(resultado.melhor_solucao) == list(range(1, 13))

        # O custo informado deve coincidir com o recalculado do zero
        assert resultado.melhor_custo == calcular_atraso_ponderado_total(
            instancia,
            resultado.melhor_solucao,
        )

        # O histórico deve ter avaliações crescentes e custos estritamente decrescentes
        historico = resultado.historico_convergencia
        for (avaliacoes_antes, custo_antes), (avaliacoes_depois, custo_depois) in zip(
            historico,
            historico[1:],
        ):
            assert avaliacoes_antes < avaliacoes_depois
            assert custo_antes > custo_depois

# ------------------------------------------------------------------------
def teste10_otimos_locais_reportados_sao_mesmo_otimos_locais():
    """Verifica se nenhum sucessor de um ótimo local reportado tem custo menor."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    for variante in (MELHOR_MELHORIA, PRIMEIRA_MELHORIA):
        problema = ProblemaManutencao(instancia, semente=3)
        resultado = executar_descida_gulosa(problema, 5000, variante)

        assert len(resultado.otimos_locais) > 0

        for otimo_local in resultado.otimos_locais:
            custo_otimo_local = calcular_atraso_ponderado_total(
                instancia,
                otimo_local,
            )

            for sucessor in problema.gerar_sucessores(list(otimo_local)):
                custo_sucessor = calcular_atraso_ponderado_total(
                    instancia,
                    sucessor,
                )
                assert custo_sucessor >= custo_otimo_local

# ========================================================================
# EXECUÇÃO DOS TESTES

if __name__ == "__main__":
    # Tenta rodar todos os testes:
    teste1_sequencia_identidade_instancia_pequena()
    teste2_solucao_aleatoria_e_permutacao_valida()
    teste3_mesma_semente_gera_mesma_solucao()
    teste4_contador_conta_cada_avaliacao()
    teste5_gerar_sucessores_cobre_toda_a_vizinhanca()
    teste6_gerar_sucessores_nao_altera_solucao_nem_conta_avaliacoes()
    teste7_sucessor_aleatorio_e_permutacao_valida_com_duas_trocas()
    teste8_descida_gulosa_respeita_orcamento_exato()
    teste9_descida_gulosa_resultado_e_consistente()
    teste10_otimos_locais_reportados_sao_mesmo_otimos_locais()

    print("Todos os testes passaram.") # Se algum falhar, não será impresso
