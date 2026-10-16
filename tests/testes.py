"""
Testes automáticos do projeto. Da raiz do projeto, execute no terminal o seguinte comando: 

python -m tests.testes
"""

from src.problema_manutencao import (
    ler_instancia, 
    calcular_atraso_ponderado_total,
    ProblemaManutencao,
    INVERSAO,
    REALOCACAO,
    TIPOS_VIZINHANCA,
    TROCA,
    aplicar_inversao,
    aplicar_realocacao, 
    aplicar_troca,
    Sucessor,
)

from src.algoritmos.alg_desc_gulosa import (
    MELHOR_MELHORIA,
    PRIMEIRA_MELHORIA,
    executar_descida_gulosa,
)
from src.algoritmos.alg_simulated_annealing import (
    executar_simulated_annealing,
)

# ========================================================================
# FUNÇÕES AUXILIARES

def contar_posicoes_diferentes(sequencia_a, sequencia_b) -> int:
    """Conta em quantas posições duas sequências têm ativos diferentes."""
    return sum(
        ativo_a != ativo_b
        for ativo_a, ativo_b in zip(sequencia_a, sequencia_b)
    )

# ------------------------------------------------------------------------

def encontrar_primeira_posicao_diferente(sequencia_a, sequencia_b) -> int:
    """Devolve a primeira posição em que duas sequências têm ativos diferentes."""
    for posicao, (ativo_a, ativo_b) in enumerate(zip(sequencia_a, sequencia_b)):
        if ativo_a != ativo_b:
            return posicao

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

# ------------------------------------------------------------------------

def teste11_operadores_reproduzem_os_exemplos_da_figura_3():
    """Confere cada operador com os exemplos da Figura 3 do enunciado."""
    solucao = [3, 7, 1, 5, 2, 8]

    assert aplicar_troca(solucao, 1, 4) == [3, 2, 1, 5, 7, 8]
    assert aplicar_realocacao(solucao, 1, 4) == [3, 1, 5, 2, 7, 8]
    assert aplicar_inversao(solucao, 1, 4) == [3, 2, 5, 1, 7, 8]

    # Os operadores devem devolver cópias, sem alterar a solução original
    assert solucao == [3, 7, 1, 5, 2, 8]

# ------------------------------------------------------------------------

def teste12_tamanho_das_vizinhancas_confere_com_o_relatorio():
    """
    Confere o número de sucessores distintos com a Tabela 1 do relatório.
    """
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    tamanhos_esperados = {
        12: {TROCA: 66, REALOCACAO: 121, INVERSAO: 66},
        50: {TROCA: 1225, REALOCACAO: 2401, INVERSAO: 1225},
        150: {TROCA: 11175, REALOCACAO: 22201, INVERSAO: 11175},
    }

    for quantidade_ativos, tamanhos in tamanhos_esperados.items():
        solucao = list(range(1, quantidade_ativos + 1))

        for tipo_vizinhanca, tamanho_esperado in tamanhos.items():
            problema = ProblemaManutencao(
                instancia,
                semente=1,
                tipo_vizinhanca=tipo_vizinhanca,
            )
            sucessores = [
                tuple(sucessor) for sucessor in problema.gerar_sucessores(solucao)
            ]

            assert len(sucessores) == tamanho_esperado
            assert len(set(sucessores)) == tamanho_esperado

# ------------------------------------------------------------------------

def teste13_sucessores_sao_permutacoes_validas_e_diferentes_da_original():
    """
    Verifica validade e diferença em relação à original, para cada vizinhança.
    """
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    for tipo_vizinhanca in TIPOS_VIZINHANCA:
        problema = ProblemaManutencao(
            instancia,
            semente=1,
            tipo_vizinhanca=tipo_vizinhanca,
        )
        solucao = problema.gerar_solucao_aleatoria()
        copia_da_solucao = list(solucao)

        for sucessor in problema.gerar_sucessores(solucao):
            assert sorted(sucessor) == list(range(1, 13))
            assert sucessor != solucao

        assert solucao == copia_da_solucao

# ------------------------------------------------------------------------

def teste14_sucessor_aleatorio_pertence_a_vizinhanca_e_a_cobre_toda():
    """
    Verifica se o sorteio só gera sucessores válidos e alcança todos eles.
    """
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    for tipo_vizinhanca in TIPOS_VIZINHANCA:
        problema = ProblemaManutencao(
            instancia,
            semente=1,
            tipo_vizinhanca=tipo_vizinhanca,
        )
        solucao = problema.gerar_solucao_aleatoria()

        vizinhanca = {
            tuple(sucessor)
            for sucessor in problema.gerar_sucessores(solucao)
        }

        sorteados = {
            tuple(problema.gerar_sucessor_aleatorio(solucao))
            for _ in range(5000)
        }

        # Todo sorteado deve estar na vizinhança, e a vizinhança toda deve ser alcançável
        assert sorteados == vizinhanca

# ------------------------------------------------------------------------

def teste15_tipo_de_vizinhanca_desconhecido_gera_erro():
    """Verifica se um tipo de vizinhança inválido é rejeitado."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    erro_levantado = False
    try:
        ProblemaManutencao(
            instancia,
            tipo_vizinhanca="invalida",
        )
    except ValueError:
        erro_levantado = True

    assert erro_levantado

# ------------------------------------------------------------------------

def teste16_primeira_posicao_alterada_esta_correta():
    """
    Verifica que cada sucessor informa corretamente onde começa 
    a diferir da origem.
    """
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    for tipo_vizinhanca in TIPOS_VIZINHANCA:
        problema = ProblemaManutencao(
            instancia,
            semente=1,
            tipo_vizinhanca=tipo_vizinhanca,
        )
        solucao = problema.gerar_solucao_aleatoria()

        for sucessor in problema.gerar_sucessores(solucao):
            assert isinstance(sucessor, Sucessor)
            assert sucessor.primeira_posicao_alterada == encontrar_primeira_posicao_diferente(
                solucao,
                sucessor,
            )

# ------------------------------------------------------------------------

def teste17_avaliacao_incremental_coincide_com_avaliacao_completa():
    """Compara a avaliação incremental com a completa em todas as vizinhanças e instâncias."""
    for nome_instancia in ("pequena", "media"):
        instancia = ler_instancia(f"instancias/manutencao_{nome_instancia}.txt")

        for tipo_vizinhanca in TIPOS_VIZINHANCA:
            problema = ProblemaManutencao(
                instancia,
                semente=1,
                tipo_vizinhanca=tipo_vizinhanca,
            )

            for _ in range(5):
                solucao = problema.gerar_solucao_aleatoria()
                estado = problema.construir_estado(solucao)

                # O estado deve terminar com o custo completo da própria solução
                assert estado.custos_acumulados[-1] == calcular_atraso_ponderado_total(
                    instancia,
                    solucao,
                )

                if nome_instancia == "pequena":
                    sucessores = list(problema.gerar_sucessores(solucao))
                else:
                    sucessores = [
                        problema.gerar_sucessor_aleatorio(solucao)
                        for _ in range(300)
                    ]

                for sucessor in sucessores:
                    assert problema.avaliar_sucessor(
                        estado,
                        sucessor,
                    ) == calcular_atraso_ponderado_total(
                        instancia,
                        sucessor,
                    )

# ------------------------------------------------------------------------

def teste18_avaliar_sucessor_conta_uma_avaliacao_e_construir_estado_nao_conta():
    """Verifica a contagem de avaliações da avaliação incremental."""
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )
    solucao = problema.gerar_solucao_aleatoria()

    estado = problema.construir_estado(solucao)
    assert problema.quantidade_avaliacoes == 0

    for _ in range(7):
        problema.avaliar_sucessor(
            estado,
            problema.gerar_sucessor_aleatorio(solucao),
        )
    assert problema.quantidade_avaliacoes == 7

# ------------------------------------------------------------------------

def teste19_simulated_annealing_respeita_orcamento_exato():
    """Verifica se o simulated annealing para exatamente ao atingir o orçamento."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")
    problema = ProblemaManutencao(instancia, semente=1)

    resultado = executar_simulated_annealing(problema, 5000)

    assert resultado.quantidade_avaliacoes_utilizadas == 5000
    assert problema.quantidade_avaliacoes == 5000

# ------------------------------------------------------------------------

def teste20_simulated_annealing_resultado_e_consistente():
    """Verifica solução, custo e histórico de convergência do simulated annealing."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")
    problema = ProblemaManutencao(instancia, semente=2)

    resultado = executar_simulated_annealing(problema, 5000)

    # A melhor solução deve ser uma permutação válida dos ativos
    assert sorted(resultado.melhor_solucao) == list(range(1, 13))

    # O custo informado deve coincidir com o recalculado do zero
    assert resultado.melhor_custo == calcular_atraso_ponderado_total(
        instancia,
        resultado.melhor_solucao,
    )

    # O histórico deve ter avaliações crescentes e custos decrescentes
    historico = resultado.historico_convergencia
    for (avaliacoes_antes, custo_antes), (avaliacoes_depois, custo_depois) in zip(
        historico,
        historico[1:],
    ):
        assert avaliacoes_antes < avaliacoes_depois
        assert custo_antes > custo_depois

# ------------------------------------------------------------------------

def teste21_simulated_annealing_garante_vizinhanca_de_inversao():
    """Verifica se o simulated annealing utiliza obrigatoriamente vizinhança de inversão."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")
    # Inicializa com troca propositalmente
    problema = ProblemaManutencao(instancia, semente=1, tipo_vizinhanca=TROCA)

    executar_simulated_annealing(problema, 100)

    # O algoritmo deve ter ajustado para inversão
    assert problema.tipo_vizinhanca == INVERSAO

# ------------------------------------------------------------------------

def teste22_simulated_annealing_temperatura_alta_aceita_quase_todas_pioras():
    """Com temperatura muito alta, comporta-se como random walk aceitando pioras."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")
    problema = ProblemaManutencao(instancia, semente=3)

    # Temperatura extrema: e^(-Δh / T) ≈ 1
    resultado = executar_simulated_annealing(
        problema,
        1000,
        temperatura_inicial=1e9,
        temperatura_final=1e8,
    )

    assert resultado.quantidade_piores_gerados > 0
    taxa_aceite_piores = (
        resultado.quantidade_piores_aceitos / resultado.quantidade_piores_gerados
    )
    # Deve aceitar praticamente 100% dos movimentos piores
    assert taxa_aceite_piores >= 0.98

# ------------------------------------------------------------------------

def teste23_simulated_annealing_temperatura_baixa_rejeita_pioras():
    """Com temperatura próxima de zero, não aceita nenhum movimento pior."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")
    problema = ProblemaManutencao(instancia, semente=4)

    # Temperatura minúscula: e^(-Δh / T) ≈ 0
    resultado = executar_simulated_annealing(
        problema,
        1000,
        temperatura_inicial=1e-6,
        temperatura_final=1e-7,
    )

    assert resultado.quantidade_piores_gerados > 0
    # Nenhuma piora deve ser aceita
    assert resultado.quantidade_piores_aceitos == 0

# ------------------------------------------------------------------------

def teste24_simulated_annealing_taxa_aceitacao_decresce_ao_longo_da_tempera():
    """Verifica se a taxa de aceitação decresce do início até o final da têmpera."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")
    problema = ProblemaManutencao(instancia, semente=5)

    resultado = executar_simulated_annealing(
        problema,
        15000,
        tamanho_janela_taxa=1000,
    )

    assert len(resultado.historico_taxa_aceitacao) >= 3

    # Taxa nas primeiras janelas versus nas últimas
    taxa_inicial = resultado.historico_taxa_aceitacao[0][2]
    taxa_final = resultado.historico_taxa_aceitacao[-1][2]

    # No início aceita a grande maioria das pioras (~70-80%), no final quase nada (< 5%)
    assert taxa_inicial > 0.60
    assert taxa_final < 0.05
    assert taxa_inicial > taxa_final

# ------------------------------------------------------------------------

def teste25_simulated_annealing_reprodutibilidade_com_mesma_semente():
    """Verifica se duas execuções com a mesma semente geram exatamente o mesmo resultado."""
    instancia = ler_instancia("instancias/manutencao_pequena.txt")

    problema_1 = ProblemaManutencao(instancia, semente=42)
    resultado_1 = executar_simulated_annealing(problema_1, 5000)

    problema_2 = ProblemaManutencao(instancia, semente=42)
    resultado_2 = executar_simulated_annealing(problema_2, 5000)

    assert resultado_1.melhor_solucao == resultado_2.melhor_solucao
    assert resultado_1.melhor_custo == resultado_2.melhor_custo
    assert resultado_1.historico_convergencia == resultado_2.historico_convergencia
    assert resultado_1.quantidade_movimentos_aceitos == resultado_2.quantidade_movimentos_aceitos

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
    teste11_operadores_reproduzem_os_exemplos_da_figura_3()
    teste12_tamanho_das_vizinhancas_confere_com_o_relatorio()
    teste13_sucessores_sao_permutacoes_validas_e_diferentes_da_original()
    teste14_sucessor_aleatorio_pertence_a_vizinhanca_e_a_cobre_toda()
    teste15_tipo_de_vizinhanca_desconhecido_gera_erro()
    teste16_primeira_posicao_alterada_esta_correta()
    teste17_avaliacao_incremental_coincide_com_avaliacao_completa()
    teste18_avaliar_sucessor_conta_uma_avaliacao_e_construir_estado_nao_conta()
    teste19_simulated_annealing_respeita_orcamento_exato()
    teste20_simulated_annealing_resultado_e_consistente()
    teste21_simulated_annealing_garante_vizinhanca_de_inversao()
    teste22_simulated_annealing_temperatura_alta_aceita_quase_todas_pioras()
    teste23_simulated_annealing_temperatura_baixa_rejeita_pioras()
    teste24_simulated_annealing_taxa_aceitacao_decresce_ao_longo_da_tempera()
    teste25_simulated_annealing_reprodutibilidade_com_mesma_semente()

    print("Todos os testes passaram.") # Se algum falhar, não será impresso
