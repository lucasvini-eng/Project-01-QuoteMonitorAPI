# 📊 Quote Analytics — Pipeline de Cotações, SQLite, FastAPI & Streamlit

Painel interativo e pipeline de dados para **monitoramento de cotações de moedas tradicionais (FIAT) e criptomoedas**, com persistência relacional em **SQLite**, camada de distribuição via **API REST pública em FastAPI** e visualização em tempo real no **Streamlit**.

---

## 📑 Sumário

- [Visão Geral](#-visão-geral)
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Modelagem do Banco de Dados (SQLite)](#-modelagem-do-banco-de-dados-sqlite)
- [Documentação da API Pública (FastAPI)](#-documentação-da-api-pública-fastapi)
  - [Endpoints e Parâmetros](#endpoints-e-parâmetros)
  - [Exemplos de Requisições](#exemplos-de-requisições)
- [Painel Streamlit](#-painel-streamlit)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Guia de Instalação e Execução](#-guia-de-instalação-e-execução)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Licença](#-licença)

---

## 📌 Visão Geral

O projeto opera em um ciclo contínuo de coleta, tratamento, armazenamento e disponibilização de dados:

1. **Extração & Carga Original (ETL)**: Coleta cotações de USD, EUR, CNY, BTC e ETH e sincroniza com o Google Sheets.
2. **Normalização & Armazenamento**: Extrai da planilha (ou mock de contingência), higieniza pontuações, casas decimais e percentuais, e armazena os registros no banco **SQLite** (`quotes.db`).
3. **Disponibilização Pública (FastAPI)**: Servidor assíncrono REST com CORS habilitado, documentação interativa Swagger e endpoints para consultas pontuais, históricas e sincronizações sob demanda.
4. **Consumo & BI (Streamlit)**: Dashboard responsivo com tema escuro personalizado (`style.css`), que consome diretamente a API FastAPI, exibe KPIs e gera gráficos interativos com Plotly.

---

## 🏛️ Arquitetura da Solução

```text
  +-----------------------+
  |    Google Finance     |
  |  (Scraper / Selenium) |
  +-----------------------+
              |
              ▼
  +-----------------------+
  |     Google Sheets     |  <-- Planilha pública / repositório em nuvem
  +-----------------------+
              |
              | (sync_sheets_to_sqlite)
              ▼
  +-----------------------+
  |     SQLite (DB)       |  <-- quotes.db
  |   Tabela: quotes      |      Índices por data e moeda
  +-----------------------+      Chave única: (datetime, currency)
              ▲
              | (queries / ORM simples)
              ▼
  +-----------------------+
  |    FastAPI Pública    |  <-- api.py
  |   Uvicorn (Port 8000) |      Swagger (/docs) & CORS aberto
  +-----------------------+
              ▲
              | (Requisições HTTP / JSON)
              ▼
  +-----------------------+
  |   Streamlit App       |  <-- app.py
  |   (Porta 8501)        |      Filtros, Cards KPI e Plotly Charts
  +-----------------------+
```

---

## 📂 Estrutura do Projeto

```text
01-Quote-monitor-API/
├── api.py              # Servidor FastAPI com rotas REST e documentação OpenAPI
├── database.py         # Módulo SQLite, limpeza numérica e sincronização de dados
├── app.py              # Interface visual interativa em Streamlit integrada à API
├── init_db.py          # Script CLI para inicialização e seed rápido do banco
├── style.css           # Folha de estilo customizada para a UI (tema dark/bronze)
├── requirements.txt    # Lista de dependências Python do projeto
├── quotes.db           # Banco de dados SQLite local (gerado automaticamente)
└── README.md           # Documentação completa da solução
```

---

## 💾 Modelagem do Banco de Dados (SQLite)

O banco é criado e configurado automaticamente pelo módulo [`database.py`](file:///d:/AREA_DE_TRABALHO/01-Quote-monitor-API/database.py).

### Tabela `quotes`

```sql
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,         -- Formato ISO: YYYY-MM-DD HH:MM:SS
    currency TEXT NOT NULL,         -- Ex: USD, EUR, CNY, BTC, ETH
    quote_value REAL NOT NULL,      -- Valor float normalizado em BRL
    percent_change REAL NOT NULL,   -- Variação percentual tratada (ex: +1.25)
    raw_date TEXT,                  -- Valor de data bruto original
    raw_quote TEXT,                 -- Valor da cotação bruto original
    raw_percent TEXT,               -- Percentual bruto original
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(datetime, currency) ON CONFLICT REPLACE
);

CREATE INDEX IF NOT EXISTS idx_quotes_currency ON quotes(currency);
CREATE INDEX IF NOT EXISTS idx_quotes_datetime ON quotes(datetime);
```

> **Garantia de integridade:** A restrição `UNIQUE(datetime, currency)` com estratégia `REPLACE` impede registros duplicados caso uma mesma cotação seja importada repetidas vezes.

---

## 🌐 Documentação da API Pública (FastAPI)

A API provê acesso público a todas as informações armazenadas no banco SQLite com suporte a **CORS total** (`allow_origins=["*"]`).

- **Swagger UI (Interativo):** `http://127.0.0.1:8000/docs`
- **Redoc:** `http://127.0.0.1:8000/redoc`

### Endpoints e Parâmetros

| Método | Rota | Descrição | Parâmetros / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Boas-vindas e mapa dos endpoints disponíveis | Nenhum |
| `GET` | `/health` | Status de saúde, total de cotações e caminho do banco | Nenhum |
| `GET` | `/api/currencies` | Lista com as moedas cadastradas no banco | Nenhum |
| `GET` | `/api/quotes` | Histórico de cotações com filtros | `currency`, `start_date`, `end_date`, `limit` |
| `GET` | `/api/quotes/latest` | Cotação mais recente de cada moeda cadastrada | Nenhum |
| `POST` | `/api/quotes/sync` | Dispara sincronização da planilha com o SQLite | `sheets_url` (opcional no corpo JSON) |
| `POST` | `/api/quotes` | Insere manualmente uma nova cotação | JSON com `currency`, `quote_value`, `percent_change` |

---

### Exemplos de Requisições

#### 1. Consultar Cotações com Filtros (`GET /api/quotes`)
```bash
curl -X GET "http://127.0.0.1:8000/api/quotes?currency=USD&start_date=2026-10-01&end_date=2026-11-04&limit=10"
```
**Resposta JSON:**
```json
{
  "total": 1,
  "data": [
    {
      "id": 12,
      "datetime": "2026-11-04 15:30:00",
      "currency": "USD",
      "quote_value": 5.4820,
      "percent_change": 0.35,
      "raw_date": "04/11/2026 15:30:00",
      "raw_quote": "5,4820",
      "raw_percent": "+0,35%"
    }
  ]
}
```

#### 2. Obter as Últimas Cotações (`GET /api/quotes/latest`)
```bash
curl -X GET "http://127.0.0.1:8000/api/quotes/latest"
```
**Resposta JSON:**
```json
[
  {
    "id": 45,
    "datetime": "2026-11-04 18:00:00",
    "currency": "BTC",
    "quote_value": 352400.0,
    "percent_change": 1.25,
    "raw_date": "04/11/2026 18:00:00",
    "raw_quote": "352.400,00",
    "raw_percent": "+1,25%"
  },
  {
    "id": 46,
    "datetime": "2026-11-04 18:00:00",
    "currency": "USD",
    "quote_value": 5.4650,
    "percent_change": -0.15,
    "raw_date": "04/11/2026 18:00:00",
    "raw_quote": "5,4650",
    "raw_percent": "-0,15%"
  }
]
```

#### 3. Sincronizar Planilha com SQLite (`POST /api/quotes/sync`)
```bash
curl -X POST "http://127.0.0.1:8000/api/quotes/sync" \
     -H "Content-Type: application/json" \
     -d '{}'
```
**Resposta JSON:**
```json
{
  "status": "success",
  "source": "google_sheets",
  "processed_records": 150,
  "note": null
}
```

#### 4. Cadastrar Cotação Manualmente (`POST /api/quotes`)
```bash
curl -X POST "http://127.0.0.1:8000/api/quotes" \
     -H "Content-Type: application/json" \
     -d '{
       "currency": "EUR",
       "quote_value": 5.9450,
       "percent_change": 0.42
     }'
```

---

## 📊 Painel Streamlit

O arquivo [`app.py`](01-Quote-monitor-API/app.py) é a camada de apresentação do usuário:

- **Indicador de Conexão na Sidebar:** Exibe em tempo real se a API está online (verde com número de registros) ou offline (vermelho com dicas para inicialização).
- **Cards Métricos:** Exibição dinâmica de cotações atuais para USD, EUR, CNY, BTC e ETH, com badges coloridos de oscilação positiva, negativa ou neutra.
- **Filtros Personalizados:** Seleção de intervalo de datas (`st.date_input`) e seleção múltipla de moedas FIAT e Criptos.
- **Gráficos Interativos (Plotly):** Séries temporais em abas separadas para moedas tradicionais e criptomoedas.
- **Sincronização Integrada:** O botão **"🔄 Atualizar Dados"** dispara uma chamada HTTP `POST` para `/api/quotes/sync`, forçando a API a reler a planilha e atualizar o SQLite, renovando o cache do Streamlit.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Descrição |
| :--- | :--- |
| **Python 3.10+** | Linguagem base da aplicação |
| **SQLite 3** | Motor de banco de dados relacional embutido e sem necessidade de servidor externo |
| **FastAPI** | Framework web assíncrono de alta performance para a construção da API REST |
| **Uvicorn** | Servidor ASGI para produção e desenvolvimento local |
| **Streamlit** | Framework para interfaces e dashboards analíticos de dados |
| **Pandas** | Manipulação, transformação e limpeza de séries tabulares |
| **Plotly** | Visualizações gráficas interativas e responsivas |
| **Requests** | Cliente HTTP utilizado pelo Streamlit para consumir a FastAPI |
| **OpenPyXL** | Leitura e parsing de arquivos de planilha XLSX |

---

## 🚀 Guia de Instalação e Execução

### 1. Clonar o Repositório ou Acessar a Pasta
```bash
cd d:\AREA_DE_TRABALHO\01-Quote-monitor-API
```

### 2. Criar e Ativar um Ambiente Virtual (Recomendado)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / MacOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Inicializar o Banco de Dados (Opcional)
Se desejar testar e povoar o banco SQLite antes de iniciar o servidor:
```bash
python init_db.py
```
*(Nota: A API FastAPI realiza essa sincronização automaticamente na inicialização se o banco estiver vazio).*

### 5. Iniciar a API Pública com FastAPI
Em um terminal, execute:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```
- A API estará disponível em: `http://127.0.0.1:8000`
- Documentação interativa Swagger: `http://127.0.0.1:8000/docs`

### 6. Iniciar o Dashboard Streamlit
Em outro terminal (com o ambiente virtual ativo):
```bash
streamlit run app.py
```
O painel abrirá automaticamente no navegador no endereço `http://localhost:8501`.

---

## ⚙️ Variáveis de Ambiente

As seguintes variáveis de ambiente podem ser customizadas conforme a necessidade:

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `DATABASE_PATH` | `quotes.db` | Caminho do arquivo de banco de dados SQLite local |
| `SHEETS_URL` | *(URL pública XLSX do Google Sheets)* | URL de onde os dados brutos são extraídos |
| `API_URL` | `http://127.0.0.1:8000` | URL da API FastAPI consumida pelo Streamlit |

Exemplo de definição no terminal PowerShell:
```powershell
$env:API_URL="http://127.0.0.1:8000"
$env:DATABASE_PATH="quotes.db"
```

---

## 📄 Licença

Este projeto é distribuído sob a licença **MIT**. Consulte o arquivo de licença para mais detalhes.

<div align="center">

**Quote Analytics** • *Construído com Python, SQLite, FastAPI, Streamlit, Pandas e Plotly*

</div>
