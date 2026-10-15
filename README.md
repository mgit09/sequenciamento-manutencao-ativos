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
├── resultados/                          # Arquivos *.csv gerados pelos experimentos
│
├── scripts/
│   ├── comparar_vizinhancas.py          # Compara as vizinhanças (troca, realocação, inversão) para T2
│   ├── executar_experimentos.py         # Executa os algoritmos nas instâncias e salva os *.csv
│   ├── medir_avaliacao_incremental.py   # Mede o ganho de tempo da avaliação incremental
│   └── gerar_analises.py                # Lê os *.csv e gera tabelas, boxplots, curvas, testes estatísticos
│
├── src/
│   ├── problema_manutencao.py           # Modelo do problema, vizinhanças e avaliação (completa e incremental)
│   └── algoritmos/
│       ├── resultado_busca.py           # Estrutura com o resultado de uma execução
│       └── alg_desc_gulosa.py           # Descida gulosa com reinício aleatório
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

Os experimentos usam sementes fixas (a semente de cada execução é o seu
número, de 0 a N-1), de modo que repetir os comandos abaixo gera exatamente
os mesmos resultados. Os arquivos gerados ficam na pasta `resultados/`.

### Experimentos dos algoritmos

Executa todos os algoritmos em todas as instâncias, seguindo o protocolo do
enunciado (orçamento de avaliações e número de execuções por instância):

    python -m scripts.executar_experimentos

Para executar apenas algumas instâncias (`pequena`, `media` ou `grande`):

    python -m scripts.executar_experimentos --instancias pequena

Para cada instância, são gerados dois arquivos:

- `resumo_execucoes_<instancia>.csv`: uma linha por execução (melhor custo, avaliações, tempo e demais métricas)
- `convergencia_<instancia>.csv`: evolução do melhor custo ao longo das avaliações

Os arquivos de uma instância são sobrescritos a cada execução do comando.
Para testes rápidos, use `--execucoes`, `--orcamento` e `--pasta-saida`
(por exemplo, `--pasta-saida resultados_teste`), a fim de não sobrescrever
os resultados oficiais.

### Ganho de tempo da avaliação incremental

    python -m scripts.medir_avaliacao_incremental

Gera o arquivo `resultados/tempo_avaliacao_incremental.csv`, com os tempos da
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
- `--pasta-saida`: diretório onde os arquivos serão salvos (padrão: `resultados`).

Exemplo para teste rápido:

    python -m scripts.comparar_vizinhancas --instancias pequena --execucoes 5 --orcamento 10000

Arquivo gerado:
- `resultados/tabela_comparacao_vizinhancas.csv`: tabela consolidada com métricas agrupadas (médias, desvios, medianas, melhor $h$, passos médios, ótimos distintos médios e tempo médio).

### Tabelas e figuras do relatório

A ser preenchido: um comando para cada tabela e figura do relatório.
