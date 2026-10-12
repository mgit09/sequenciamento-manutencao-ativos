# Sequenciamento de Manutenção de Ativos

Trabalho prático realizado no contexto da disciplina de Fundamentos de 
Inteligência Artificial (UFMG).

Uma concessionária de energia precisa executar a manutenção preventiva de
vários ativos (religadores, transformadores, chaves seccionadoras) com uma
única equipe, que atende um ativo por vez. Cada ativo tem localização,
duração do serviço, prazo e peso de criticidade. O objetivo é encontrar a
ordem de visita que minimiza o atraso ponderado total.

Comparamos três algoritmos em três instâncias (12, 50 e 150 ativos):
descida gulosa com reinício aleatório, simulated annealing e algoritmo genético.

## Como executar

É necessário ter Python 3.10 ou superior. Na pasta do projeto, crie e ative
um ambiente virtual e instale as dependências:

**Linux / macOS**

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

**Windows (PowerShell)**

    py -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Se o PowerShell bloquear a ativação, rode antes
`Set-ExecutionPolicy -Scope Process RemoteSigned`. No prompt de comando
(cmd), use `.venv\Scripts\activate.bat`.

Para verificar a instalação e a função de avaliação:

    python testes.py

## Estrutura do projeto

```txt
sequenciamento-manutencao-ativos
│
├── instancias/                  # Instâncias fornecidas (manutencao_*.txt)
├── resultados/                  # Arquivos .csv gerados pelos experimentos
├── src/
│   ├── problema_manutencao.py   # Modelo do problema e função de avaliação
│   └── algoritmos/              # Algoritmos utilizados (GA, GD, SA)
│
├── tests/
│   ├── testes.py                # Testes automáticos
│   └── algoritmos/              # Algoritmos utilizados (GA, GD, SA)
│
├── executar_experimentos.py     # Executa tudo e salva os .csv
├── gerar_analises.py            # Lê os .csv e gera tabelas, boxplots, curvas, testes estatísticos
│
├── requirements.txt             # Requisitos para rodar os códigos
└── README.md                    
```

## Reprodução dos resultados

A ser preenchido: um comando para cada tabela e figura do relatório.
