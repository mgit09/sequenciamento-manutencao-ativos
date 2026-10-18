"""
Converte as tabelas .csv geradas por gerar_analises.py em arquivos .tex.

Cada tabela vira um arquivo com o ambiente tabular (estilo booktabs), ajustado
à largura disponível, pronto para ser incluído no relatório com \\input.

Uso, a partir da raiz do projeto:

    python -m scripts.gerar_tabelas_latex
"""

import argparse
import re
from pathlib import Path

import pandas as pd


# ========================================================================
# CONFIGURAÇÕES

# Caracteres que têm significado especial em LaTeX ou não existem na fonte padrão
SUBSTITUICOES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
    "±": r"$\pm$",
    "μ": r"$\mu$",
    "α": r"$\alpha$",
    "π": r"$\pi$",
    "≥": r"$\geq$",
    "≤": r"$\leq$",
}

# ========================================================================

def formatar_celula(valor) -> str:
    """Escapa os caracteres especiais e usa vírgula como separador decimal."""
    texto = str(valor)
    for caractere, substituto in SUBSTITUICOES.items():
        texto = texto.replace(caractere, substituto)

    # Troca o ponto decimal por vírgula (1.5 vira 1{,}5)
    return re.sub(r"(\d)\.(\d)", r"\1{,}\2", texto)


def converter_tabela(caminho_csv: Path, caminho_tex: Path):
    """Lê um .csv e grava o .tex correspondente."""
    # Lê tudo como texto, para preservar exatamente o que está no .csv (ex.: "N/A", "0.0420")
    tabela = pd.read_csv(
        caminho_csv,
        dtype=str,
        keep_default_na=False,
    )

    # Colunas inteiramente numéricas ficam à direita e as demais à esquerda
    alinhamentos = "".join(
        "r" if pd.to_numeric(tabela[coluna], errors="coerce").notna().all() else "l"
        for coluna in tabela.columns
    )

    linhas = [
        r"\resizebox{\linewidth}{!}{%",
        rf"\begin{{tabular}}{{{alinhamentos}}}",
        r"\toprule",
        " & ".join(formatar_celula(coluna) for coluna in tabela.columns) + r" \\",
        r"\midrule",
    ]
    for _, linha in tabela.iterrows():
        linhas.append(" & ".join(formatar_celula(valor) for valor in linha) + r" \\")
    linhas += [r"\bottomrule", r"\end{tabular}}"]

    caminho_tex.write_text("\n".join(linhas) + "\n", encoding="utf-8")

# ========================================================================
# EXECUÇÃO PRINCIPAL

def main():
    """Converte todos os .csv da pasta de tabelas."""
    leitor = argparse.ArgumentParser(
        description="Converte as tabelas .csv da análise em arquivos .tex.",
    )
    leitor.add_argument(
        "--pasta-entrada",
        default="resultados/analise/tabelas",
        help="pasta com os .csv (padrão: resultados/analise/tabelas)",
    )
    leitor.add_argument(
        "--pasta-saida",
        default="resultados/analise/tabelas_latex",
        help="pasta onde os .tex serão gravados (padrão: resultados/analise/tabelas_latex)",
    )
    argumentos = leitor.parse_args()

    pasta_saida = Path(argumentos.pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    for caminho_csv in sorted(Path(argumentos.pasta_entrada).glob("*.csv")):
        caminho_tex = pasta_saida / f"{caminho_csv.stem}.tex"
        converter_tabela(caminho_csv, caminho_tex)
        print(f"{caminho_csv.name} -> {caminho_tex}")


if __name__ == "__main__":
    main()
