#importação das bibliotecas
import streamlit as st
import pandas as pd
import plotly.express as px 

# carregando dados
@st.cache_data
def carregar_dados():
    df = pd.read_excel("Base_Vendas_2024.xlsx", sheet_name="Vendas_dos_Mercados_2024")
    df['Data da Venda'] = pd.to_datetime(df['Data da Venda'])  # corrigido para atualizar a coluna existente
    df['Ano-Mês'] = df['Data da Venda'].dt.to_period('M').astype(str)
    return df

df = carregar_dados()

st.title("Painel de Vendas")

# Importações

st.sidebar.header("Filtros")
ufs = st.sidebar.multiselect("Selecione os estados:", options=df['UF da Compra'].unique(), default=df['UF da Compra'].unique())
lojas = st.sidebar.multiselect("Selecione as lojas:", options=df['Nome da Loja'].unique(), default=df['Nome da Loja'].unique())
data_min = df['Data da Venda'].min()
data_max = df['Data da Venda'].max()

data_range = st.sidebar.date_input(
    "Período da venda:",
    [data_min, data_max],
    min_value=data_min,
    max_value=data_max,
    format="DD/MM/YYYY"
)

# Etapa verificaçao 
if len(data_range) != 2:
    st.warning("Por favor, selecione o intervalo >>>(data inicial e data final)<<<")
    st.stop()

# Aplicando filtros 
df_filtrado = df[
    (df['UF da Compra'].isin(ufs)) &
    (df['Nome da Loja'].isin(lojas)) &
    (df['Data da Venda'] >= pd.to_datetime(data_range[0])) &
    (df['Data da Venda'] <= pd.to_datetime(data_range[1]))
]

# 1. Total vendido
total_vendido = df_filtrado['Valor da Venda'].sum()
st.metric("Total Vendido (R$)", f"R$ {total_vendido:,.2f}")

# 2. Vendas por loja
vendas_por_loja = df_filtrado.groupby('Nome da Loja')['Valor da Venda'].sum().reset_index().sort_values(by='Valor da Venda', ascending=False)
st.subheader("Vendas por Loja")
st.dataframe(vendas_por_loja.style.format({"Valor da Venda": "R$ {:,.2f}"}), use_container_width=True)

# 3. Resumo por estado
estados_df = df_filtrado.groupby('UF da Compra').agg(
    Valor_Total=('Valor da Venda', 'sum'),
    Quantidade_de_Vendas=('Quantidade', 'sum')
).reset_index()
estados_df['Ticket Médio'] = estados_df['Valor_Total'] / estados_df['Quantidade_de_Vendas']

st.subheader("Resumo por Estado")
st.dataframe(
    estados_df.style.format({
        "Valor_Total": "R$ {:,.2f}",
        "Ticket Médio": "R$ {:,.2f}"
    }),
    use_container_width=True
)

# 4. Gráfico de evolução mensal
evolucao_mensal = df_filtrado.groupby('Ano-Mês')['Valor da Venda'].sum().reset_index()
fig_linha = px.line(evolucao_mensal, x='Ano-Mês', y='Valor da Venda', title='Evolução das Vendas Mensais', markers=True)
fig_linha.update_layout(
    xaxis_title='Mês',
    yaxis_title='Valor (R$)',
    yaxis_tickprefix='R$ ',
    yaxis_tickformat=',.2f'
)
st.plotly_chart(fig_linha, use_container_width=True)

# 5. Mês com maior faturamento
if not evolucao_mensal.empty:
    mes_maior = evolucao_mensal.loc[evolucao_mensal['Valor da Venda'].idxmax()]
    st.info(f"Mês com maior faturamento: **{mes_maior['Ano-Mês']}** com **R$ {mes_maior['Valor da Venda']:,.2f}**")
else:
    st.warning("Nenhum dado disponível.")
