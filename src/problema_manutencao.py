"""
Modelo do problema de sequenciamento de manutenção de ativos.

Reúne tudo o que é específico do problema: leitura das instâncias,
tempos de deslocamento e função de avaliação (atraso ponderado total).
Os algoritmos de busca usarão este módulo sem conhecer os detalhes dele.
"""

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterator

import numpy as np

# ========================================================================

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

# ========================================================================

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

# ========================================================================

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

# ========================================================================
# OPERADORES

# Tipos de vizinhança disponíveis para gerar sucessores
TROCA = "troca"
REALOCACAO = "realocacao"
INVERSAO = "inversao"
TIPOS_VIZINHANCA = (TROCA, REALOCACAO, INVERSAO)


def aplicar_troca(solucao, posicao_a: int, posicao_b: int) -> list[int]:
    """Devolve uma cópia da solução com os ativos das duas posições trocados."""
    sucessor = list(solucao)
    sucessor[posicao_a], sucessor[posicao_b] = (
        sucessor[posicao_b],
        sucessor[posicao_a],
    )
    return sucessor

# ------------------------------------------------------------------------

def aplicar_realocacao(
    solucao,
    posicao_origem: int,
    posicao_destino: int,
) -> list[int]:
    """
    Devolve uma cópia da solução com um ativo realocado.

    O ativo é removido da posição de origem e reinserido de modo a
    ocupar a posição de destino na nova sequência.
    """
    sucessor = list(solucao)
    ativo = sucessor.pop(posicao_origem)
    sucessor.insert(posicao_destino, ativo)

    return sucessor

# ------------------------------------------------------------------------

def aplicar_inversao(
    solucao,
    posicao_inicial: int,
    posicao_final: int,
) -> list[int]:
    """
    Devolve uma cópia da solução com o trecho entre as 
    duas posições invertido.
    """
    sucessor = list(solucao)
    trecho = sucessor[posicao_inicial:posicao_final + 1]
    sucessor[posicao_inicial:posicao_final + 1] = trecho[::-1]

    return sucessor

# ========================================================================

class Sucessor(list):
    """
    Sequência de visita obtida por um movimento a partir de outra solução.

    Comporta-se como uma lista comum, mas também guarda a primeira posição
    em que difere da solução de origem, o que permite a avaliação incremental.
    """

    def __init__(self, sequencia, primeira_posicao_alterada: int):
        """
        Cria o sucessor a partir da sequência e da primeira posição alterada.
        """
        super().__init__(sequencia)
        self.primeira_posicao_alterada = int(primeira_posicao_alterada)


@dataclass
class EstadoSolucao:
    """
    Valores intermediários da avaliação de uma solução, 
    reaproveitados pelos sucessores.
    """
    # instantes_conclusao[k]: instante de conclusão do ativo na posição k
    instantes_conclusao: list[int]

    # custos_acumulados[k]: atraso ponderado somando as posições 0 até k
    custos_acumulados: list[int]

# ========================================================================

class ProblemaManutencao:
    """
    Interface entre os algoritmos de busca e o problema de manutenção.

    Os algoritmos só chamam os métodos desta classe, sem saber nada
    sobre ativos, prazos ou deslocamentos.
    """
    def __init__(
        self,
        instancia: Instancia,
        semente: int | None = None,
        tipo_vizinhanca: str = TROCA,
    ):
        """Prepara o problema, o gerador aleatório e o contador de avaliações."""
        if tipo_vizinhanca not in TIPOS_VIZINHANCA:
            raise ValueError(f"Tipo de vizinhança desconhecido: {tipo_vizinhanca}")

        self.instancia = instancia
        self.tipo_vizinhanca = tipo_vizinhanca
        self.gerador_aleatorio = np.random.default_rng(semente)
        self.quantidade_avaliacoes = 0

    # --------------------------------------------------------------------
    def gerar_solucao_aleatoria(self) -> list[int]:
        """
        Sorteia uma sequência de visita qualquer 
        (permutação dos ativos 1..n).
        """
        ativos = np.arange(1, self.instancia.quantidade_ativos + 1)

        return self.gerador_aleatorio.permutation(ativos).tolist()

    # --------------------------------------------------------------------
    def avaliar(self, sequencia_de_visita) -> int:
        """Calcula h(π) e conta uma avaliação do orçamento."""
        self.quantidade_avaliacoes += 1
        return calcular_atraso_ponderado_total(
            self.instancia,
            sequencia_de_visita,
        )

    # --------------------------------------------------------------------
    def zerar_contador_avaliacoes(self):
        """Zera o contador de avaliações."""
        self.quantidade_avaliacoes = 0

    # --------------------------------------------------------------------
    def construir_estado(self, sequencia_de_visita) -> EstadoSolucao:
        """
        Calcula os valores intermediários da avaliação de uma solução.

        Não conta como avaliação: serve apenas para preparar a avaliação
        incremental dos sucessores de uma solução cujo custo já foi avaliado.
        """
        tempos_deslocamento = self.instancia.tempos_deslocamento
        duracoes_servico = self.instancia.duracoes_servico
        prazos = self.instancia.prazos
        pesos_criticidade = self.instancia.pesos_criticidade

        instante_atual = 0
        ativo_anterior = 0  # a equipe começa na base, que é o ponto de índice 0
        custo_acumulado = 0
        instantes_conclusao = []
        custos_acumulados = []

        for ativo in sequencia_de_visita:
            instante_atual += tempos_deslocamento[ativo_anterior, ativo]
            instante_atual += duracoes_servico[ativo]

            atraso = instante_atual - prazos[ativo]
            if atraso > 0:
                custo_acumulado += pesos_criticidade[ativo] * atraso

            instantes_conclusao.append(int(instante_atual))
            custos_acumulados.append(int(custo_acumulado))
            ativo_anterior = ativo

        return EstadoSolucao(instantes_conclusao, custos_acumulados)

    # --------------------------------------------------------------------
    def avaliar_sucessor(
        self,
        estado_solucao_origem: EstadoSolucao,
        sucessor: Sucessor,
    ) -> int:
        """
        Calcula h(π) de um sucessor reaproveitando o prefixo da solução de origem.

        As posições anteriores à primeira alterada têm os mesmos instantes de
        conclusão e o mesmo custo da solução de origem, então só o restante da
        sequência é recalculado. Conta uma avaliação do orçamento, como `avaliar`.
        """
        self.quantidade_avaliacoes += 1

        tempos_deslocamento = self.instancia.tempos_deslocamento
        duracoes_servico = self.instancia.duracoes_servico
        prazos = self.instancia.prazos
        pesos_criticidade = self.instancia.pesos_criticidade

        primeira_posicao = sucessor.primeira_posicao_alterada

        # Retoma o cálculo do ponto em que o prefixo inalterado termina
        if primeira_posicao == 0:
            instante_atual = 0
            custo_acumulado = 0
            ativo_anterior = 0  # base
        else:
            instante_atual = estado_solucao_origem.instantes_conclusao[primeira_posicao - 1]
            custo_acumulado = estado_solucao_origem.custos_acumulados[primeira_posicao - 1]
            ativo_anterior = sucessor[primeira_posicao - 1]

        # Recalcula apenas o trecho a partir da primeira posição alterada
        for ativo in sucessor[primeira_posicao:]:
            instante_atual += tempos_deslocamento[ativo_anterior, ativo]
            instante_atual += duracoes_servico[ativo]

            atraso = instante_atual - prazos[ativo]
            if atraso > 0:
                custo_acumulado += pesos_criticidade[ativo] * atraso

            ativo_anterior = ativo

        return int(custo_acumulado)

    # --------------------------------------------------------------------
    def gerar_sucessores(self, solucao) -> Iterator[list[int]]:
        """
        Gera, um de cada vez, todos os sucessores de uma solução.

        Os sucessores dependem do tipo de vizinhança escolhido.
        A solução original não é modificada.
        """
        if self.tipo_vizinhanca == TROCA:
            return self._gerar_sucessores_por_troca(solucao)
        
        if self.tipo_vizinhanca == REALOCACAO:
            return self._gerar_sucessores_por_realocacao(solucao)
        
        return self._gerar_sucessores_por_inversao(solucao)

    # --------------------------------------------------------------------
    def gerar_sucessor_aleatorio(self, solucao) -> list[int]:
        """
        Sorteia um único sucessor de uma solução.

        O sorteio é uniforme entre os sucessores da vizinhança escolhida.
        A solução original não é modificada.
        """
        if self.tipo_vizinhanca == TROCA:
            return self._gerar_sucessor_aleatorio_por_troca(solucao)
        
        if self.tipo_vizinhanca == REALOCACAO:
            return self._gerar_sucessor_aleatorio_por_realocacao(solucao)
        
        return self._gerar_sucessor_aleatorio_por_inversao(solucao)

    # --------------------------------------------------------------------
    def _gerar_sucessores_por_troca(self, solucao) -> Iterator[list[int]]:
        """Gera os n(n-1)/2 sucessores obtidos trocando dois ativos de lugar."""
        quantidade_ativos = len(solucao)

        for posicao_a in range(quantidade_ativos - 1):
            for posicao_b in range(posicao_a + 1, quantidade_ativos):
                yield Sucessor(
                    aplicar_troca(solucao, posicao_a, posicao_b),
                    primeira_posicao_alterada=posicao_a,
                )

    # --------------------------------------------------------------------
    def _gerar_sucessores_por_realocacao(self, solucao) -> Iterator[list[int]]:
        """Gera os (n-1)^2 sucessores distintos obtidos realocando um ativo."""
        quantidade_ativos = len(solucao)

        for posicao_origem in range(quantidade_ativos):
            for posicao_destino in range(quantidade_ativos):
                if posicao_destino == posicao_origem:
                    continue

                # Mover um ativo uma posição à frente equivale a mover o seguinte
                # uma posição atrás, então um dos dois movimentos é descartado
                if posicao_destino == posicao_origem + 1:
                    continue

                yield Sucessor(
                    aplicar_realocacao(solucao, posicao_origem, posicao_destino),
                    primeira_posicao_alterada=min(posicao_origem, posicao_destino),
                )

    # --------------------------------------------------------------------
    def _gerar_sucessores_por_inversao(self, solucao) -> Iterator[list[int]]:
        """Gera os n(n-1)/2 sucessores obtidos invertendo um trecho da sequência."""
        quantidade_ativos = len(solucao)

        for posicao_inicial in range(quantidade_ativos - 1):
            for posicao_final in range(posicao_inicial + 1, quantidade_ativos):
                yield Sucessor(
                    aplicar_inversao(solucao, posicao_inicial, posicao_final),
                    primeira_posicao_alterada=posicao_inicial,
                )

    # --------------------------------------------------------------------
    def _gerar_sucessor_aleatorio_por_troca(self, solucao) -> list[int]:
        """Sorteia dois ativos diferentes e os troca de lugar."""
        posicao_a, posicao_b = self.gerador_aleatorio.choice(
            len(solucao),
            size=2,
            replace=False,
        )
        return Sucessor(
            aplicar_troca(solucao, posicao_a, posicao_b),
            primeira_posicao_alterada=min(posicao_a, posicao_b),
        )

    # --------------------------------------------------------------------
    def _gerar_sucessor_aleatorio_por_realocacao(self, solucao) -> list[int]:
        """Sorteia um ativo e uma nova posição para ele."""
        while True:
            posicao_origem, posicao_destino = self.gerador_aleatorio.choice(
                len(solucao),
                size=2,
                replace=False,
            )

            # Descarta o movimento redundante 
            # (mesma regra de _gerar_sucessores_por_realocacao)
            if posicao_destino != posicao_origem + 1:
                return Sucessor(
                    aplicar_realocacao(solucao, posicao_origem, posicao_destino),
                    primeira_posicao_alterada=min(posicao_origem, posicao_destino),
                )

    # --------------------------------------------------------------------
    def _gerar_sucessor_aleatorio_por_inversao(self, solucao) -> list[int]:
        """Sorteia dois extremos e inverte o trecho entre eles."""
        posicao_a, posicao_b = self.gerador_aleatorio.choice(
            len(solucao),
            size=2,
            replace=False,
        )
        
        posicao_inicial = min(posicao_a, posicao_b)
        posicao_final = max(posicao_a, posicao_b)

        return Sucessor(
            aplicar_inversao(solucao, posicao_inicial, posicao_final),
            primeira_posicao_alterada=posicao_inicial,
        )
