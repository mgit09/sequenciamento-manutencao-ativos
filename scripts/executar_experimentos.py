"""
Executa os experimentos do trabalho e salva os resultados em arquivos *.csv.

Para cada instância e cada algoritmo, roda as execuções independentes
definidas no protocolo (orçamento de avaliações e número de execuções)
e grava, na pasta de resultados:

- resumo_execucoes_<instancia>.csv: uma linha por execução
- convergencia_<instancia>.csv: evolução do melhor custo ao longo das avaliações

Exemplos de uso, a partir da raiz do projeto:

python -m scripts.executar_experimentos
python -m scripts.executar_experimentos --instancias pequena
"""

import argparse
import time
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path

import pandas as pd

from src.algoritmos.alg_desc_gulosa import (
    MELHOR_MELHORIA,
    PRIMEIRA_MELHORIA,
    executar_descida_gulosa,
)
from src.problema_manutencao import (
    ProblemaManutencao, 
    ler_instancia
)

# ========================================================================
# CONFIGURAÇÕES

@dataclass
class ConfiguracaoInstancia:
    """Arquivo e parâmetros do protocolo experimental de uma instância."""
    caminho_arquivo: str
    orcamento_avaliacoes: int
    quantidade_execucoes: int


# Orçamentos e números de execuções definidos na Seção 3 do enunciado
CONFIGURACOES_INSTANCIAS = {
    "pequena": ConfiguracaoInstancia(
        caminho_arquivo="instancias/manutencao_pequena.txt",
        orcamento_avaliacoes=50_000,
        quantidade_execucoes=30,
    ),
    "media": ConfiguracaoInstancia(
        caminho_arquivo="instancias/manutencao_media.txt",
        orcamento_avaliacoes=150_000,
        quantidade_execucoes=30,
    ),
    "grande": ConfiguracaoInstancia(
        caminho_arquivo="instancias/manutencao_grande.txt",
        orcamento_avaliacoes=300_000,
        quantidade_execucoes=10,
    ),
}

# Cada algoritmo é uma função que recebe (problema, orcamento_avaliacoes)
ALGORITMOS = {
    "descida_gulosa_melhor_melhoria": partial(
        executar_descida_gulosa,
        variante=MELHOR_MELHORIA,
    ),
    "descida_gulosa_primeira_melhoria": partial(
        executar_descida_gulosa,
        variante=PRIMEIRA_MELHORIA,
    ),
}

# ========================================================================

def executar_instancia(
    nome_instancia: str,
    configuracao: ConfiguracaoInstancia,
    pasta_saida: Path,
):
    """Roda todos os algoritmos numa instância e salva os resultados em .csv."""
    instancia = ler_instancia(configuracao.caminho_arquivo)

    caminho_resumo = pasta_saida / f"resumo_execucoes_{nome_instancia}.csv"
    caminho_convergencia = pasta_saida / f"convergencia_{nome_instancia}.csv"

    linhas_resumo = []
    linhas_convergencia = []

    for nome_algoritmo, executar_algoritmo in ALGORITMOS.items():

        for semente in range(configuracao.quantidade_execucoes):

            # A semente é o número da execução, o que torna tudo reprodutível
            problema = ProblemaManutencao(
                instancia,
                semente=semente,
            )

            inicio = time.perf_counter()
            resultado = executar_algoritmo(
                problema,
                configuracao.orcamento_avaliacoes,
            )
            tempo_segundos = time.perf_counter() - inicio

            linhas_resumo.append(
                {
                    "instancia": nome_instancia,
                    "algoritmo": nome_algoritmo,
                    "semente": semente,
                    "melhor_custo": resultado.melhor_custo,
                    "avaliacoes_utilizadas": resultado.quantidade_avaliacoes_utilizadas,
                    "tempo_segundos": tempo_segundos,
                    "melhor_solucao": " ".join(map(str, resultado.melhor_solucao)),
                    **resultado.obter_metricas_adicionais(),
                }
            )

            for avaliacoes, melhor_custo in resultado.historico_convergencia:
                linhas_convergencia.append(
                    {
                        "instancia": nome_instancia,
                        "algoritmo": nome_algoritmo,
                        "semente": semente,
                        "avaliacoes": avaliacoes,
                        "melhor_custo": melhor_custo,
                    }
                )

            # Regrava os arquivos a cada execução para não perder dados se algo falhar
            pd.DataFrame(linhas_resumo).to_csv(caminho_resumo, index=False)
            pd.DataFrame(linhas_convergencia).to_csv(caminho_convergencia, index=False)

            print(
                f"{nome_instancia} | {nome_algoritmo} | "
                f"execução {semente + 1}/{configuracao.quantidade_execucoes} | "
                f"melhor custo {resultado.melhor_custo} | {tempo_segundos:.2f} s"
            )

# ========================================================================

def ler_argumentos() -> argparse.Namespace:
    """Lê as opções passadas na linha de comando."""
    leitor = argparse.ArgumentParser(
        description="Executa os experimentos e salva os resultados em .csv.",
    )
    leitor.add_argument(
        "--instancias",
        nargs="+",
        choices=list(CONFIGURACOES_INSTANCIAS),
        default=list(CONFIGURACOES_INSTANCIAS),
        help="instâncias a executar (padrão: todas)",
    )
    leitor.add_argument(
        "--execucoes",
        type=int,
        default=None,
        help="substitui o número de execuções do protocolo (útil para testes rápidos)",
    )
    leitor.add_argument(
        "--orcamento",
        type=int,
        default=None,
        help="substitui o orçamento de avaliações do protocolo (útil para testes rápidos)",
    )
    leitor.add_argument(
        "--pasta-saida",
        default="resultados",
        help="pasta onde os .csv serão gravados (padrão: resultados)",
    )
    return leitor.parse_args()

# ========================================================================
# EXECUÇÃO PRINCIPAL

def main():
    """Executa os experimentos conforme as opções da linha de comando."""
    argumentos = ler_argumentos()

    pasta_saida = Path(argumentos.pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    for nome_instancia in argumentos.instancias:
        configuracao = CONFIGURACOES_INSTANCIAS[nome_instancia]

        if argumentos.execucoes is not None:
            configuracao = replace(
                configuracao,
                quantidade_execucoes=argumentos.execucoes,
            )
        
        if argumentos.orcamento is not None:
            configuracao = replace(
                configuracao,
                orcamento_avaliacoes=argumentos.orcamento,
            )

        executar_instancia(
            nome_instancia,
            configuracao,
            pasta_saida,
        )


if __name__ == "__main__":
    main()
