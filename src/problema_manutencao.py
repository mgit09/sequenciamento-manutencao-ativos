"""
Modelo do problema de sequenciamento de manutenção de ativos.

Reúne tudo o que é específico do problema: leitura das instâncias,
tempos de deslocamento e função de avaliação (atraso ponderado total).
Os algoritmos de busca usarão este módulo sem conhecer os detalhes dele.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Instancia:
    quantidade_ativos: int

    # Os vetores abaixo têm tamanho n+1: o índice 0 representa a base
    # (com duração 0) e os índices 1..n representam os ativos
    duracoes_servico: np.ndarray
    prazos: np.ndarray
    pesos_criticidade: np.ndarray

    # Matriz (n+1)x(n+1) com o tempo de deslocamento entre cada par de pontos
    tempos_deslocamento: np.ndarray


def ler_instancia(caminho_arquivo) -> Instancia:
    """
    Lê um arquivo de instância e monta os dados do problema.

    O arquivo contém a quantidade de ativos, as coordenadas da base
    e os dados de cada ativo. Os tempos de deslocamento são calculados
    a partir das coordenadas usando a distância euclidiana arredondada.
    """
    linhas = [
        linha.split()
        for linha in Path(caminho_arquivo)
        .read_text()
        .strip()
        .splitlines()
    ]

    quantidade_ativos = int(linhas[0][0])
    coordenadas_base = [float(valor) for valor in linhas[1]]

    # Extrai os dados de cada ativo, convertendo os valores para números
    linhas_ativos = [
        [float(valor) for valor in linha]
        for linha in linhas[2:2 + quantidade_ativos]
    ]

    assert len(linhas_ativos) == quantidade_ativos, (
        "Número de linhas de ativos diferente de n"
    )

    # Separa as coordenadas dos ativos das demais informações de cada linha
    coordenadas_ativos = [linha[0:2] for linha in linhas_ativos]
    coordenadas = np.array([coordenadas_base] + coordenadas_ativos)

    # O índice 0 representa a base; os índices seguintes representam os ativos
    duracoes_servico = np.array(
        [0] + [linha[2] for linha in linhas_ativos],
        dtype=np.int64,
    )
    prazos = np.array(
        [0] + [linha[3] for linha in linhas_ativos],
        dtype=np.int64,
    )
    pesos_criticidade = np.array(
        [0] + [linha[4] for linha in linhas_ativos],
        dtype=np.int64,
    )

    # Equação (1) do enunciado: distância euclidiana arredondada
    diferencas = coordenadas[:, None, :] - coordenadas[None, :, :]

    # Calcula as dist. euclidianas e arredonda cada uma pro int mais próximo
    distancias = np.sqrt((diferencas ** 2).sum(axis=2))
    tempos_deslocamento = np.rint(distancias).astype(np.int64)

    return Instancia(
        quantidade_ativos,
        duracoes_servico,
        prazos,
        pesos_criticidade,
        tempos_deslocamento,
    )


def calcular_atraso_ponderado_total(instancia: Instancia, sequencia_de_visita) -> int:
    """
    Função de avaliação h(π), equações (2) e (3) do enunciado.
    A sequência contém os ativos numerados de 1 a n; a equipe parte da base.
    """
    instante_atual = 0
    ativo_anterior = 0  # A equipe começa na base, que é o ponto de índice 0
    atraso_ponderado_total = 0

    for ativo in sequencia_de_visita:
        instante_atual += instancia.tempos_deslocamento[ativo_anterior, ativo]
        instante_atual += instancia.duracoes_servico[ativo]
        atraso = instante_atual - instancia.prazos[ativo]

        if atraso > 0:
            atraso_ponderado_total += instancia.pesos_criticidade[ativo] * atraso

        ativo_anterior = ativo

    return int(atraso_ponderado_total)