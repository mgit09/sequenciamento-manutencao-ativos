"""
Testes automáticos do projeto. Da raiz do projeto, execute no terminal o seguinte comando: 

python -m tests.testes
"""

from src.problema_manutencao import (
    ler_instancia, 
    calcular_atraso_ponderado_total,
    ProblemaManutencao,
)


def teste_sequencia_identidade_instancia_pequena():
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


def teste_solucao_aleatoria_e_permutacao_valida():
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )

    for _ in range(100):
        solucao = problema.gerar_solucao_aleatoria()

        # Toda solução deve conter cada ativo de 1 a 12 exatamente uma vez
        assert sorted(solucao) == list(range(1, 13))


def teste_mesma_semente_gera_mesma_solucao():
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


def teste_contador_conta_cada_avaliacao():
    problema = ProblemaManutencao(
        ler_instancia("instancias/manutencao_pequena.txt"),
        semente=1,
    )

    for _ in range(5):
        problema.avaliar(problema.gerar_solucao_aleatoria())

    assert problema.quantidade_avaliacoes == 5

    problema.zerar_contador_avaliacoes()
    assert problema.quantidade_avaliacoes == 0


if __name__ == "__main__":
    teste_sequencia_identidade_instancia_pequena()
    print("Todos os testes passaram.")