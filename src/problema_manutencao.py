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
    """
    Armazena os dados de uma instância do problema de manutenção.
    O índice 0 representa a base, e os índices 1..n representam os ativos.
    """
    quantidade_ativos: int

    # Os vetores abaixo têm tamanho n+1
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


class ProblemaManutencao:
    """
    Interface entre os algoritmos de busca e o problema de manutenção.

    Os algoritmos só chamam os métodos desta classe, sem saber nada
    sobre ativos, prazos ou deslocamentos.
    """

    def __init__(self, instancia: Instancia, semente: int | None = None):
        """Construtor da classe."""
        self.instancia = instancia
        self.gerador_aleatorio = np.random.default_rng(semente)
        self.quantidade_avaliacoes = 0

    def gerar_solucao_aleatoria(self) -> list[int]:
        """Sorteia uma sequência de visita qualquer (permutação dos ativos 1..n)."""
        ativos = np.arange(1, self.instancia.quantidade_ativos + 1)
        return self.gerador_aleatorio.permutation(ativos).tolist()

    def avaliar(self, sequencia_de_visita) -> int:
        """Calcula h(π) e conta uma avaliação do orçamento."""
        self.quantidade_avaliacoes += 1
        return calcular_atraso_ponderado_total(self.instancia, sequencia_de_visita)

    def zerar_contador_avaliacoes(self):
        """Zera o contador de avaliações."""
        self.quantidade_avaliacoes = 0
