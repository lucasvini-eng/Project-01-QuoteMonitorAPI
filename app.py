import os
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Quote Analytics ($) - FastAPI & SQLite",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css(file_path="style.css"):
    resolved_path = os.path.join(os.path.dirname(__file__), file_path)
    if not os.path.exists(resolved_path):
        resolved_path = file_path
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Não foi possível carregar o arquivo CSS ({file_path}): {e}")

load_css("style.css")

def get_default_api_url():
    try:
        if hasattr(st, "secrets") and "API_URL" in st.secrets:
            return str(st.secrets["API_URL"]).strip()
    except Exception:
        pass
    return os.getenv("API_URL", "http://127.0.0.1:8000").strip()

DEFAULT_API_URL = get_default_api_url()

st.sidebar.markdown("## 🌐 Conexão com API")
api_url = st.sidebar.text_input(
    "URL da API FastAPI (Render ou Local)",
    value=DEFAULT_API_URL,
    help="Endereço da API FastAPI no Render (ex: https://quote-monitor-api.onrender.com) ou local (http://127.0.0.1:8000)"
)

@st.cache_data(ttl=20)
def check_api_health(base_url: str):
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=15)
        if resp.status_code == 200:
            return True, resp.json()
        return False, f"Status code: {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "Tempo limite esgotado. A API no Render pode estar iniciando (cold start de ~40s)."
    except Exception as e:
        return False, str(e)

@st.cache_data(ttl=30)
def fetch_quotes_from_api(base_url: str):
    try:
        endpoint = f"{base_url.rstrip('/')}/api/quotes"
        resp = requests.get(endpoint, timeout=15)
        if resp.status_code == 200:
            payload = resp.json()
            quotes_list = payload.get("data", [])
            if not quotes_list:
                return pd.DataFrame(), "Nenhum registro encontrado no banco de dados SQLite."
            
            df = pd.DataFrame(quotes_list)
            df["DATETIME"] = pd.to_datetime(df["datetime"])
            df["VALOR_NUM"] = pd.to_numeric(df["quote_value"])
            df["PERC_NUM"] = pd.to_numeric(df["percent_change"])
            df["MOEDA"] = df["currency"].astype(str)
            df["COTAÇÃO"] = df["raw_quote"].fillna(df["quote_value"].astype(str))
            df["PERCENTUAL"] = df["raw_percent"].fillna(df["percent_change"].apply(lambda p: f"{p:+.2f}%"))
            df["DATE_ONLY"] = df["DATETIME"].dt.date
            df = df.sort_values("DATETIME")
            return df, None
        else:
            return pd.DataFrame(), f"API retornou erro {resp.status_code}: {resp.text}"
    except Exception as e:
        return pd.DataFrame(), f"Falha de conexão com a API: {str(e)}"

is_online, health_info = check_api_health(api_url)
if is_online:
    records_cnt = health_info.get("total_records", 0) if isinstance(health_info, dict) else 0
    st.sidebar.success(f"🟢 **API Online** ({records_cnt} registros)")
else:
    st.sidebar.error("🔴 **API Offline**")
    if "onrender.com" in api_url:
        st.sidebar.warning(
            "⏳ **Aviso Render Free Tier:** No plano gratuito, a API entra em suspensão após 15 minutos sem requisições e leva ~40 segundos para acordar. Aguarde um instante e recarregue."
        )
    else:
        st.sidebar.caption(
            "Para iniciar a API localmente, execute no terminal:\n"
            "```bash\n"
            "uvicorn api:app --reload\n"
            "```"
        )
    if st.sidebar.button("🔁 Tentar Reconectar"):
        st.cache_data.clear()
        st.rerun()

df, error_msg = fetch_quotes_from_api(api_url)

if (df.empty or error_msg) and not is_online:
    try:
        import database
        local_quotes = database.get_quotes()
        if not local_quotes:
            database.sync_sheets_to_sqlite()
            local_quotes = database.get_quotes()
        if local_quotes:
            df = pd.DataFrame(local_quotes)
            df["DATETIME"] = pd.to_datetime(df["datetime"])
            df["VALOR_NUM"] = pd.to_numeric(df["quote_value"])
            df["PERC_NUM"] = pd.to_numeric(df["percent_change"])
            df["MOEDA"] = df["currency"].astype(str)
            df["COTAÇÃO"] = df["raw_quote"].fillna(df["quote_value"].astype(str))
            df["PERCENTUAL"] = df["raw_percent"].fillna(df["percent_change"].apply(lambda p: f"{p:+.2f}%"))
            df["DATE_ONLY"] = df["DATETIME"].dt.date
            df = df.sort_values("DATETIME")
            st.sidebar.info("💾 Operando em contingência com banco de dados SQLite local")
            error_msg = None
    except Exception:
        pass

col_header, col_refresh = st.columns([4, 1])
with col_header:
    st.markdown('<div class="main-title">Quote Analytics <span>($)</span></div>', unsafe_allow_html=1)
    st.markdown('<div class="subtitle-text">Monitoramento integrado via <b>FastAPI pública</b> e banco <b>SQLite</b></div>', unsafe_allow_html=1)

with col_refresh:
    if st.button("🔄 Atualizar Dados"):
        try:
            sync_resp = requests.post(f"{api_url.rstrip('/')}/api/quotes/sync", timeout=15)
            if sync_resp.status_code == 200:
                st.toast("✅ Banco de dados SQLite sincronizado com sucesso!")
            else:
                st.toast(f"⚠️ Sincronização retornou status {sync_resp.status_code}")
        except Exception as e:
            st.toast(f"⚠️ Erro ao acionar sincronização na API: {e}")
        st.cache_data.clear()
        st.rerun()

if error_msg:
    st.warning(f"⚠️ {error_msg}")
    st.info(
        "💡 **Dica:** Certifique-se de que a API FastAPI está em execução:\n"
        "`uvicorn api:app --host 0.0.0.0 --port 8000 --reload`\n\n"
        "Acesse a documentação interativa da API em: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)"
    )

st.markdown("### 📊 Cotações Atuais")

fiat_symbols = ["USD", "EUR", "CNY"]
crypto_symbols = ["BTC", "ETH"]
all_symbols = fiat_symbols + crypto_symbols

metric_cols = st.columns(len(all_symbols))

for idx, symbol in enumerate(all_symbols):
    with metric_cols[idx]:
        sub_df = df[df["MOEDA"] == symbol] if not df.empty else pd.DataFrame()
        if not sub_df.empty:
            latest_row = sub_df.iloc[-1]
            val = latest_row["VALOR_NUM"]
            perc = latest_row["PERC_NUM"]
            
            if symbol in crypto_symbols:
                val_formatted = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                val_formatted = f"R$ {val:.4f}".replace(".", ",")
            
            badge_class = "positive" if perc > 0 else ("negative" if perc < 0 else "neutral")
            perc_prefix = "+" if perc > 0 else ""
            perc_formatted = f"{perc_prefix}{perc:.2f}%".replace(".", ",")
        else:
            val_formatted = "N/A"
            perc_formatted = "0.00%"
            badge_class = "neutral"

        card_html = f"""
        <div class="quote-card">
            <div class="quote-header">
                <span class="quote-symbol">{symbol}/BRL</span>
                <span class="quote-badge {badge_class}">{perc_formatted}</span>
            </div>
            <div class="quote-value">{val_formatted}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=1)

st.markdown("<br>", unsafe_allow_html=1)

st.sidebar.markdown("## ⚙️ Filtros de Análise")

if not df.empty:
    min_date = df["DATE_ONLY"].min()
    max_date = df["DATE_ONLY"].max()
else:
    min_date = datetime.now().date() - timedelta(days=30)
    max_date = datetime.now().date()

date_range = st.sidebar.date_input(
    "📅 Selecione o Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = df[(df["DATE_ONLY"] >= start_d) & (df["DATE_ONLY"] <= end_d)]
else:
    filtered_df = df.copy()

selected_fiats = st.sidebar.multiselect(
    "💵 Moedas Tradicionais",
    options=fiat_symbols,
    default=fiat_symbols
)

selected_cryptos = st.sidebar.multiselect(
    "🪙 Criptomoedas",
    options=crypto_symbols,
    default=crypto_symbols
)

plotly_theme = dict(
    paper_bgcolor="#13151b",
    plot_bgcolor="#13151b",
    font=dict(color="#f1f5f9", family="Inter, sans-serif"),
    xaxis=dict(
        gridcolor="#1e293b",
        zerolinecolor="#1e293b",
        showline=True,
        linecolor="rgba(184, 110, 40, 0.35)"
    ),
    yaxis=dict(
        gridcolor="#1e293b",
        zerolinecolor="#1e293b",
        showline=True,
        linecolor="rgba(184, 110, 40, 0.35)"
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8")
    ),
    margin=dict(l=40, r=20, t=40, b=40)
)

st.markdown("### 📈 Histórico de Cotações")

tab_fiat, tab_crypto = st.tabs(["💵 Moedas Tradicionais (FIAT)", "🪙 Criptomoedas"])

with tab_fiat:
    fiat_df = filtered_df[filtered_df["MOEDA"].isin(selected_fiats)] if not filtered_df.empty else pd.DataFrame()
    
    if not fiat_df.empty:
        fig_fiat = go.Figure()
        
        fiat_colors = {
            "USD": "#b86e28",
            "EUR": "#38bdf8",
            "CNY": "#a855f7"
        }
        
        for symbol in selected_fiats:
            sub = fiat_df[fiat_df["MOEDA"] == symbol]
            if not sub.empty:
                fig_fiat.add_trace(go.Scatter(
                    x=sub["DATETIME"],
                    y=sub["VALOR_NUM"],
                    mode="lines+markers",
                    name=f"{symbol}/BRL",
                    line=dict(color=fiat_colors.get(symbol, "#b86e28"), width=2.5, shape='spline'),
                    marker=dict(size=5),
                    hovertemplate="%{x|%d/%m %H:%M}<br><b>%{y:.4f} BRL</b><extra></extra>"
                ))
        
        fig_fiat.update_layout(
            title=dict(text="Moedas FIAT (USD, EUR, CNY) vs BRL", font=dict(size=15, color="#b86e28")),
            yaxis_title="Valor (R$)",
            xaxis_title="Data e Hora",
            hovermode="x unified",
            **plotly_theme
        )
        st.plotly_chart(fig_fiat, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período e moedas selecionadas.")

with tab_crypto:
    crypto_df = filtered_df[filtered_df["MOEDA"].isin(selected_cryptos)] if not filtered_df.empty else pd.DataFrame()
    
    if not crypto_df.empty:
        fig_crypto = go.Figure()
        
        crypto_colors = {
            "BTC": "#f97316",
            "ETH": "#818cf8"
        }
        
        for symbol in selected_cryptos:
            sub = crypto_df[crypto_df["MOEDA"] == symbol]
            if not sub.empty:
                fig_crypto.add_trace(go.Scatter(
                    x=sub["DATETIME"],
                    y=sub["VALOR_NUM"],
                    mode="lines+markers",
                    name=f"{symbol}/BRL",
                    line=dict(color=crypto_colors.get(symbol, "#f97316"), width=2.5, shape='spline'),
                    marker=dict(size=5),
                    hovertemplate="%{x|%d/%m %H:%M}<br><b>R$ %{y:,.2f}</b><extra></extra>"
                ))
        
        fig_crypto.update_layout(
            title=dict(text="Criptomoedas (BTC, ETH) vs BRL", font=dict(size=15, color="#b86e28")),
            yaxis_title="Valor (R$)",
            xaxis_title="Data e Hora",
            hovermode="x unified",
            **plotly_theme
        )
        st.plotly_chart(fig_crypto, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período e criptomoedas selecionadas.")

st.markdown("<br><hr style='border-color: rgba(184, 110, 40, 0.2);'><p style='text-align: center; color: #64748b; font-size: 0.8rem;'>Quote Analytics Dashboard • Desenvolvido com Streamlit, FastAPI e SQLite</p>", unsafe_allow_html=1)
