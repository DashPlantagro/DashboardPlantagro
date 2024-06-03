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
			NFCAB.ESTAB,     		
      		PEMPRESA.FANTASIA, 
            SUM(CASE WHEN EXTRACT(YEAR FROM NFCAB.DTEMISSAO) = EXTRACT(YEAR FROM SYSDATE) THEN NFITEM.VALORTOTAL ELSE 0 END) AS VENDAS_ANO_ATUAL,
    		SUM(CASE WHEN EXTRACT(YEAR FROM NFCAB.DTEMISSAO) = EXTRACT(YEAR FROM SYSDATE) - 1 THEN NFITEM.VALORTOTAL ELSE 0 END) AS VENDAS_ANO_PASSADO
        FROM
            NFCAB
        LEFT JOIN
            PREPRESE ON PREPRESE.REPRESENT = NFCAB.REPRESENT
        JOIN
            NFCFG ON NFCFG.NOTACONF = NFCAB.NOTACONF
        LEFT JOIN
            ITEMTABPRC ON ITEMTABPRC.ESTAB = NFCAB.ESTAB AND ITEMTABPRC.TABPRC = NFCAB.TABPRC
        LEFT JOIN
            NFITEM ON NFITEM.SEQNOTA = NFCAB.SEQNOTA AND NFITEM.ESTAB = NFCAB.ESTAB
        LEFT JOIN PEMPRESA
        	ON PEMPRESA.EMPRESA = NFCAB.ESTAB 
        WHERE
            (NFCAB.DTEMISSAO BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD') OR
            NFCAB.DTEMISSAO BETWEEN ADD_MONTHS(TO_DATE('{start_date}', 'YYYY-MM-DD'), -12) AND ADD_MONTHS(TO_DATE('{end_date}', 'YYYY-MM-DD'), -12))
            AND NFCFG.ENTRADASAIDA = 'S'
        GROUP BY 
			NFCAB.ESTAB,PEMPRESA.FANTASIA
		ORDER BY 
			NFCAB.ESTAB     		

    """
    df = pd.read_sql(query, conn)


    
    # Redefinir o índice diretamente após a leitura, se necessário
    df.reset_index(inplace=True)

    # Depois de pivotar os dados
    df_pivot = df.pivot_table(index=['ESTAB', 'FANTASIA']).reset_index()

    # Assegurar que ambas as colunas 'VENDAS_ESTE_ANO' e 'VENDAS_ANO_PASSADO' existam
    if 'VENDAS_ANO_ATUAL' not in df_pivot.columns:
        df_pivot['VENDAS_ANO_ATUAL'] = 0
    if 'VENDAS_ANO_PASSADO' not in df_pivot.columns:
        df_pivot['VENDAS_ANO_PASSADO'] = 0

    # Substitua valores NaN por 0
    df_pivot.fillna(0, inplace=True)

   # Definir a localidade para Português do Brasil para formatação de números
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        print("Locale pt_BR não disponível. Usando locale padrão.")

    # Truncar e criar hovertext após pivotar os dados
    df_pivot = df.pivot_table(index=['ESTAB', 'FANTASIA']).reset_index()

    # Substitua valores NaN por 0 e assegure a existência das colunas
    df_pivot.fillna(0, inplace=True)
    df_pivot['VENDAS_ANO_ATUAL'] = df_pivot.get('VENDAS_ANO_ATUAL', 0)
    df_pivot['VENDAS_ANO_PASSADO'] = df_pivot.get('VENDAS_ANO_PASSADO', 0)

    # Truncar nomes longos com elipses
    df_pivot['FANTASIA_TRUNC'] = df_pivot['FANTASIA'].apply(lambda x: (x[:12] + '...') if len(x) > 15 else x)

    # Formatar hovertext com nome truncado e valor em reais
    df_pivot['HOVER_TEXT'] = df_pivot.apply(lambda row: f"Empresa: {row['FANTASIA_TRUNC']}<br>Total Vendas: R$ {locale.format_string('%.2f', row['VENDAS_ANO_ATUAL'], grouping=True)}", axis=1)
    # Formatar hovertext com nome completo, nome truncado e valor em reais
    df_pivot['HOVER_TEXT'] = df_pivot.apply(lambda row: f"Empresa: {row['FANTASIA']}<br>Total Vendas: R$ {locale.format_string('%.2f', row['VENDAS_ANO_ATUAL'], grouping=True)}", axis=1)



    # Criando os traces para o gráfico com hovertext
    trace_este_ano = go.Bar(
        x=df_pivot['FANTASIA_TRUNC'],
        y=df_pivot['VENDAS_ANO_ATUAL'],
        marker=dict(color='#17BECF'),
        name='Este Ano',
        hovertext=df_pivot['HOVER_TEXT'],
        hoverinfo="text"
    )
    trace_ano_passado = go.Bar(
        x=df_pivot['FANTASIA_TRUNC'],
        y=df_pivot['VENDAS_ANO_PASSADO'],
        marker=dict(color='#7F7F7F'),
        name='Ano Passado',
        hovertext=df_pivot['HOVER_TEXT'],
        hoverinfo="text"
    )

    # Criando o gráfico
    fig = go.Figure([trace_este_ano, trace_ano_passado])

    # Configurando o layout do gráfico para o tema Darkly
    fig.update_layout(
        paper_bgcolor='#333',  # Cor de fundo do gráfico
        plot_bgcolor='#333',  # Cor de fundo da área de plotagem
        font=dict(color='white'),  # Cor da fonte para melhor contraste
        title='Comparando Vendas: Este Ano vs Ano Passado',
        title_font=dict(size=20, color='white'),  # Ajustando a cor e tamanho do título
        xaxis=dict(
            title='Empresa',
            title_font=dict(size=18, color='white'),  # Ajustando a cor e tamanho do título do eixo X
            tickfont=dict(color='white')  # Ajustando a cor dos ticks do eixo X
        ),
        yaxis=dict(
            title='Total de Vendas',
            title_font=dict(size=18, color='white'),  # Ajustando a cor e tamanho do título do eixo Y
            tickfont=dict(color='white')  # Ajustando a cor dos ticks do eixo Y
        ),
        legend_title='Período',
        legend_title_font_color='white',  # Ajustando a cor do título da legenda
        legend=dict(
            font=dict(
                color='white'  # Ajustando a cor dos textos da legenda
            )
        ),
        barmode='group',  # Agrupando as barras
        dragmode=False  # Define o modo de arraste para falso, desabilitando o arraste
    )

    # Para a propriedade `scrollZoom`, é necessário configurá-la no componente dcc.Graph no Dash, se estiver usando Dash
    return html.Div(
        dcc.Graph(
            figure=fig,
            config={
                'scrollZoom': True  # Permite zoom com scroll do mouse
            }
        )
    )