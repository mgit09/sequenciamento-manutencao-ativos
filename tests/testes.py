"""
Testes automáticos do projeto. Execute no terminal com o seguinte comando: 

python testes.py
"""

from src.problema_manutencao import (
    ler_instancia, 
    calcular_atraso_ponderado_total
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


if __name__ == "__main__":
    teste_sequencia_identidade_instancia_pequena()
    print("Todos os testes passaram.")