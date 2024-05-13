import pandas as pd
import locale
from conexao_banco_dados import get_connection
import plotly.graph_objects as go
from dash import dcc, html

# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

def update_chart(start_date=None, end_date=None):

    query = f"""
    SELECT
        pempresa.FANTASIA,
        pempresa.EMPRESA,
        TRUNC(MAX(NFCAB.DTEMISSAO)) AS data_pedido,
        SUM(CASE WHEN EXTRACT(YEAR FROM NFCAB.DTEMISSAO) = EXTRACT(YEAR FROM SYSDATE) THEN NFITEM.VALORTOTAL ELSE 0 END) AS vendas_este_ano,
        SUM(CASE WHEN EXTRACT(YEAR FROM NFCAB.DTEMISSAO) = EXTRACT(YEAR FROM SYSDATE) - 1 THEN NFITEM.VALORTOTAL ELSE 0 END) AS vendas_ano_passado
    FROM
        NFCAB
    JOIN
        pempresa ON NFCAB.ESTAB = pempresa.EMPRESA
    LEFT JOIN
        PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
    LEFT JOIN
        ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
    LEFT JOIN
        NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
    JOIN
        NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
    WHERE 
        (NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        OR NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD'))
        AND NFCFG.ENTRADASAIDA IN 'S'
    GROUP BY 
        pempresa.FANTASIA,
        pempresa.EMPRESA
    ORDER BY 
        TO_NUMBER(pempresa.EMPRESA)

    """
    df = pd.read_sql(query, conn)
    
    # Redefinir o índice diretamente após a leitura, se necessário
    df.reset_index(inplace=True)

    # Pivotar os dados
    df_pivot = df.pivot_table(index=['EMPRESA', 'FANTASIA']).reset_index()

    # Assegurar que ambas as colunas 'ESTE_ANO' e 'ANO_PASSADO' existam
    if 'VENDAS_ESTE_ANO' not in df_pivot.columns:
        df_pivot['VENDAS_ESTE_ANO'] = 0
    if 'VENDAS_ANO_PASSADO' not in df_pivot.columns:
        df_pivot['VENDAS_ANO_PASSADO'] = 0

    # Substitua valores NaN por 0
    df_pivot.fillna(0, inplace=True)

    # Criando os traces para o gráfico com cores adaptadas ao tema DARKLY
    trace_este_ano = go.Bar(x=df_pivot['FANTASIA'], y=df_pivot['VENDAS_ESTE_ANO'], marker=dict(color='#17BECF'), name='Este Ano')
    trace_ano_passado = go.Bar(x=df_pivot['FANTASIA'], y=df_pivot['VENDAS_ANO_PASSADO'], marker=dict(color='#7F7F7F'), name='Ano Passado')

    # Criando o gráfico
    fig = go.Figure([trace_este_ano, trace_ano_passado])

    # Configurando layout do gráfico para o tema DARKLY
    fig.update_layout(
        paper_bgcolor='#222',  # Cor de fundo do gráfico
        plot_bgcolor='#222',  # Cor de fundo da área de plotagem
        font=dict(color='#DDD'),  # Cor da fonte para melhor contraste
        title='Comparando Vendas: Este Ano vs Ano Passado',
        title_font=dict(size=20, color='#FFF'),  # Ajustando a cor e tamanho do título
        xaxis=dict(
            title='Empresa',
            title_font=dict(size=18, color='#DDD'),  # Ajustando a cor e tamanho do título do eixo X
            tickfont=dict(color='#DDD')  # Ajustando a cor dos ticks do eixo X
        ),
        yaxis=dict(
            title='Total de Vendas',
            title_font=dict(size=18, color='#DDD'),  # Ajustando a cor e tamanho do título do eixo Y
            tickfont=dict(color='#DDD')  # Ajustando a cor dos ticks do eixo Y
        ),
        legend_title='Período',
        legend_title_font_color='#DDD',  # Ajustando a cor do título da legenda
        legend=dict(
            font=dict(
                color='#DDD'  # Ajustando a cor dos textos da legenda
            )
        ),
        dragmode=False  # Define o modo de arraste para falso, desabilitando o arraste
    )

    # Para a propriedade `scrollZoom`, é necessário configurá-la no componente dcc.Graph no Dash, se estiver usando Dash
    
    return html.Div(
        dcc.Graph(
            figure=fig,
            config={
                'scrollZoom': False # Permite zoom com scroll do mouse
            }
        )
    )
