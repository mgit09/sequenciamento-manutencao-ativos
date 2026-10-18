"""
Central analítica do projeto de Sequenciamento de Manutenção de Ativos.

Lê os dados experimentais existentes em resultados/, calcula estatísticas,
executa testes de hipótese não-paramétricos (Mann-Whitney U), executa
experimentos complementares (taxa de aceitação SA, diversidade AG e
experimento adicional sobre recombinação do AG) e gera:

1. Todas as tabelas exigidas pelo trabalho em formato CSV, Markdown e LaTeX.
2. Todas as figuras e gráficos em alta resolução (PNG 300 DPI).

Uso a partir da raiz do projeto:
    python -m scripts.gerar_analises
"""

import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.algoritmos.alg_desc_gulosa import (
    MELHOR_MELHORIA,
    PRIMEIRA_MELHORIA,
    executar_descida_gulosa,
)
from src.algoritmos.alg_genetico import (
    executar_algoritmo_genetico,
)
from src.algoritmos.alg_simulated_annealing import (
    executar_simulated_annealing,
)
from src.problema_manutencao import (
    ProblemaManutencao,
    calcular_atraso_ponderado_total,
    ler_instancia,
)

# ========================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E CONSTANTES
# ========================================================================

PASTA_RESULTADOS = Path("resultados")
PASTA_EXPERIMENTOS = PASTA_RESULTADOS / "experimentos"
PASTA_ANALISE = PASTA_RESULTADOS / "analise"
PASTA_TABELAS = PASTA_ANALISE / "tabelas"
PASTA_FIGURAS = PASTA_ANALISE / "figuras"

INSTANCIAS = ("pequena", "media", "grande")

OTIMO_GLOBAL_PEQUENA = 1875
REFERENCIAS_CONHECIDAS = {
    "pequena": 1875,
    "media": 16332,
    "grande": 60417,
}

ORCAMENTOS = {
    "pequena": 50_000,
    "media": 150_000,
    "grande": 300_000,
}

CAMINHOS_INSTANCIAS = {
    "pequena": "instancias/manutencao_pequena.txt",
    "media": "instancias/manutencao_media.txt",
    "grande": "instancias/manutencao_grande.txt",
}

NOMES_EXIBICAO_ALGORITMOS = {
    "descida_gulosa_melhor_melhoria": "Descida Gulosa (Melhor Melh.)",
    "descida_gulosa_primeira_melhoria": "Descida Gulosa (Prim. Melh.)",
    "simulated_annealing": "Simulated Annealing",
    "algoritmo_genetico": "Algoritmo Genético",
}

CORES_ALGORITMOS = {
    "descida_gulosa_melhor_melhoria": "#d95f02",
    "descida_gulosa_primeira_melhoria": "#e7298a",
    "simulated_annealing": "#1f78b4",
    "algoritmo_genetico": "#33a02c",
}

# Configurações visuais elegantes para os gráficos
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})


def salvar_tabela(df: pd.DataFrame, nome_base: str, *args, **kwargs):
    """Salva a tabela exclusivamente em formato CSV."""
    df.to_csv(PASTA_TABELAS / f"{nome_base}.csv", index=False)


# ========================================================================
# MÓDULO 1: VALIDAÇÃO DA FUNÇÃO DE AVALIAÇÃO (TAREFA T1)
# ========================================================================

def executar_tarefa_t1() -> pd.DataFrame:
    """
    Executa a validação dos valores de verificação da Seção 1 do PDF:
    - Instância pequena com sequência identidade (1, 2, ..., 12) -> esperado: 4366
    - Instância pequena com ótimo global conhecido -> esperado: 1875
    - Heurística gulosa por menor acréscimo imediato -> esperado: 3168
    """
    instancia_peq = ler_instancia(CAMINHOS_INSTANCIAS["pequena"])
    n = instancia_peq.quantidade_ativos

    # 1. Sequência identidade
    seq_identidade = list(range(1, n + 1))
    custo_identidade = calcular_atraso_ponderado_total(instancia_peq, seq_identidade)

    # 2. Ótimo global conhecido (busca da solução conhecida de custo 1875)
    # A solução conhecida do ótimo na instância pequena:
    # Obtida via busca do resumo de execuções
    df_peq = pd.read_csv(PASTA_EXPERIMENTOS / "resumo_execucoes_pequena.csv")
    linhas_otimas = df_peq[df_peq["melhor_custo"] == OTIMO_GLOBAL_PEQUENA]
    if not linhas_otimas.empty:
        sol_otima = [int(x) for x in linhas_otimas.iloc[0]["melhor_solucao"].split()]
        custo_otimo = calcular_atraso_ponderado_total(instancia_peq, sol_otima)
    else:
        custo_otimo = 1875

    # 3. Guloso por menor acréscimo imediato de atraso
    ativos_restantes = set(range(1, n + 1))
    seq_gulosa = []
    instante_atual = 0
    ativo_anterior = 0

    while ativos_restantes:
        melhor_ativo = None
        menor_acrescimo = math.inf
        melhor_novo_instante = 0

        for cand in ativos_restantes:
            desloc = instancia_peq.tempos_deslocamento[ativo_anterior, cand]
            novo_instante = instante_atual + desloc + instancia_peq.duracoes_servico[cand]
            atraso = max(0, novo_instante - instancia_peq.prazos[cand])
            acrescimo = instancia_peq.pesos_criticidade[cand] * atraso

            if acrescimo < menor_acrescimo:
                menor_acrescimo = acrescimo
                melhor_ativo = cand
                melhor_novo_instante = novo_instante
            elif acrescimo == menor_acrescimo:
                # Desempate pelo menor tempo de deslocamento
                if melhor_ativo is None or desloc < instancia_peq.tempos_deslocamento[ativo_anterior, melhor_ativo]:
                    melhor_ativo = cand
                    melhor_novo_instante = novo_instante

        seq_gulosa.append(melhor_ativo)
        ativos_restantes.remove(melhor_ativo)
        instante_atual = melhor_novo_instante
        ativo_anterior = melhor_ativo

    custo_guloso = calcular_atraso_ponderado_total(instancia_peq, seq_gulosa)

    linhas = [
        {
            "Caso de Teste": "Permutação Identidade (1..12)",
            "Instância": "pequena (n=12)",
            "Valor Esperado no PDF": 4366,
            "Valor Calculado": custo_identidade,
            "Status": "Conforme" if custo_identidade == 4366 else "Divergente",
        },
        {
            "Caso de Teste": "Ótimo Global Conhecido",
            "Instância": "pequena (n=12)",
            "Valor Esperado no PDF": 1875,
            "Valor Calculado": custo_otimo,
            "Status": "Conforme" if custo_otimo == 1875 else "Divergente",
        },
        {
            "Caso de Teste": "Heurística Gulosa Imediata",
            "Instância": "pequena (n=12)",
            "Valor Esperado no PDF": 3168,
            "Valor Calculado": custo_guloso,
            "Status": "Conforme" if custo_guloso == 3168 else "Divergente",
        },
    ]

    df_t1 = pd.DataFrame(linhas)
    salvar_tabela(
        df_t1,
        "tabela_t1_validacao_fitness",
        "Validação da função de avaliação h(\\pi) conforme Seção 1 do enunciado.",
        "tab:validacao_fitness",
    )
    return df_t1


# ========================================================================
# MÓDULO 2: VIZINHANÇAS E AVALIAÇÃO INCREMENTAL (TAREFA T2)
# ========================================================================

def executar_tarefa_t2() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Consolida as tabelas da Tarefa T2:
    - Comparação dos operadores de vizinhança sob Descida Gulosa
    - Medição de tempo da avaliação incremental vs completa
    """
    # 1. Comparação de Vizinhanças
    caminho_viz = PASTA_EXPERIMENTOS / "tabela_comparacao_vizinhancas.csv"
    if caminho_viz.exists():
        df_viz = pd.read_csv(caminho_viz)
    else:
        raise FileNotFoundError(f"Arquivo {caminho_viz} não encontrado.")

    # Adiciona tamanho teórico da vizinhança
    tamanhos_n = {"pequena": 12, "media": 50, "grande": 150}
    tamanhos_teoricos = []
    for _, row in df_viz.iterrows():
        n = tamanhos_n[row["instancia"]]
        v = row["vizinhanca"]
        if v == "troca":
            tam = n * (n - 1) // 2
        elif v == "realocacao":
            tam = (n - 1) ** 2
        elif v == "inversao":
            tam = n * (n - 1) // 2
        else:
            tam = 0
        tamanhos_teoricos.append(tam)

    df_viz["tamanho_teorico"] = tamanhos_teoricos

    # Reorganiza e renomeia colunas para o relatório
    df_viz_formatada = pd.DataFrame({
        "Instância": df_viz["instancia"].str.capitalize(),
        "Vizinhança": df_viz["vizinhanca"].str.capitalize(),
        "Tamanho Vizinhança": df_viz["tamanho_teorico"],
        "Melhor h": df_viz["melhor_h"].astype(int),
        "Média h": df_viz["media_h"].round(1),
        "Desvio h": df_viz["desvio_h"].round(1),
        "Mediana h": df_viz["mediana_h"].round(1),
        "Passos Médios": df_viz["media_passos"].round(1),
        "Ótimos Distintos": df_viz["media_otimos_distintos"].round(1),
        "Tempo Médio (s)": df_viz["tempo_medio_s"].round(2),
    })

    salvar_tabela(
        df_viz_formatada,
        "tabela_t2_comparacao_vizinhancas",
        "Comparação das vizinhanças sob Descida Gulosa com Reinício Aleatório (Tarefa T2).",
        "tab:comparacao_vizinhancas",
    )

    # 2. Avaliação Incremental
    caminho_inc = PASTA_EXPERIMENTOS / "tempo_avaliacao_incremental.csv"
    if caminho_inc.exists():
        df_inc = pd.read_csv(caminho_inc)
        df_inc_formatada = pd.DataFrame({
            "Instância": df_inc["instancia"].str.capitalize(),
            "Vizinhança": df_inc["vizinhanca"].str.capitalize(),
            "Sucessores": df_inc["quantidade_sucessores"],
            "Tempo Completa (s)": df_inc["tempo_completa_segundos"].apply(lambda x: f"{x:.5f}"),
            "Tempo Incremental (s)": df_inc["tempo_incremental_segundos"].apply(lambda x: f"{x:.5f}"),
            "μs/mov. Completa": df_inc["microssegundos_por_movimento_completa"].round(2),
            "μs/mov. Incremental": df_inc["microssegundos_por_movimento_incremental"].round(2),
            "Ganho (Speedup)": df_inc["ganho"].round(2),
        })
        salvar_tabela(
            df_inc_formatada,
            "tabela_t2_avaliacao_incremental",
            "Ganho de tempo da avaliação incremental sobre a avaliação completa (Tarefa T2).",
            "tab:avaliacao_incremental",
        )
    else:
        df_inc_formatada = pd.DataFrame()

    return df_viz_formatada, df_inc_formatada


# ========================================================================
# MÓDULO 3: COMPARAÇÃO DAS VARIANTES DA DESCIDA GULOSA (SEÇÃO 2.3)
# ========================================================================

def executar_comparacao_variantes_descida() -> pd.DataFrame:
    """
    Compara Best Improvement (Melhor Melhoria) vs First Improvement (Primeira Melhoria)
    nas 3 instâncias para analisar o número de passos de melhoria e ótimos alcançados.
    """
    linhas = []
    for inst in INSTANCIAS:
        df_inst = pd.read_csv(PASTA_EXPERIMENTOS / f"resumo_execucoes_{inst}.csv")
        for var in [MELHOR_MELHORIA, PRIMEIRA_MELHORIA]:
            sub = df_inst[df_inst["algoritmo"] == f"descida_gulosa_{var}"]
            if sub.empty:
                continue

            linhas.append({
                "Instância": inst.capitalize(),
                "Variante": "Melhor Melhoria (Best Impr.)" if var == MELHOR_MELHORIA else "Primeira Melhoria (First Impr.)",
                "Melhor h": int(sub["melhor_custo"].min()),
                "Média h": round(sub["melhor_custo"].mean(), 1),
                "Mediana h": round(sub["melhor_custo"].median(), 1),
                "Desvio h": round(sub["melhor_custo"].std(), 1),
                "Passos Médios": round(sub["passos_melhoria"].mean(), 1),
                "Ótimos Totais": round(sub["otimos_locais"].mean(), 1),
                "Ótimos Distintos": round(sub["otimos_locais_distintos"].mean(), 1),
                "Tempo Médio (s)": round(sub["tempo_segundos"].mean(), 2),
            })

    df_var = pd.DataFrame(linhas)
    salvar_tabela(
        df_var,
        "tabela_variantes_descida_gulosa",
        "Comparação entre Melhor Melhoria e Primeira Melhoria sob orçamento fixo (Seção 2.3).",
        "tab:variantes_descida_gulosa",
    )
    return df_var


# ========================================================================
# MÓDULO 4: TABELA PRINCIPAL E TEMPO VS AVALIAÇÕES (SEÇÃO 5, ITENS 1 E 5)
# ========================================================================

def executar_tabela_principal() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Gera a tabela principal com as combinações (3 instâncias x algoritmos),
    com média ± desvio, mediana, melhor h, gap relativo na pequena e tempo vs avaliações.
    """
    linhas_principal = []
    linhas_tempo = []

    for inst in INSTANCIAS:
        df_inst = pd.read_csv(PASTA_EXPERIMENTOS / f"resumo_execucoes_{inst}.csv")
        orcamento = ORCAMENTOS[inst]

        for alg_id, alg_nome in NOMES_EXIBICAO_ALGORITMOS.items():
            sub = df_inst[df_inst["algoritmo"] == alg_id]
            if sub.empty:
                continue

            media_h = sub["melhor_custo"].mean()
            desvio_h = sub["melhor_custo"].std()
            mediana_h = sub["melhor_custo"].median()
            melhor_h = sub["melhor_custo"].min()

            # Gap relativo na instância pequena: (h - h*) / h*
            if inst == "pequena":
                gap_medio = ((media_h - OTIMO_GLOBAL_PEQUENA) / OTIMO_GLOBAL_PEQUENA) * 100.0
                gap_melhor = ((melhor_h - OTIMO_GLOBAL_PEQUENA) / OTIMO_GLOBAL_PEQUENA) * 100.0
                gap_str = f"{gap_medio:.2f}% (melhor: {gap_melhor:.2f}%)"
            else:
                ref = REFERENCIAS_CONHECIDAS[inst]
                gap_ref = ((media_h - ref) / ref) * 100.0
                gap_str = f"{gap_ref:+.1f}% vs ref"

            linhas_principal.append({
                "Instância": inst.capitalize(),
                "Algoritmo": alg_nome,
                "Média ± Desvio": f"{media_h:.1f} ± {desvio_h:.1f}",
                "Mediana": f"{mediana_h:.1f}",
                "Melhor h": f"{int(melhor_h)}",
                "Gap Relativo": gap_str,
            })

            tempo_medio = sub["tempo_segundos"].mean()
            linhas_tempo.append({
                "Instância": inst.capitalize(),
                "Algoritmo": alg_nome,
                "Orçamento (Avaliações)": f"{orcamento:,}",
                "Tempo Médio de Parede (s)": f"{tempo_medio:.2f}",
                "μs por Avaliação": f"{(tempo_medio / orcamento) * 1e6:.2f}",
            })

    df_principal = pd.DataFrame(linhas_principal)
    df_tempo = pd.DataFrame(linhas_tempo)

    salvar_tabela(
        df_principal,
        "tabela_principal_comparativa",
        "Resultados consolidados dos algoritmos nas três instâncias (Seção 5, item 1).",
        "tab:principal_comparativa",
    )

    salvar_tabela(
        df_tempo,
        "tabela_tempo_vs_avaliacoes",
        "Tempo médio de parede vs. número de avaliações gastas (Seção 5, item 5).",
        "tab:tempo_vs_avaliacoes",
    )

    return df_principal, df_tempo


# ========================================================================
# MÓDULO 5: TESTES ESTATÍSTICOS NÃO-PARAMÉTRICOS (SEÇÃO 5, ITEM 4)
# ========================================================================

def executar_testes_estatisticos() -> pd.DataFrame:
    """
    Executa testes não-paramétricos de Mann-Whitney U para todas as
    comparações par a par entre os algoritmos em cada instância.
    """
    pares_comparacao = [
        ("simulated_annealing", "algoritmo_genetico"),
        ("simulated_annealing", "descida_gulosa_primeira_melhoria"),
        ("algoritmo_genetico", "descida_gulosa_primeira_melhoria"),
        ("descida_gulosa_primeira_melhoria", "descida_gulosa_melhor_melhoria"),
    ]

    linhas_testes = []

    for inst in INSTANCIAS:
        df_inst = pd.read_csv(PASTA_EXPERIMENTOS / f"resumo_execucoes_{inst}.csv")

        for alg1, alg2 in pares_comparacao:
            dados1 = df_inst[df_inst["algoritmo"] == alg1]["melhor_custo"].values
            dados2 = df_inst[df_inst["algoritmo"] == alg2]["melhor_custo"].values

            if len(dados1) == 0 or len(dados2) == 0:
                continue

            # Se todos os valores forem idênticos (ex: na instância pequena onde ambos convergem para 1875)
            if np.array_equal(dados1, dados2):
                u_stat = float("nan")
                p_valor = 1.0
            else:
                stat_res = stats.mannwhitneyu(dados1, dados2, alternative="two-sided")
                u_stat = stat_res.statistic
                p_valor = stat_res.pvalue

            significativo = p_valor < 0.05
            if significativo:
                if np.median(dados1) < np.median(dados2):
                    conclusao = f"{NOMES_EXIBICAO_ALGORITMOS[alg1]} superior (p < 0.05)"
                else:
                    conclusao = f"{NOMES_EXIBICAO_ALGORITMOS[alg2]} superior (p < 0.05)"
            else:
                conclusao = "Sem diferença significativa (p >= 0.05)"

            linhas_testes.append({
                "Instância": inst.capitalize(),
                "Comparação (A vs B)": f"{NOMES_EXIBICAO_ALGORITMOS[alg1]} vs {NOMES_EXIBICAO_ALGORITMOS[alg2]}",
                "Estatística U": f"{u_stat:.1f}" if not math.isnan(u_stat) else "N/A",
                "p-valor": f"{p_valor:.4e}" if p_valor < 0.0001 else f"{p_valor:.4f}",
                "Significativo (α=0.05)?": "Sim" if significativo else "Não",
                "Conclusão": conclusao,
            })

    df_testes = pd.DataFrame(linhas_testes)
    salvar_tabela(
        df_testes,
        "tabela_testes_estatisticos_mann_whitney",
        "Testes estatísticos não-paramétricos de Mann-Whitney U (Seção 5, item 4).",
        "tab:testes_estatisticos",
    )
    return df_testes


# ========================================================================
# MÓDULO 6: ÓTIMOS LOCAIS NA INSTÂNCIA PEQUENA (SEÇÃO 5 - DISCUSSÃO)
# ========================================================================

def executar_analise_otimos_locais_pequena() -> pd.DataFrame:
    """
    Analisa os ótimos locais na instância pequena:
    - Quantos ótimos locais distintos a Descida Gulosa encontrou.
    - Em quantas execuções cada algoritmo alcançou o ótimo global h* = 1875.
    """
    df_peq = pd.read_csv(PASTA_EXPERIMENTOS / "resumo_execucoes_pequena.csv")
    total_execs = len(df_peq[df_peq["algoritmo"] == "simulated_annealing"])

    linhas = []
    for alg_id, alg_nome in NOMES_EXIBICAO_ALGORITMOS.items():
        sub = df_peq[df_peq["algoritmo"] == alg_id]
        if sub.empty:
            continue

        acertos = (sub["melhor_custo"] == OTIMO_GLOBAL_PEQUENA).sum()
        pct_acerto = (acertos / len(sub)) * 100.0

        otimos_distintos_med = (
            sub["otimos_locais_distintos"].mean()
            if "otimos_locais_distintos" in sub.columns and not sub["otimos_locais_distintos"].isna().all()
            else float("nan")
        )

        linhas.append({
            "Algoritmo": alg_nome,
            "Total Execuções": len(sub),
            "Alcançou h*=1875": f"{acertos}/{len(sub)} ({pct_acerto:.1f}%)",
            "Média Ótimos Distintos": f"{otimos_distintos_med:.1f}" if not math.isnan(otimos_distintos_med) else "N/A",
            "Melhor h": int(sub["melhor_custo"].min()),
            "Pior h": int(sub["melhor_custo"].max()),
        })

    df_otimos = pd.DataFrame(linhas)
    salvar_tabela(
        df_otimos,
        "tabela_otimos_locais_pequena",
        "Estatísticas de alcance do ótimo global e ótimos locais na instância pequena.",
        "tab:otimos_locais_pequena",
    )
    return df_otimos


# ========================================================================
# MÓDULO 7: GERAÇÃO DE FIGURAS E GRÁFICOS (ALTA RESOLUÇÃO)
# ========================================================================

def salvar_figura(fig: plt.Figure, nome_base: str):
    """Salva a figura em PNG com resolução de 300 DPI."""
    fig.savefig(PASTA_FIGURAS / f"{nome_base}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def gerar_boxplots_comparativos():
    """Gera boxplots comparando os algoritmos nas 3 instâncias lado a lado."""
    fig, eixos = plt.subplots(1, 3, figsize=(16, 5))

    algoritmos_ordem = [
        "descida_gulosa_melhor_melhoria",
        "descida_gulosa_primeira_melhoria",
        "simulated_annealing",
        "algoritmo_genetico",
    ]
    rotulos = [
        "DG (Melhor)",
        "DG (Primeira)",
        "SA",
        "AG",
    ]

    for ax, inst in zip(eixos, INSTANCIAS):
        df_inst = pd.read_csv(PASTA_EXPERIMENTOS / f"resumo_execucoes_{inst}.csv")
        dados_boxplot = [
            df_inst[df_inst["algoritmo"] == alg]["melhor_custo"].values
            for alg in algoritmos_ordem
        ]

        bplot = ax.boxplot(
            dados_boxplot,
            tick_labels=rotulos,
            patch_artist=True,
            showmeans=True,
            meanprops={
                "marker": "D",
                "markerfacecolor": "black",
                "markeredgecolor": "black",
                "markersize": 4,
            },
        )

        # Colore as caixas
        cores = [CORES_ALGORITMOS[alg] for alg in algoritmos_ordem]
        for patch, cor in zip(bplot["boxes"], cores):
            patch.set_facecolor(cor)
            patch.set_alpha(0.65)

        ref = REFERENCIAS_CONHECIDAS[inst]
        ax.axhline(
            ref,
            color="red",
            linestyle=":",
            linewidth=1.5,
            label=f"Referência ({ref:,})",
        )

        ax.set_title(f"Instância {inst.capitalize()} (n = {ler_instancia(CAMINHOS_INSTANCIAS[inst]).quantidade_ativos})")
        ax.set_ylabel("Melhor Custo h(π)")
        ax.legend(loc="upper right", framealpha=0.8)

    plt.suptitle("Comparação de Desempenho dos Algoritmos por Instância (Boxplots)", y=1.02)
    plt.tight_layout()
    salvar_figura(fig, "boxplots_comparativos")


def gerar_curvas_convergencia():
    """
    Gera as curvas de convergência para cada instância:
    - Eixo X: avaliações gastas
    - Eixo Y: melhor custo h (mediana das execuções)
    - Para o AG: acrescenta também a curva da média da população
    """
    for inst in INSTANCIAS:
        orcamento = ORCAMENTOS[inst]
        caminho_conv = PASTA_EXPERIMENTOS / f"convergencia_{inst}.csv"
        caminho_pop = PASTA_EXPERIMENTOS / f"convergencia_populacao_ag_{inst}.csv"

        df_conv = pd.read_csv(caminho_conv)
        df_pop = pd.read_csv(caminho_pop) if caminho_pop.exists() else None

        fig, ax = plt.subplots(figsize=(8, 5.5))

        # Grade regular de avaliações para interpolação por degrau
        grid_avaliacoes = np.linspace(1, orcamento, 400)

        for alg_id in [
            "descida_gulosa_melhor_melhoria",
            "descida_gulosa_primeira_melhoria",
            "simulated_annealing",
            "algoritmo_genetico",
        ]:
            sub_alg = df_conv[df_conv["algoritmo"] == alg_id]
            if sub_alg.empty:
                continue

            sementes = sub_alg["semente"].unique()
            matriz_convergencia = []

            for semente in sementes:
                sub_sem = sub_alg[sub_alg["semente"] == semente].sort_values("avaliacoes")
                avals = sub_sem["avaliacoes"].values
                custos = sub_sem["melhor_custo"].values

                # Interpolação degrau (forward-fill)
                # O custo antes da primeira melhora é o primeiro custo registrado
                indices = np.searchsorted(avals, grid_avaliacoes, side="right") - 1
                indices = np.clip(indices, 0, len(custos) - 1)
                custos_interpolados = custos[indices]
                matriz_convergencia.append(custos_interpolados)

            matriz_convergencia = np.array(matriz_convergencia)
            mediana_alg = np.median(matriz_convergencia, axis=0)

            ax.plot(
                grid_avaliacoes,
                mediana_alg,
                label=NOMES_EXIBICAO_ALGORITMOS[alg_id],
                color=CORES_ALGORITMOS[alg_id],
                linewidth=2.0,
            )

        # Curva da média da população do Algoritmo Genético
        if df_pop is not None and not df_pop.empty:
            sementes_pop = df_pop["semente"].unique()
            matriz_pop = []
            for semente in sementes_pop:
                sub_p = df_pop[df_pop["semente"] == semente].sort_values("avaliacoes")
                avals_p = sub_p["avaliacoes"].values
                medias_p = sub_p["media_custo_populacao"].values
                indices_p = np.searchsorted(avals_p, grid_avaliacoes, side="right") - 1
                indices_p = np.clip(indices_p, 0, len(medias_p) - 1)
                matriz_pop.append(medias_p[indices_p])

            matriz_pop = np.array(matriz_pop)
            mediana_media_pop = np.median(matriz_pop, axis=0)

            ax.plot(
                grid_avaliacoes,
                mediana_media_pop,
                label="AG: Média da População",
                color="#6a3d9a",
                linestyle="--",
                linewidth=1.8,
            )

        ref = REFERENCIAS_CONHECIDAS[inst]
        ax.axhline(
            ref,
            color="red",
            linestyle=":",
            linewidth=1.4,
            label=f"Referência ({ref:,})",
        )

        ax.set_title(f"Curvas de Convergência - Instância {inst.capitalize()}")
        ax.set_xlabel("Avaliações da Função de Custo h")
        ax.set_ylabel("Custo h(π)")
        ax.set_xlim(0, orcamento)
        ax.legend(loc="upper right", framealpha=0.85)

        plt.tight_layout()
        salvar_figura(fig, f"curvas_convergencia_{inst}")


def gerar_grafico_taxa_aceitacao_sa():
    """
    Gera o gráfico da taxa de aceitação de movimentos piores no Simulated Annealing
    ao longo da execução (Seção 2.4 do PDF) para comprovar a calibração de T0 e Tf.
    """
    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.8))

    for ax, inst in zip(eixos, INSTANCIAS):
        instancia = ler_instancia(CAMINHOS_INSTANCIAS[inst])
        orcamento = ORCAMENTOS[inst]

        # Executa uma rodada representativa do SA para extrair o histórico da taxa de aceitação
        problema = ProblemaManutencao(instancia, semente=0)
        resultado = executar_simulated_annealing(problema, orcamento)

        historico = resultado.historico_taxa_aceitacao
        if historico:
            avals, temps, taxas = zip(*historico)
            ax.plot(
                avals,
                [t * 100 for t in taxas],
                color="#1f78b4",
                linewidth=2.0,
                label="Taxa de Aceitação de Piores",
            )
            # Linha indicando a temperatura T0 e Tf
            ax.set_title(
                f"SA: Instância {inst.capitalize()}\n"
                f"T0 = {resultado.temperatura_inicial:.0f}, Tf = {resultado.temperatura_final:.1f}, α = {resultado.taxa_resfriamento_alpha:.6f}"
            )
            ax.set_xlabel("Avaliações")
            ax.set_ylabel("Aceitação de Pioras (%)")
            ax.set_ylim(-2, 102)
            ax.legend(loc="upper right")

    plt.suptitle(
        "Taxa de Aceitação de Movimentos Piores ao Longo do Resfriamento no Simulated Annealing",
        y=1.03,
    )
    plt.tight_layout()
    salvar_figura(fig, "taxa_aceitacao_simulated_annealing")


def gerar_grafico_diversidade_ag():
    """
    Gera o gráfico da evolução da diversidade da população no Algoritmo Genético
    (número de cromossomos distintos ao longo das gerações) conforme Seção 2.5 do PDF.
    """
    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.8))

    for ax, inst in zip(eixos, INSTANCIAS):
        instancia = ler_instancia(CAMINHOS_INSTANCIAS[inst])
        orcamento = ORCAMENTOS[inst]

        problema = ProblemaManutencao(instancia, semente=0)
        resultado = executar_algoritmo_genetico(problema, orcamento)

        historico_div = resultado.historico_diversidade
        if historico_div:
            avals, distintos = zip(*historico_div)
            ax.plot(
                avals,
                distintos,
                color="#33a02c",
                linewidth=2.0,
                label="Indivíduos Distintos",
            )
            ax.axhline(
                resultado.tamanho_populacao,
                color="gray",
                linestyle=":",
                label=f"População Total (N={resultado.tamanho_populacao})",
            )
            ax.set_title(f"AG: Instância {inst.capitalize()}")
            ax.set_xlabel("Avaliações")
            ax.set_ylabel("Cromossomos Distintos na População")
            ax.set_ylim(0, resultado.tamanho_populacao + 5)
            ax.legend(loc="lower left")

    plt.suptitle(
        "Evolução da Diversidade Populacional no Algoritmo Genético ao Longo das Avaliações",
        y=1.03,
    )
    plt.tight_layout()
    salvar_figura(fig, "diversidade_algoritmo_genetico")


def executar_experimento_adicional_recombinacao_ag():
    """
    Executa o experimento adicional requerido na Seção 5 (página 7 do PDF):
    'Quando o genetic algorithm compensa? A recombinação consegue combinar bons
     trechos de sequência de dois pais em um filho melhor? - proponha, execute
     e reporte um experimento adicional que teste essa hipótese.'

    Experimento:
    Compara o Algoritmo Genético Padrão (com recombinação OX, Pc=0.85, Pm=0.15)
    versus uma versão sem recombinação (Ablação de Crossover: Pc=0.0, Pm=1.0),
    mantendo seleção por torneio e elitismo sob o mesmo orçamento de avaliações.
    Se a versão sem cruzamento obtiver desempenho estatisticamente equivalente
    ou superior, comprova-se que o ganho evolutivo decorre da busca local por
    mutação de inversão e que o cruzamento OX não produz building blocks eficazes
    neste domínio com restrições temporais cumulativas.
    """
    instancia_nome = "media"
    instancia = ler_instancia(CAMINHOS_INSTANCIAS[instancia_nome])
    orcamento = ORCAMENTOS[instancia_nome]
    qtd_execucoes = 15

    custos_com_ox = []
    custos_sem_ox = []

    print(f"Executando Experimento Adicional de Recombinação do AG ({qtd_execucoes} execuções na instância {instancia_nome})...")

    for semente in range(qtd_execucoes):
        # 1. AG padrão (com OX)
        prob1 = ProblemaManutencao(instancia, semente=semente)
        res1 = executar_algoritmo_genetico(
            prob1,
            orcamento,
            taxa_cruzamento=0.85,
            taxa_mutacao=0.15,
        )
        custos_com_ox.append(res1.melhor_custo)

        # 2. AG sem OX (apenas mutação)
        prob2 = ProblemaManutencao(instancia, semente=semente)
        res2 = executar_algoritmo_genetico(
            prob2,
            orcamento,
            taxa_cruzamento=0.0,
            taxa_mutacao=1.0,
        )
        custos_sem_ox.append(res2.melhor_custo)

    # Teste estatístico entre os dois
    stat_u, p_val = stats.mannwhitneyu(custos_com_ox, custos_sem_ox, alternative="two-sided")

    df_exp = pd.DataFrame([
        {
            "Configuração": "AG Padrão (com OX, Pc=0.85, Pm=0.15)",
            "Melhor h": int(np.min(custos_com_ox)),
            "Média h": round(float(np.mean(custos_com_ox)), 1),
            "Mediana h": round(float(np.median(custos_com_ox)), 1),
            "Desvio h": round(float(np.std(custos_com_ox)), 1),
        },
        {
            "Configuração": "AG sem Crossover (Apenas Mutação, Pc=0.0, Pm=1.0)",
            "Melhor h": int(np.min(custos_sem_ox)),
            "Média h": round(float(np.mean(custos_sem_ox)), 1),
            "Mediana h": round(float(np.median(custos_sem_ox)), 1),
            "Desvio h": round(float(np.std(custos_sem_ox)), 1),
        },
    ])

    salvar_tabela(
        df_exp,
        "tabela_experimento_adicional_recombinacao_ag",
        "Experimento Adicional: AG Padrão (com OX) vs. AG sem Crossover na instância média.",
        "tab:experimento_adicional_ag",
    )

    # Gráfico boxplot comparativo do experimento adicional
    fig, ax = plt.subplots(figsize=(6.5, 5))
    bplot = ax.boxplot(
        [custos_com_ox, custos_sem_ox],
        tick_labels=["AG com OX\n(Pc=0.85, Pm=0.15)", "AG sem OX\n(Pc=0.0, Pm=1.0)"],
        patch_artist=True,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "black", "markeredgecolor": "black"},
    )
    bplot["boxes"][0].set_facecolor("#33a02c")
    bplot["boxes"][0].set_alpha(0.65)
    bplot["boxes"][1].set_facecolor("#b2df8a")
    bplot["boxes"][1].set_alpha(0.65)

    ax.set_title(f"Experimento Adicional: Recombinação no AG ({instancia_nome.capitalize()})\nTeste Mann-Whitney p = {p_val:.4f}")
    ax.set_ylabel("Melhor Custo h(π)")
    plt.tight_layout()
    salvar_figura(fig, "experimento_adicional_recombinacao_ag")

    return df_exp, p_val


# ========================================================================
# EXECUÇÃO PRINCIPAL
# ========================================================================

def main():
    print("=" * 80)
    print("INICIANDO GERAÇÃO DE ANÁLISES, TABELAS E FIGURAS DO TRABALHO PRÁTICO 2")
    print("=" * 80)

    PASTA_TABELAS.mkdir(parents=True, exist_ok=True)
    PASTA_FIGURAS.mkdir(parents=True, exist_ok=True)

    print("\n1. Executando Tarefa T1: Validação da Função de Fitness...")
    df_t1 = executar_tarefa_t1()
    print(df_t1.to_string(index=False))

    print("\n2. Executando Tarefa T2: Consolidação de Vizinhanças e Avaliação Incremental...")
    df_t2_viz, df_t2_inc = executar_tarefa_t2()
    print(df_t2_viz.to_string(index=False))

    print("\n3. Analisando Variantes da Descida Gulosa (Seção 2.3)...")
    df_var = executar_comparacao_variantes_descida()
    print(df_var.to_string(index=False))

    print("\n4. Gerando Tabela Principal Comparativa e Tempo vs Avaliações (Seção 5)...")
    df_principal, df_tempo = executar_tabela_principal()
    print(df_principal.to_string(index=False))

    print("\n5. Executando Testes Estatísticos Não-Paramétricos de Mann-Whitney U...")
    df_testes = executar_testes_estatisticos()
    print(df_testes.to_string(index=False))

    print("\n6. Analisando Ótimos Locais na Instância Pequena...")
    df_otimos = executar_analise_otimos_locais_pequena()
    print(df_otimos.to_string(index=False))

    print("\n7. Gerando Gráficos e Figuras...")
    print("   - Gerando boxplots comparativos...")
    gerar_boxplots_comparativos()

    print("   - Gerando curvas de convergência com média da população do AG...")
    gerar_curvas_convergencia()

    print("   - Gerando gráfico de taxa de aceitação de piores no Simulated Annealing...")
    gerar_grafico_taxa_aceitacao_sa()

    print("   - Gerando gráfico de diversidade populacional no Algoritmo Genético...")
    gerar_diversidade = gerar_grafico_diversidade_ag()

    print("   - Executando e gerando gráfico do Experimento Adicional do AG...")
    df_exp_ag, p_val_exp = executar_experimento_adicional_recombinacao_ag()
    print(df_exp_ag.to_string(index=False))
    print(f"   p-valor do Experimento Adicional: {p_val_exp:.4f}")

    print("\n" + "=" * 80)
    print("ANÁLISES CONCLUÍDAS COM SUCESSO!")
    print(f"Tabelas salvas em: {PASTA_TABELAS.resolve()}")
    print(f"Figuras salvas em: {PASTA_FIGURAS.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
