# Sequenciamento de Manutenção de Ativos

Trabalho prático realizado no contexto da disciplina de Fundamentos de
Inteligência Artificial (UFMG).

Uma concessionária de energia precisa executar a manutenção preventiva de
vários ativos (religadores, transformadores, chaves seccionadoras) com uma
única equipe, que atende um ativo por vez. Cada ativo tem localização,
duração do serviço, prazo e peso de criticidade. O objetivo é encontrar a
ordem de visita que minimiza o atraso ponderado total.

Nesse projeto, foram comparados três algoritmos em três instâncias (12, 50 e 150 ativos):
descida gulosa com reinício aleatório, simulated annealing e algoritmo genético.

## Como executar

É necessário ter Python 3.10 ou superior. Na pasta do projeto, crie e ative
um ambiente virtual e instale as dependências:

**Linux / macOS**

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

**Windows**

    py -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Todos os comandos abaixo devem ser executados a partir da pasta raiz do
projeto, com o ambiente virtual ativado.

Para verificar a instalação e a função de avaliação, execute os testes
automáticos:

    python -m tests.testes

Se tudo estiver correto, a mensagem "Todos os testes passaram." é exibida.

## Estrutura do projeto

```txt
sequenciamento-manutencao-ativos
│
├── instancias/                          # Instâncias fornecidas (manutencao_*.txt)
├── resultados/
│   ├── experimentos/                    # Arquivos *.csv brutos gerados pelos experimentos
│   └── analise/
│       ├── tabelas/                     # Tabelas consolidadas em *.csv
│       ├── tabelas_latex/               # Tabelas convertidas em *.tex, prontas para o relatório
│       └── figuras/                     # Gráficos em alta resolução (*.png)
│
├── scripts/
│   ├── comparar_vizinhancas.py          # Compara as vizinhanças (troca, realocação, inversão) para T2
│   ├── executar_experimentos.py         # Executa os algoritmos nas instâncias e salva os *.csv
│   ├── medir_avaliacao_incremental.py   # Mede o ganho de tempo da avaliação incremental
│   ├── gerar_analises.py                # Lê experimentos/, gera tabelas em analise/tabelas e figuras em analise/figuras
│   └── gerar_tabelas_latex.py           # Converte as tabelas *.csv da análise em arquivos *.tex
│
├── src/
│   ├── problema_manutencao.py           # Modelo do problema, vizinhanças e avaliação (completa e incremental)
│   └── algoritmos/
│       ├── resultado_busca.py           # Estrutura base com o resultado de uma execução
│       ├── alg_desc_gulosa.py           # Descida gulosa com reinício aleatório
│       ├── alg_simulated_annealing.py   # Simulated Annealing com resfriamento geométrico
│       └── alg_genetico.py              # Algoritmo Genético com seleção por torneio, OX e elitismo
│
├── tests/
│   └── testes.py                        # Testes automáticos
│
├── .gitignore                           # Arquivos e pastas ignoradas
├── LICENSE                              # Licença do projeto
├── README.md                            # Informações úteis gerais do projeto
└── requirements.txt                     # Requisitos para rodar os códigos
```

## Reprodução dos resultados

Os experimentos utilizam sementes pseudoaleatórias fixas (a semente de cada execução é o seu índice, de 0 a $N-1$), o que permite reproduzir os resultados de qualidade (os tempos de execução variam conforme a máquina). Os arquivos brutos ficam na pasta `resultados/experimentos/`.

> **Nota sobre o fluxo de execução**: caso deseje reproduzir todos os dados do zero, a ordem recomendada é:
> 1. `python -m scripts.medir_avaliacao_incremental`
> 2. `python -m scripts.comparar_vizinhancas`
> 3. `python -m scripts.executar_experimentos`
> 4. `python -m scripts.gerar_analises` (depende das saídas dos scripts anteriores)
> 5. `python -m scripts.gerar_tabelas_latex` (depende da saída do passo 4)

### Experimentos dos algoritmos

Executa todos os algoritmos em todas as instâncias, seguindo o protocolo do
enunciado (orçamento de avaliações e número de execuções por instância):

    python -m scripts.executar_experimentos

Para executar apenas algumas instâncias (`pequena`, `media` ou `grande`):

    python -m scripts.executar_experimentos --instancias pequena

Para cada instância, são gerados arquivos na pasta `resultados/experimentos/`:

- `resumo_execucoes_<instancia>.csv`: uma linha por execução (melhor custo, avaliações, tempo e demais métricas)
- `convergencia_<instancia>.csv`: evolução do melhor custo ao longo das avaliações
- `convergencia_populacao_ag_<instancia>.csv`: evolução da média da população do AG

Os arquivos de uma instância são sobrescritos a cada execução do comando.
Para testes rápidos, use `--execucoes`, `--orcamento` e `--pasta-saida`
(por exemplo, `--pasta-saida resultados_teste`), a fim de não sobrescrever
os resultados oficiais.

Para executar apenas alguns algoritmos, use `--algoritmos` (`descida_gulosa_melhor_melhoria`, `descida_gulosa_primeira_melhoria`, `simulated_annealing` e `algoritmo_genetico`). Atenção: os arquivos da instância são regravados apenas com os algoritmos escolhidos, então, para os resultados oficiais, execute todos os algoritmos de uma mesma instância na mesma chamada.

A execução completa leva dezenas de minutos.

### Ganho de tempo da avaliação incremental

    python -m scripts.medir_avaliacao_incremental

Gera o arquivo `resultados/experimentos/tempo_avaliacao_incremental.csv`, com os tempos da
avaliação completa e da incremental para cada instância e vizinhança.

### Comparação das vizinhanças (Tarefa T2)

Compara os três operadores de vizinhança (`troca`, `realocacao` e `inversao`)
utilizando descida gulosa com reinício aleatório sob o mesmo orçamento de avaliações:

    python -m scripts.comparar_vizinhancas

Opções disponíveis:
- `--instancias`: instâncias a avaliar (`pequena`, `media`, `grande`). Padrão: todas.
- `--vizinhancas`: vizinhanças a testar (`troca`, `realocacao`, `inversao`). Padrão: todas.
- `--variante`: variante de descida (`primeira_melhoria` ou `melhor_melhoria`). Padrão: `primeira_melhoria`.
- `--execucoes`: número de execuções independentes por combinação (sobrescreve o padrão do protocolo).
- `--orcamento`: orçamento de avaliações por execução (sobrescreve o padrão do protocolo).
- `--pasta-saida`: diretório onde os arquivos serão salvos (padrão: `resultados/experimentos`).

Arquivo gerado:
- `resultados/experimentos/tabela_comparacao_vizinhancas.csv`: tabela consolidada com métricas agrupadas.

### Tabelas e figuras do relatório

Para processar todos os resultados, executar os testes de hipótese não-paramétricos, gerar todas as tabelas em CSV (`resultados/analise/tabelas/`) e produzir todos os gráficos em alta resolução PNG (`resultados/analise/figuras/`) para o relatório:

    python -m scripts.gerar_analises

Arquivos gerados:
- `resultados/analise/tabelas/`:
  - `tabela_t1_validacao_fitness.csv`: Validação da função de fitness $h(\pi)$ (Tarefa T1).
  - `tabela_t2_comparacao_vizinhancas.csv`: Desempenho comparativo das vizinhanças (Tarefa T2).
  - `tabela_t2_avaliacao_incremental.csv`: Ganho de tempo da avaliação incremental (Tarefa T2).
  - `tabela_variantes_descida_gulosa.csv`: Melhor Melhoria vs. Primeira Melhoria (Seção 2.3).
  - `tabela_principal_comparativa.csv`: Tabela principal com média $\pm$ desvio, mediana, melhor $h$ e gap relativo (Seção 5, item 1).
  - `tabela_tempo_vs_avaliacoes.csv`: Tempo de parede vs. avaliações gastas (Seção 5, item 5).
  - `tabela_testes_estatisticos_mann_whitney.csv`: Testes não-paramétricos de Mann-Whitney U (Seção 5, item 4).
  - `tabela_otimos_locais_pequena.csv`: Ótimos distintos e taxa de alcance do ótimo global $h^*=1875$ na pequena.
  - `tabela_experimento_adicional_recombinacao_ag.csv`: Experimento adicional sobre o operador OX do AG.

- `resultados/analise/figuras/`:
  - `boxplots_comparativos.png`: Distribuição do melhor $h$ dos algoritmos nas três instâncias.
  - `curvas_convergencia_{pequena,media,grande}.png`: Mediana do melhor $h$ ao longo das avaliações e média da população do AG.
  - `taxa_aceitacao_simulated_annealing.png`: Taxa de aceitação de piores ao longo do resfriamento no SA.
  - `diversidade_algoritmo_genetico.png`: Rastreamento de cromossomos distintos ao longo das avaliações no AG.
  - `experimento_adicional_recombinacao_ag.png`: Comparação entre AG com OX vs. AG puramente mutacional.

### Tabelas em LaTeX

Converte cada tabela `*.csv` de `resultados/analise/tabelas/` em um arquivo `*.tex` (ambiente `tabular` no estilo `booktabs`, ajustado à largura disponível), para ser incluído no relatório com `\input`:

    python -m scripts.gerar_tabelas_latex

Opções disponíveis:
- `--pasta-entrada`: pasta com os `*.csv` (padrão: `resultados/analise/tabelas`).
- `--pasta-saida`: pasta onde os `*.tex` serão gravados (padrão: `resultados/analise/tabelas_latex`).
