import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Definir localidade para formatar moeda brasileira
try:
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')  # Windows
except:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Linux/macOS


# Carregar os dados
@st.cache_data
def carregar_dados():
    df = pd.read_excel("dados/Base_Vendas_2024.xlsx", sheet_name="Vendas_dos_Mercados_2024")
    df['Data da Venda'] = pd.to_datetime(df['Data da Venda'])
    df['Ano-Mês'] = df['Data da Venda'].dt.to_period('M').astype(str)
    return df

df = carregar_dados()

st.title("Painel de Vendas")

# Filtros interativos
st.sidebar.header("Filtros")
ufs = st.sidebar.multiselect("Selecione os estados:", options=df['UF da Compra'].unique(), default=df['UF da Compra'].unique())
lojas = st.sidebar.multiselect("Selecione as lojas:", options=df['Nome da Loja'].unique(), default=df['Nome da Loja'].unique())
data_min = df['Data da Venda'].min()
data_max = df['Data da Venda'].max()
data_range = st.sidebar.date_input("Período da venda:", [data_min, data_max], min_value=data_min, max_value=data_max, format="DD/MM/YYYY")

# Verificar se o usuário selecionou as duas datas
if len(data_range) == 2:
    data_inicio = pd.to_datetime(data_range[0])
    data_fim = pd.to_datetime(data_range[1])

    # Aplicar filtros
    df_filtrado = df[(df['UF da Compra'].isin(ufs)) &
                     (df['Nome da Loja'].isin(lojas)) &
                     (df['Data da Venda'] >= data_inicio) &
                     (df['Data da Venda'] <= data_fim)]
else:
    st.warning("Por favor, selecione a data de início e fim do período.")
    st.stop()

# 1. Total vendido em Reais
total_vendido = df_filtrado['Valor da Venda'].sum()
st.metric("Total Vendido (R$)", locale.currency(total_vendido, grouping=True))

# 2. Valor vendido por cada loja
vendas_por_loja = df_filtrado.groupby('Nome da Loja')['Valor da Venda'].sum().reset_index().sort_values(by='Valor da Venda', ascending=False)
vendas_por_loja['Valor da Venda'] = vendas_por_loja['Valor da Venda'].apply(lambda x: locale.currency(x, grouping=True))
st.subheader("Vendas por Loja")
st.dataframe(vendas_por_loja, use_container_width=True)

# 3. Tabela por estado
estados_df = df_filtrado.groupby('UF da Compra').agg(
    Valor_Total=('Valor da Venda', 'sum'),
    Quantidade_de_Vendas=('Quantidade', 'sum')
).reset_index()
estados_df['Ticket Médio'] = estados_df['Valor_Total'] / estados_df['Quantidade_de_Vendas']
estados_df['Valor_Total'] = estados_df['Valor_Total'].apply(lambda x: locale.currency(x, grouping=True))
estados_df['Ticket Médio'] = estados_df['Ticket Médio'].apply(lambda x: locale.currency(x, grouping=True))
st.subheader("Resumo por Estado")
st.dataframe(estados_df, use_container_width=True)

# 4. Gráfico de linhas - Evolução mensal
evolucao_mensal = df_filtrado.groupby('Ano-Mês')['Valor da Venda'].sum().reset_index()
# evolucao_mensal['Valor da Venda'] = evolucao_mensal['Valor da Venda'].apply(lambda x: locale.currency(x, grouping=True))
fig_linha = px.line(evolucao_mensal, x='Ano-Mês', y='Valor da Venda', title='Evolução das Vendas Mensais', markers=True)
fig_linha.update_layout(
    xaxis_title='Mês',
    yaxis_title='Valor da Venda (R$)')
    #,yaxis_tickformat=',.2f')

fig_linha.update_traces(hovertemplate='Mês: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>')
st.plotly_chart(fig_linha, use_container_width=True)

# 5. Mês com maior faturamento (usando o gráfico de linhas)
if not evolucao_mensal.empty:
    mes_maior = evolucao_mensal.loc[evolucao_mensal['Valor da Venda'].idxmax()]
    st.info(f"📈 Mês com maior faturamento: **{mes_maior['Ano-Mês']}** com **{locale.currency(mes_maior['Valor da Venda'], grouping=True)}**")
else:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
