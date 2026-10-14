"""
Mede o ganho de tempo da avaliação incremental sobre a avaliação completa.

Para cada instância e cada tipo de vizinhança, avalia todos os sucessores de
uma mesma solução aleatória das duas formas e compara os tempos de parede.
O número de avaliações é o mesmo nas duas; só o tempo muda.

Uso, a partir da raiz do projeto:

python -m scripts.medir_avaliacao_incremental
"""

import argparse
import time
from pathlib import Path

import pandas as pd

from src.problema_manutencao import TIPOS_VIZINHANCA, ProblemaManutencao, ler_instancia

# ========================================================================
# CONFIGURAÇÕES
CAMINHOS_INSTANCIAS = {
    "pequena": "instancias/manutencao_pequena.txt",
    "media": "instancias/manutencao_media.txt",
    "grande": "instancias/manutencao_grande.txt",
}

# Cada medição é repetida e fica o menor tempo, 
# o menos afetado por ruídos do computador
QUANTIDADE_REPETICOES = 5

# ========================================================================

def medir_vizinhanca(
    nome_instancia: str,
    tipo_vizinhanca: str,
) -> dict:
    """
    Mede os tempos das duas avaliações sobre toda a vizinhança de uma solução.
    """
    instancia = ler_instancia(CAMINHOS_INSTANCIAS[nome_instancia])
    problema = ProblemaManutencao(
        instancia,
        semente=0,
        tipo_vizinhanca=tipo_vizinhanca,
    )

    solucao = problema.gerar_solucao_aleatoria()
    estado = problema.construir_estado(solucao)

    # Os sucessores são gerados antes de medir, para cronometrar só a avaliação
    sucessores = list(problema.gerar_sucessores(solucao))

    tempos_avaliacao_completa = []
    tempos_avaliacao_incremental = []

    for _ in range(QUANTIDADE_REPETICOES):
        inicio = time.perf_counter()
        custos_completa = [problema.avaliar(sucessor) for sucessor in sucessores]
        tempos_avaliacao_completa.append(time.perf_counter() - inicio)

        inicio = time.perf_counter()
        custos_incremental = [
            problema.avaliar_sucessor(estado, sucessor)
            for sucessor in sucessores
        ]
        tempos_avaliacao_incremental.append(time.perf_counter() - inicio)

        # Os dois métodos devem produzir exatamente os mesmos custos
        assert custos_completa == custos_incremental

    tempo_completa = min(tempos_avaliacao_completa)
    tempo_incremental = min(tempos_avaliacao_incremental)
    quantidade_sucessores = len(sucessores)

    return {
        "instancia": nome_instancia,
        "vizinhanca": tipo_vizinhanca,
        "quantidade_sucessores": quantidade_sucessores,
        "tempo_completa_segundos": tempo_completa,
        "tempo_incremental_segundos": tempo_incremental,
        "microssegundos_por_movimento_completa": 1e6 * tempo_completa / quantidade_sucessores,
        "microssegundos_por_movimento_incremental": 1e6 * tempo_incremental / quantidade_sucessores,
        "ganho": tempo_completa / tempo_incremental,
    }

# ========================================================================
# EXECUÇÃO PRINCIPAL

def main():
    """
    Mede todas as instâncias e vizinhanças, imprime a tabela e salva em *.csv.
    """
    leitor = argparse.ArgumentParser(
        description="Mede o ganho de tempo da avaliação incremental.",
    )
    leitor.add_argument(
        "--pasta-saida",
        default="resultados",
        help="pasta onde o .csv será gravado (padrão: resultados)",
    )
    argumentos = leitor.parse_args()

    linhas = []
    for nome_instancia in CAMINHOS_INSTANCIAS:
        for tipo_vizinhanca in TIPOS_VIZINHANCA:
            linhas.append(medir_vizinhanca(nome_instancia, tipo_vizinhanca))

    tabela = pd.DataFrame(linhas)
    print(tabela.round(3).to_string(index=False))

    pasta_saida = Path(argumentos.pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(pasta_saida / "tempo_avaliacao_incremental.csv", index=False)


if __name__ == "__main__":
    main()
