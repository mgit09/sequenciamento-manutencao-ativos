"""
Compara os três operadores de vizinhança (Troca, Realocação e Inversão)
utilizando Descida Gulosa com Reinício Aleatório (Tarefa T2 do trabalho).

Avalia o desempenho de cada vizinhança nas três instâncias (pequena, média
e grande) sob o mesmo orçamento de avaliações, registrando:
- Custo mínimo, médio e desvio-padrão de h(π)
- Quantidade de passos de melhoria realizados dentro do orçamento
- Quantidade total e distinta de ótimos locais visitados
- Tempo de execução de parede

Os resultados são consolidados e gravados em 
resultados/tabela_comparacao_vizinhancas.csv.

Exemplo de uso, a partir da raiz do projeto:
python -m scripts.comparar_vizinhancas
"""

import argparse
import time
from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd

from src.algoritmos.alg_desc_gulosa import (
    MELHOR_MELHORIA,
    PRIMEIRA_MELHORIA,
    executar_descida_gulosa,
)
from src.problema_manutencao import (
    INVERSAO,
    REALOCACAO,
    TIPOS_VIZINHANCA,
    TROCA,
    ProblemaManutencao,
    ler_instancia,
)

# ========================================================================
# CONFIGURAÇÕES DO PROTOCOLO EXPERIMENTAL

@dataclass
class ConfiguracaoInstancia:
    """Arquivo e parâmetros de orçamento/execuções de uma instância."""
    caminho_arquivo: str
    orcamento_avaliacoes: int
    quantidade_execucoes: int


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

# ========================================================================

def executar_comparacao(
    instancias: list[str],
    vizinhancas: list[str],
    variante: str,
    configuracoes: dict[str, ConfiguracaoInstancia],
    pasta_saida: Path,
):
    """
    Roda a descida gulosa variando vizinhanças e instâncias,
    salvando os resultados e exibindo a tabela consolidada.
    """
    caminho_tabela = pasta_saida / "tabela_comparacao_vizinhancas.csv"

    linhas_brutas = []
    total_combinacoes = len(instancias) * len(vizinhancas)
    combinacao_atual = 0

    print("=" * 80)
    print("INICIANDO EXPERIMENTO DA TAREFA T2: COMPARAÇÃO DAS VIZINHANÇAS")
    print(f"Variante da Descida Gulosa: {variante}")
    print(f"Vizinhanças avaliadas: {', '.join(vizinhancas)}")
    print("=" * 80)

    for nome_instancia in instancias:
        configuracao = configuracoes[nome_instancia]
        instancia = ler_instancia(configuracao.caminho_arquivo)

        for tipo_vizinhanca in vizinhancas:
            combinacao_atual += 1
            print(
                f"\n[{combinacao_atual}/{total_combinacoes}] "
                f"Instância: {nome_instancia} | Vizinhança: {tipo_vizinhanca} | "
                f"Orçamento: {configuracao.orcamento_avaliacoes:,} avaliações | "
                f"{configuracao.quantidade_execucoes} execuções..."
            )

            for semente in range(configuracao.quantidade_execucoes):
                problema = ProblemaManutencao(
                    instancia,
                    semente=semente,
                    tipo_vizinhanca=tipo_vizinhanca,
                )

                inicio = time.perf_counter()
                resultado = executar_descida_gulosa(
                    problema,
                    configuracao.orcamento_avaliacoes,
                    variante=variante,
                )
                tempo_segundos = time.perf_counter() - inicio

                metricas_adicionais = resultado.obter_metricas_adicionais()

                linhas_brutas.append(
                    {
                        "instancia": nome_instancia,
                        "vizinhanca": tipo_vizinhanca,
                        "variante": variante,
                        "semente": semente,
                        "melhor_custo": resultado.melhor_custo,
                        "avaliacoes_utilizadas": resultado.quantidade_avaliacoes_utilizadas,
                        "tempo_segundos": tempo_segundos,
                        "passos_melhoria": metricas_adicionais.get("passos_melhoria", 0),
                        "otimos_locais": metricas_adicionais.get("otimos_locais", 0),
                        "otimos_locais_distintos": metricas_adicionais.get("otimos_locais_distintos", 0),
                    }
                )

                print(
                    f"  Exec {semente + 1:2d}/{configuracao.quantidade_execucoes:2d} | "
                    f"Melhor h: {resultado.melhor_custo:6.0f} | "
                    f"Passos: {metricas_adicionais.get('passos_melhoria', 0):4d} | "
                    f"Ótimos distintos: {metricas_adicionais.get('otimos_locais_distintos', 0):3d} | "
                    f"Tempo: {tempo_segundos:5.2f} s"
                )

            # Atualiza o arquivo da tabela resumida ao término de cada vizinhança
            df_parcial = pd.DataFrame(linhas_brutas)
            resumo_parcial = (
                df_parcial.groupby(["instancia", "vizinhanca", "variante"], sort=False)
                .agg(
                    melhor_h=("melhor_custo", "min"),
                    media_h=("melhor_custo", "mean"),
                    desvio_h=("melhor_custo", "std"),
                    mediana_h=("melhor_custo", "median"),
                    media_passos=("passos_melhoria", "mean"),
                    media_otimos_distintos=("otimos_locais_distintos", "mean"),
                    tempo_medio_s=("tempo_segundos", "mean"),
                )
                .reset_index()
            )
            resumo_parcial.to_csv(caminho_tabela, index=False)

    df = pd.DataFrame(linhas_brutas)
    resumo = (
        df.groupby(["instancia", "vizinhanca", "variante"], sort=False)
        .agg(
            melhor_h=("melhor_custo", "min"),
            media_h=("melhor_custo", "mean"),
            desvio_h=("melhor_custo", "std"),
            mediana_h=("melhor_custo", "median"),
            media_passos=("passos_melhoria", "mean"),
            media_otimos_distintos=("otimos_locais_distintos", "mean"),
            tempo_medio_s=("tempo_segundos", "mean"),
        )
        .reset_index()
    )

    resumo.to_csv(caminho_tabela, index=False)

    print("\n" + "=" * 80)
    print("RESUMO CONSOLIDADO DA COMPARAÇÃO DE VIZINHANÇAS (TAREFA T2)")
    print("=" * 80)
    print(resumo.to_string(index=False))
    print("=" * 80)
    print(f"\nTabela resumida salva em: {caminho_tabela}\n")


# ========================================================================

def ler_argumentos() -> argparse.Namespace:
    """Lê opções da linha de comando."""
    leitor = argparse.ArgumentParser(
        description="Compara as três vizinhanças usando Descida Gulosa com Reinício Aleatório (Tarefa T2).",
    )
    leitor.add_argument(
        "--instancias",
        nargs="+",
        choices=list(CONFIGURACOES_INSTANCIAS),
        default=list(CONFIGURACOES_INSTANCIAS),
        help="instâncias a executar (padrão: todas)",
    )
    leitor.add_argument(
        "--vizinhancas",
        nargs="+",
        choices=list(TIPOS_VIZINHANCA),
        default=list(TIPOS_VIZINHANCA),
        help="vizinhanças a comparar (padrão: troca, realocacao, inversao)",
    )
    leitor.add_argument(
        "--variante",
        choices=[PRIMEIRA_MELHORIA, MELHOR_MELHORIA],
        default=PRIMEIRA_MELHORIA,
        help="variante da descida gulosa (padrão: primeira_melhoria)",
    )
    leitor.add_argument(
        "--execucoes",
        type=int,
        default=None,
        help="número de execuções independentes (sobrescreve o padrão do protocolo)",
    )
    leitor.add_argument(
        "--orcamento",
        type=int,
        default=None,
        help="orçamento de avaliações (sobrescreve o padrão do protocolo)",
    )
    leitor.add_argument(
        "--pasta-saida",
        default="resultados/experimentos",
        help="pasta onde os arquivos .csv serão gravados (padrão: resultados/experimentos)",
    )
    return leitor.parse_args()


# ========================================================================
# EXECUÇÃO PRINCIPAL

def main():
    argumentos = ler_argumentos()

    pasta_saida = Path(argumentos.pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    configuracoes = {}
    for nome in argumentos.instancias:
        cfg = CONFIGURACOES_INSTANCIAS[nome]
        if argumentos.execucoes is not None:
            cfg = replace(cfg, quantidade_execucoes=argumentos.execucoes)
        if argumentos.orcamento is not None:
            cfg = replace(cfg, orcamento_avaliacoes=argumentos.orcamento)
        configuracoes[nome] = cfg

    executar_comparacao(
        instancias=argumentos.instancias,
        vizinhancas=argumentos.vizinhancas,
        variante=argumentos.variante,
        configuracoes=configuracoes,
        pasta_saida=pasta_saida,
    )


if __name__ == "__main__":
    main()

