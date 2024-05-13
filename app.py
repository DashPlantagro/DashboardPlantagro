import pandas as pd
import dash_bootstrap_components as dbc
import locale
import top_5_Clientes_mais_compraram
import vendas_diarias_por_filial
import vendas_mensais_por_filial
import pedidos_pendente_de_baixa
import vendas_anuais_por_filial
import valor_liquido_por_conceito_cliente
import valor_liquido_por_vendedor
import valor_liquido_agrupamento_produtos
import valor_liquido_por_produto
import mapa_vendas_cliente
import mapa_compras_fornecedor
import plotly.express as px
import comparando_vendas_periodo_atual_x_ano_passado
import total_devolucao_por_filial
import total_despesas_por_filial
import valor_total_transacao_cnpf_cpf
import distribuicao_clientes_por_regiao
import crescimento_base_clientes
import indice_lealdade_cliente
import total_marca_comprados
import total_produtos_comprados
import curva_abc_produtos
import curva_abc_fornecedores



from total_clientes_empresa import buscar_total_clientes
from total_transacoes_por_periodo import buscar_total_transacoes_periodo
from valor_total_de_todos_os_pedidos import sumarizacao_total_dos_pedidos
from valor_de_compras_empresa import valor_total_das_compras
from saving import valor_total_saving
from conexao_banco_dados import get_connection
from datetime import datetime
from dash import Dash, dcc, html, Input, Output
from valor_duplicatas_vencidas_em_determinado_periodo import valor_total_duplicatas_vencidas
from valor_duplicatas_a_pagar_vencidas import valor_total_contas_a_pagar_vencidas
from meta_atingida import total_metas, create_gauge_chart_with_pointer
from apscheduler.schedulers.background import BackgroundScheduler




# Definir a localização para pt_BR
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Estabelecer a conexão com o banco de dados Oracle
conn = get_connection()

# Inicializar o aplicativo Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
app.title = 'DashBoard Plantagro'  # Altera o título da aba do navegador
server = app.server

# Funções de Atualização
def update_app():
    print('CAIU AQUI::')
    print('-----------------------------------------')
    print("Aplicativo atualizado em:", datetime.now())
    print('-----------------------------------------')

# Definir a data atual
data_atual = datetime.today().date()

# Obter o primeiro dia do mês corrente
primeiro_dia_mes_corrente = datetime.today().replace(day=1).date()

total_clientes = buscar_total_clientes()

# ============INICIO CRIAÇÃO DOS FILTROS============ #
# ============= REPRESENTANTE ================ #
def carregar_representantes():
    query = """
        SELECT 
            EMPRESA, 
            REPRESENT, 
            DESCRICAO, 
            DTINATIVO
        FROM 
            PREPRESE p 
        WHERE
            p.DTINATIVO IS NULL
        ORDER BY
            TO_NUMBER(REPRESENT)
            """
    df = pd.read_sql(query, conn)
    # Ajustando para usar as colunas corretas para label e value
    return [{'label': f"{row['REPRESENT']} - {row['DESCRICAO']}", 'value': row['REPRESENT']} for index, row in df.iterrows()]

representantes_options = carregar_representantes()

# ============= EMPRESA ================ #
def carregar_empresas():
    query = """ 
        SELECT 
            empresa, 
            FANTASIA 
        FROM 
            PEMPRESA
            """
    df = pd.read_sql(query, conn)

    return [{'label': f"{row['EMPRESA']} - {row['FANTASIA']}", 'value': row['EMPRESA']} for index, row in df.iterrows()]

empresa_options = carregar_empresas()

# ============= TABELA DE PREÇO ================ #
def carregar_tabela_preco():
    query = """
            SELECT 
                ITEMTABPRC.TABPRC,
                ITEMTABPRC.DESCRICAO 
            FROM 
                ITEMTABPRC 
            GROUP BY 
                ITEMTABPRC.TABPRC, 
                ITEMTABPRC.DESCRICAO
        """
    df = pd.read_sql(query, conn)

    return  [{'label': f"{row['TABPRC']} - {row['DESCRICAO']}", 'value': row['TABPRC']} for index, row in df.iterrows()]

tabela_precos_options = carregar_tabela_preco()

# ============= CONFIGURAÇÃO PEDIDO ================ #
def carregar_configuracao_pedido():
    query = """   SELECT 
                    NFCFG.NOTACONF, 
                    NFCFG.DESCRICAO 
                FROM
                     NFCFG
                WHERE
                     NFCFG.ENTRADASAIDA IN ('S', 'E')
                ORDER BY
                    NFCFG.NOTACONF asc"""
    df = pd.read_sql_query(query, conn)
    return [{'label': f"{row['NOTACONF']} - {row['DESCRICAO']}", 'value': row['NOTACONF']} for index, row in df.iterrows()]
configuracao_pedidos_options = carregar_configuracao_pedido()

# ============FIM CRIAÇÃO DOS FILTROS============ #


# ============ INICIO LAYOUT SEPARADO ============ #
# Simulação de funções que retornariam o layout de cada seção


def layout_vendas():
    return html.Div([
        html.H2("Pedidos", style={"textAlign": "center", "margin": "18px"}),

        dbc.Row([  # Linha para os cards de resumo
            dbc.Col(  # Primeiro card
                dbc.Card([
                    html.H2('Total de Transações por Período', style={"textAlign": "center", "fontSize": "18px"}),
                    html.H3(id='container-total-transacao-por-periodo', style={"textAlign": "center", "fontSize": "24px"})
                ],style={
                    "borderRadius": "15px",  # A sintaxe em camelCase é usada aqui por ser um dicionário Python
                    "overflow": "hidden",
                    "margin": "10px",
                    "padding": "10px",
                    "maxHeight": "100px",
                    "border-radius": "15px"
                }),
                width=6
            ),
            dbc.Col(  # Segundo card
                dbc.Card([
                    html.H2('Total de Vendas no Período', style={"textAlign": "center", "fontSize": "18px"}),
                    html.H3(id='container-valor-total-de-todos-pedidos', style={"textAlign": "center", "fontSize": "24px"})
                ], style={        
                    "margin": "10px", 
                    "padding": "10px", 
                    "maxHeight": "100px",
                    "display": "flex",  
                    "justifyContent": "center",
                    "overflow": "hidden"
                }),
                width=6
            )
        ]),
        
        # Seção de gráficos e dados
        dbc.Row([
            dbc.Col(html.Div(id='container-grafico-top-clientes'), width=6),
            dbc.Col(html.Div(id='container-pedidos-pendentes'), width=6)
        ]),
        dbc.Row([
            dbc.Col(html.Div(id='container-valor-liquido-conceito'), width=6),
            dbc.Col(html.Div(id='container-valor-liquido-vendedor'), width=6)
        ]),
        html.Div(id='container-grafico-comparando-vendas-atuais-x-ano-passado'),
        html.Div(id='total-devolucao-por-filial'),
        html.Div(id='container-grafico-vendas-diarias'),
        html.Div(id='container-grafico-vendas-mensais'),
        html.Div(id='container-grafico-vendas-anuais'),
    ])


def layout_compras():
    return html.Div([
        html.H2("Compras", style={"textAlign": "center", "margin": "20px 0"}),  
        dbc.Card([
            html.H2('Total de Compras no Período', style={"textAlign": "center", "fontSize": "18px"}),
            html.H3(id='container-valor-total-de-compras', style={"textAlign": "center", "fontSize": "24px"})
        ], style={        
            "margin": "10px", 
            "padding": "10px", 
            "maxHeight": "100px",
            "display": "flex",
            "justifyContent": "center",
            "overflow": "hidden"}),
          
        dbc.Card([
            html.H2('Total de Saving no Período', style={"textAlign": "center", "fontSize": "18px"}),
            html.H3(id='container-valor-total-saving', style={"textAlign": "center", "fontSize": "24px"})
        ], style={        
            "margin": "10px", 
            "padding": "10px", 
            "maxHeight": "100px",
            "display": "flex",
            "justifyContent": "center",
            "overflow": "hidden"}),
                      
        html.Div([
            html.Div(id='container-grafico-total-marca-produtos', className='six columns', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ], className='row'),

        html.Div([
            html.Div(id='container-grafico-total-produtos-comprados', className='six columns', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ], className='row'),

        html.Div([
            html.Div(id='container-grafico-abc-produtos', className='six columns', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ], className='row'),

        html.Div([
            html.H2("Mapa de Compras dos Fornecedores", style={"textAlign": "center", "marginTop": "10px"}),
            html.Div(id='container-mapa-compras', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ]),

        html.Div([
            html.Div(id='container-grafico-abc-fornecedores', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ]),
    ])


def layout_estoque():
    return html.Div([

        html.Div([
            html.Div(id='container-valor-liquido-agrupamento-produtos', className='six columns', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ], className='row'),

        html.Div([
            html.Div(id='container-valor-liquido-por-produto', className='six columns', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ], className='row'),
    ])

def layout_clientes():
        return html.Div([
            dbc.Row([
                dbc.Col(dbc.Card([
                    html.H2('Total de Clientes na Empresa', style={"textAlign": "center", "fontSize": "18px"}),
                    html.H3(f'{total_clientes}', id='container-total-clientes-empresa', style={"textAlign": "center", "fontSize": "24px"})
                ], style={        
                    "margin": "10px", 
                    "padding": "10px", 
                    "maxHeight": "100px",
                    "display": "flex",
                    "justifyContent": "center",
                    "overflow": "hidden"})),

                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H4("Ticket Médio por Cliente", className="card-title", style={"fontSize": "14px"}),
                        html.P(id='container-ticket-medio', className="card-text", style={"fontSize": "18px"}),
                    ])
                ], style={        
                    "margin": "10px", 
                    "padding": "10px", 
                    "maxHeight": "100px",
                    "display": "flex",
                    "justifyContent": "center",
                    "overflow": "hidden"})),

                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H4("Total de Clientes Ativos", className="card-title", style={"fontSize": "14px"}),
                        html.P(id='container-total-clientes-ativos-periodo', className="card-text", style={"fontSize": "18px"}),
                    ])
                ], style={        
                    "margin": "10px", 
                    "padding": "10px", 
                    "maxHeight": "100px",
                    "display": "flex",
                    "justifyContent": "center",
                    "overflow": "hidden"})),

                html.Div([
                    html.H2("Vendas CPF & CNPJ", style={"textAlign": "center", "marginTop": "10px"}),
                    html.Div(id='container-valor-total-cpf-cnpj', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
                ]),
                html.Div([
                    html.H2("Mapa de Distribuição de Clientes", style={"textAlign": "center", "marginTop": "10px"}),
                    html.Div(id='container-mapa-clientes-regiao', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
                ]),
                html.Div([
                    html.H2("Crescimento da Base de Clientes", style={"textAlign": "center", "marginTop": "10px"}),
                    html.Div(id='container-crescimento-clientes', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
                ]),
        ]),
            

    ])


def layout_contas():
    return html.Div([
            html.H2("Contas", style={"textAlign": "center", "margin": "20px 0"}),  
            dbc.Card([
            dbc.CardBody([
                    html.H2('Total de Duplicatas a Receber Vencidas no Período', style={"textAlign": "center", "fontSize": "18px"}),
                    html.H3(id='container-valor-total-duplicatas-vencidas', style={"textAlign": "center", "fontSize": "18px"})
                ])
            ], style={        
                "margin": "10px", 
                "padding": "10px", 
                "maxHeight": "100px",
                "display": "flex",
                "justifyContent": "center",
                "overflow": "hidden"}),

            dbc.Card([
                html.H2('Total de Duplicatas a Pagar Vencidas no Período', style={"textAlign": "center", "fontSize": "18px"}),
                html.H3(id='container-valor-total-duplicatas-a-pagar-vencidas', style={"textAlign": "center", "fontSize": "18px"})
            ], style={        
                "margin": "10px", 
                "padding": "10px", 
                "maxHeight": "100px",
                "display": "flex",
                "justifyContent": "center",
                "overflow": "hidden"}),
        html.Div([
            html.Div(id='total-despesas-por-filial', className='six columns', style={'backgroundColor': 'lightblue', 'margin': '10px', 'padding': '10px'}),
        ],className='row'),
    ])

def layout_meta():
    # Aqui estaria o código que retorna o layout ou componente Dash
    return html.Div([
        dbc.Card([
            html.H2('Progresso em Relação à Meta', style={"textAlign": "center", "fontSize": "18px"}),
            dcc.Graph(id='gauge-chart')  
        ], style={
            "margin": "10px", 
            "padding": "10px", 
            "width": "35%", 
            "maxHeight": "385px",
            "display": "flex",
            "justifyContent": "center",
            "overflow": "hidden"
        }) 
    ])


# ============ FIM LAYOUT SEPARADO ============ #

# ============INICIO LAYOUT============ #
# Layout do aplicativo
app.layout = html.Div(style={ 'fontFamily': 'Arial, sans-serif'}, children=[
    html.Div([
            dcc.Interval(
            id='interval-component',
            interval=2*60*60*1000,  # 2 horas em milissegundos
            n_intervals=0
        )
    ]),

    # Sidebar
    html.Div([  
        html.H1('Filtros', style={'textAlign': 'center', 'marginBottom': '20px'}),
        html.H3('Selecione uma data', style={'textAlign': 'center'}),
        # Filtro de data
        dcc.DatePickerRange(
            id='date-picker-range-app',
            display_format='DD/MM/YYYY',
            start_date=primeiro_dia_mes_corrente,
            end_date=data_atual,
            start_date_placeholder_text="Data de início",
            end_date_placeholder_text="Data de término",
            style={'width': '100%'}
        ),
        # Filtro Representante
        html.H3('Selecione um Representante', style={'textAlign': 'center'}, className='titulo-filtro'),
        dcc.Dropdown(
            id='filtro-representante',
            options=representantes_options,
            multi=True,
            placeholder="Todos Representantes Selecionados",
            style={'width': '100%'}
        ),
        # Filtro Empresa
        html.H3('Selecione uma empresa', style={'textAlign': 'center'},className='titulo-filtro'),
        dcc.Dropdown(
            id='filtro-empresa',
            options=empresa_options,
            multi=True,
            placeholder="Todas as Empresa Selecionadas",
            style={'width': '100%'}
        ),
        # Filtro Tabela de Preço
        html.H3('Selecione uma Tabela de Preço', style={'textAlign': 'center'},className='titulo-filtro'),
        dcc.Dropdown(
            id='filtro-tabela-preco',
            options=tabela_precos_options,
            multi=True,
            placeholder="Todas as Tabelas Selecionadas",
            style={'width': '100%'}
        ),
        html.H3('Selecione uma Configuração de Nota', style={'textAlign': 'center'},className='titulo-filtro'),
        dcc.Dropdown(
            id='filtro-configuracao-pedido',
            options=configuracao_pedidos_options,
            multi=True,
            placeholder="Todas as Configurações Selecionadas",
            style={'width': '100%'}
        )
        # Adicione aqui mais filtros conforme necessário
    ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '10px'}),
    
    # Conteúdo Principal
    html.Div([
        dbc.Tabs([
            dbc.Tab(label="Vendas", tab_id="tab-vendas"),
            dbc.Tab(label="Compras", tab_id="tab-compras"),
            dbc.Tab(label="Estoque", tab_id="tab-estoque"),
            dbc.Tab(label="Clientes", tab_id="tab-clientes"),
            dbc.Tab(label="Contas", tab_id="tab-contas"),
            dbc.Tab(label="Meta", tab_id="tab-meta"),
        ], id="tabs-principal", active_tab="tab-vendas"),
        html.Div(id="conteudo-principal"),
    ],style={'width': '80%', 'float': 'right', 'display': 'inline-block', 'padding': '10px'}),     
])


# ============FIM LAYOUT============ #

# ============INICIO Callback============ #

# Callback para atualizar o resumo da seleção de representantes
@app.callback(
    Output('placeholder-representante', 'children'),
    [Input('filtro-representante', 'value')]
)
def update_placeholder(selected_representantes):
    if not selected_representantes:
        return "Selecione um representante"
    elif len(selected_representantes) == 1:
        rep_label = next((item['label'] for item in representantes_options if item['value'] == selected_representantes[0]), "Selecione um representante")
        return rep_label
    else:
        return "Selecionado mais de um representante"

# Callback para o gráfico de vendas diarias
@app.callback(
    Output('container-grafico-vendas-diarias', 'children'),  # Assume que você tem um dcc.Graph com id='grafico-vendas-diarias' no layout
    
        [
            Input('date-picker-range-app', 'start_date'),
            Input('date-picker-range-app', 'end_date'),
            Input('filtro-representante', 'value'),
            Input('filtro-empresa', 'value'),
            Input('filtro-tabela-preco', 'value'),
            Input('filtro-configuracao-pedido', 'value')
    ]
)
def update_grafico_vendas_diarias(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    figura = vendas_diarias_por_filial.update_chart(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)

# Callback para o gráfico de vendas mensais
@app.callback(
    Output('container-grafico-vendas-mensais', 'children'),  
    [
            Input('date-picker-range-app', 'start_date'),
            Input('date-picker-range-app', 'end_date'),
            Input('filtro-representante', 'value'),
            Input('filtro-empresa', 'value'),
            Input('filtro-tabela-preco', 'value'),
            Input('filtro-configuracao-pedido', 'value')
    ]
)
def update_grafico_vendas_mensais(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    # Calcula o primeiro dia do mês atual e a data atual, ignorando as entradas do date picker
    hoje = datetime.now()
    primeiro_dia_do_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
    data_atual = hoje.strftime('%Y-%m-%d')

    # Usa as datas calculadas para obter os dados do gráfico
    figura = vendas_mensais_por_filial.update_chart(primeiro_dia_do_mes, data_atual, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)


# Callback para o gráfico de vendas anuais
@app.callback(
    Output('container-grafico-vendas-anuais', 'children'),  # Use 'figure' ao invés de 'children' se estiver retornando diretamente um gráfico
    [
            Input('date-picker-range-app', 'start_date'),
            Input('date-picker-range-app', 'end_date'),
            Input('filtro-representante', 'value'),
            Input('filtro-empresa', 'value'),
            Input('filtro-tabela-preco', 'value'),
            Input('filtro-configuracao-pedido', 'value')
    ]
)
def update_grafico_vendas_anuais(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    # Calcula o primeiro dia do ano e a data atual
    hoje = datetime.now()
    primeiro_dia_do_ano = hoje.replace(month=1, day=1).strftime('%Y-%m-%d')
    data_atual = hoje.strftime('%Y-%m-%d')

    # Agora usa as datas calculadas para chamar a função de atualização do gráfico
    figura = vendas_anuais_por_filial.update_chart(primeiro_dia_do_ano, data_atual, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado)
    return figura



# Callback para atualizar o gráfico do Top 5 Clientes que Mais Compraram
@app.callback(
    Output('container-grafico-top-clientes', 'children'),
    [Input('date-picker-range-app', 'start_date'),
     Input('date-picker-range-app', 'end_date'),
     Input('filtro-representante', 'value'),
     Input('filtro-empresa', 'value'),
     Input('filtro-tabela-preco', 'value'),
     Input('filtro-configuracao-pedido', 'value')]
)
def update_top_5_clientes(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    figura = top_5_Clientes_mais_compraram.update_chart(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)


# Callback para atualizar o de Total de Marcas Compradas
@app.callback(
    Output('container-grafico-total-marca-produtos', 'children'),
    [Input('date-picker-range-app', 'start_date'),
     Input('date-picker-range-app', 'end_date'),
     Input('filtro-representante', 'value'),
     Input('filtro-empresa', 'value'),
     Input('filtro-tabela-preco', 'value'),
     Input('filtro-configuracao-pedido', 'value')]
)
def update_total_marcas_mais_compradas(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    figura = total_marca_comprados.update_chart(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)


# Callback para atualizar o de Total de Produtos Comprados Compradas
@app.callback(
    Output('container-grafico-total-produtos-comprados', 'children'),
    [Input('date-picker-range-app', 'start_date'),
     Input('date-picker-range-app', 'end_date'),
     Input('filtro-representante', 'value'),
     Input('filtro-empresa', 'value'),
     Input('filtro-tabela-preco', 'value'),
     Input('filtro-configuracao-pedido', 'value')]
)
def update_total_marcas_mais_compradas(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    figura = total_produtos_comprados.update_chart(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)

# Callback para atualizar a curva abc de produtos.
@app.callback(
    Output('container-grafico-abc-produtos', 'children'),
    [Input('date-picker-range-app', 'start_date'),
     Input('date-picker-range-app', 'end_date'),
     Input('filtro-representante', 'value'),
     Input('filtro-empresa', 'value'),
     Input('filtro-tabela-preco', 'value'),
     Input('filtro-configuracao-pedido', 'value')]
)
def update_curva_abc_produto(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    figura = curva_abc_produtos.update_chart(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado)
    return dcc.Graph(figure=figura, style={'overflowX': 'auto', 'width': '100%'})

# Callback para atualizar a curva abc dos fornecedores.
@app.callback(
    Output('container-grafico-abc-fornecedores', 'children'),
    [Input('date-picker-range-app', 'start_date'),
     Input('date-picker-range-app', 'end_date'),
     Input('filtro-representante', 'value'),
     Input('filtro-empresa', 'value'),
     Input('filtro-tabela-preco', 'value'),
     Input('filtro-configuracao-pedido', 'value')]
)
def update_curva_abc_fornecedor(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado):
    figura = curva_abc_fornecedores.update_chart(start_date, end_date, representantes_selecionados, estab_selecionado, tab_preco_selecionado, cfg_pedido_selecionado)
    return dcc.Graph(figure=figura, style={'overflowX': 'auto', 'width': '100%'})




# Callback para atualizar os pedidos pendentes de baixa
@app.callback(
    Output('container-pedidos-pendentes', 'children'),
    [Input('date-picker-range-app', 'start_date'),
     Input('date-picker-range-app', 'end_date'),
     Input('filtro-representante', 'value'),
     Input('filtro-empresa', 'value'),
     Input('filtro-tabela-preco', 'value'),
     Input('filtro-configuracao-pedido', 'value')]
)
def update_pedidos_pendentes(start_date, end_date, representantes_selecionados, empresa_selecionada, tabela_preco_selecionada,  cfg_pedido_selecionado):
    figura = pedidos_pendente_de_baixa.update_chart(start_date, end_date, conn, representantes_selecionados, empresa_selecionada, tabela_preco_selecionada,cfg_pedido_selecionado)
    return dcc.Graph(id='grafico-pedidos-pendentes', figure=figura)

# Callback para atualizar o gráfico do valor liquido por conceito da pessoa
@app.callback(
        Output('container-valor-liquido-conceito', 'children'),
        [Input('date-picker-range-app', 'start_date'),
        Input('date-picker-range-app', 'end_date'),
        Input('filtro-representante', 'value'),
        Input('filtro-empresa', 'value'),
        Input('filtro-tabela-preco', 'value'),
        Input('filtro-configuracao-pedido', 'value')]
)
def update_valor_liquido_conceito(start_date, end_date,representantes_selecionados, estab_selecionado, tabela_selecionado, cfg_pedido_selecionado):
    figura = valor_liquido_por_conceito_cliente.update_chart(start_date, end_date,representantes_selecionados, estab_selecionado, tabela_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)

# Callback para atualizar o grafico de valor liquido por Vendedor
@app.callback(
     Output('container-valor-liquido-vendedor', 'children'),
        [Input('date-picker-range-app', 'start_date'),
        Input('date-picker-range-app', 'end_date'),
        Input('filtro-representante', 'value'),
        Input('filtro-empresa', 'value'),
        Input('filtro-tabela-preco', 'value'),
        Input('filtro-configuracao-pedido', 'value')]
)
def update_valor_liquido_vendedor(start_date, end_date,representantes_selecionados,estab_selecionado,tabela_selecionado, cfg_pedido_selecionado):
    figura = valor_liquido_por_vendedor.update_chart(start_date, end_date,representantes_selecionados,estab_selecionado,tabela_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)

# Callback para atualizar o grafico de valor liquido por Agrupamento de Produto
@app.callback(
     Output('container-valor-liquido-agrupamento-produtos', 'children'),
        [Input('date-picker-range-app', 'start_date'),
        Input('date-picker-range-app', 'end_date'),
        Input('filtro-representante', 'value'),
        Input('filtro-empresa', 'value'),
        Input('filtro-tabela-preco', 'value'),
        Input('filtro-configuracao-pedido', 'value')]
)
def update_valor_liquido_agrupamento_produto(start_date, end_date,representantes_selecionados,estab_selecionado,tabela_selecionado,cfg_pedido_selecionado):
    figura = valor_liquido_agrupamento_produtos.update_chart(start_date, end_date,representantes_selecionados,estab_selecionado,tabela_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)

# Callback para atualizar o grafico de valor liquido dos Produto
@app.callback(
     Output('container-valor-liquido-por-produto', 'children'),
        [Input('date-picker-range-app', 'start_date'),
        Input('date-picker-range-app', 'end_date'),
        Input('filtro-representante', 'value'),
        Input('filtro-empresa', 'value'),
        Input('filtro-tabela-preco', 'value'),
        Input('filtro-configuracao-pedido', 'value')]
)
def update_valor_liquido_por_produto(start_date, end_date,representantes_selecionados,estab_selecionado,tabela_selecionado, cfg_pedido_selecionado):
    figura = valor_liquido_por_produto.update_chart(start_date, end_date,representantes_selecionados,estab_selecionado,tabela_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)

# Callback para atualizar o total de transações por periodo
@app.callback(
    Output('container-total-transacao-por-periodo', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value'),]
)
def update_total_transacoes(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado):
    total_transacoes = buscar_total_transacoes_periodo(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado)
    return f"Total de Transações no Período: {total_transacoes}"


# Callback para atualizar o total de clientes ativos
@app.callback(
    Output('container-total-clientes-ativos-periodo', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value'),]
)
def update_total_clientes_ativos(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado):
    total_clientes_ativos = indice_lealdade_cliente.clientes_ativos_periodo(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado)
    return f"Total de Cliente Ativos: {total_clientes_ativos}"

# Callback para atualizar o total de vendas por periodo
@app.callback(
    Output('container-valor-total-de-todos-pedidos', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value')]
)
def update_total_vendas_periodo(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado):
    total_vendas = sumarizacao_total_dos_pedidos(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado)
    return f"Sumarização das Vendas no Periodo: {total_vendas}"

# Callback para calcular e atualizar o ticket médio por cliente
@app.callback(
    Output('container-ticket-medio', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value')]
)
def update_ticket_medio(start_date, end_date, selected_reps_ids):
    # Obtenha o total de vendas e garanta que seja um float
    total_vendas_str = sumarizacao_total_dos_pedidos(start_date, end_date, selected_reps_ids)
    total_vendas = float(total_vendas_str.replace('.', '').replace(',', '.'))

    # Obtenha o total de clientes e garanta que seja um float
    total_clientes_str = buscar_total_clientes()
    total_clientes = float(total_clientes_str) if total_clientes_str else 0

    # Faça o cálculo do ticket médio, tratando divisão por zero
    ticket_medio = (total_vendas / total_clientes) if total_clientes > 0 else 0

    # Formate o ticket médio para exibição
    ticket_medio_formatado = locale.format_string('%.2f', ticket_medio, grouping=True)

    return f"Ticket Médio: R$ {ticket_medio_formatado}"


# Callback para atualizar o total de compras por periodo
@app.callback(
    Output('container-valor-total-de-compras', 'children'),
        [Input('date-picker-range-app', 'start_date'),
        Input('date-picker-range-app', 'end_date'),
        Input('filtro-representante', 'value'),
        Input('filtro-empresa', 'value'),
        Input('filtro-tabela-preco', 'value'),
        Input('filtro-configuracao-pedido', 'value')]
)
def update_total_compra(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado):
    total_compras = valor_total_das_compras(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado)
    return f"Total de Compras no Periodo: {total_compras}"



# Callback para atualizar o saving
@app.callback(
    Output('container-valor-total-saving', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value')]
)
def update_total_compra(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado):
    total_compras = valor_total_saving(start_date, end_date, selected_reps_ids, selected_emp, selected_tab_id, cfg_pedido_selecionado)
    return f"Total do Saving no Periodo: {total_compras}"


# Callback para o mapa de vendas
@app.callback(
    Output('container-mapa-vendas', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value')]
)
def update_mapa_venda(start_date, end_date, selected_reps_ids, selected_estab, selected_tabela, selected_config_pedido):
    dataframe = mapa_vendas_cliente.mapa_vendas(start_date, end_date, selected_reps_ids,selected_estab,selected_tabela,selected_config_pedido)
    if dataframe.empty:
        return 'Não há dados para exibir.'  # Lida com o DataFrame vazio

    # Cria a figura com o DataFrame atualizado
    figura = px.scatter_mapbox(dataframe, lat="LATITUDEENDERECO", lon="LONGITUDEENDERECO", hover_name="hover_text",
                               color_discrete_sequence=["fuchsia"], zoom=3, height=300)
    figura.update_layout(mapbox_style="open-street-map")
    figura.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Retorna um novo dcc.Graph com a figura atualizada
    return dcc.Graph(figure=figura)


# Callback para o mapa de vendas
@app.callback(
    Output('container-mapa-compras', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value')]
)
def update_mapa_venda(start_date, end_date, selected_reps_ids, selected_estab, selected_tabela, selected_config_pedido):
    dataframe = mapa_compras_fornecedor.mapa_compras(start_date, end_date, selected_reps_ids,selected_estab,selected_tabela,selected_config_pedido)
    if dataframe.empty:
        return 'Não há dados para exibir.'  # Lida com o DataFrame vazio

    # Cria a figura com o DataFrame atualizado
    figura = px.scatter_mapbox(dataframe, lat="LATITUDEENDERECO", lon="LONGITUDEENDERECO", hover_name="hover_text",
                               color_discrete_sequence=["fuchsia"], zoom=3, height=300)
    figura.update_layout(mapbox_style="open-street-map")
    figura.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Retorna um novo dcc.Graph com a figura atualizada
    return dcc.Graph(figure=figura)


# Callback para atualizar o gráfico que compara as vendas atuais x ano passado
@app.callback(
    Output('container-grafico-comparando-vendas-atuais-x-ano-passado', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date')]
)
def update_chart_comparando_vendas_atuais_x_passado(start_date, end_date):
    fig = comparando_vendas_periodo_atual_x_ano_passado.update_chart(start_date, end_date)
    return fig


# Callback para atualizar o total de Duplicatas Vencidas
@app.callback(
    Output('container-valor-total-duplicatas-vencidas', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date')]
)
def update_total_dup_vencida(start_date, end_date):
    total_compras = valor_total_duplicatas_vencidas(start_date, end_date)
    return f"Total de Duplicatas Vencidas no Periodo (sem contar Juros nem Multas): {total_compras}"

# Callback para atualizar o total de Duplicatas a Pagar Vencidas
@app.callback(
    Output('container-valor-total-duplicatas-a-pagar-vencidas', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value')]
)
def update_total_dup_vencida(start_date, end_date, selected_reps_ids):
    total_compras = valor_total_contas_a_pagar_vencidas(start_date, end_date, selected_reps_ids)
    return f"Total de Duplicatas a Pagar Vencidas no Periodo: {total_compras}"

# Callback para atualizar o gráfico de metas x vendedor
@app.callback(
    Output('gauge-chart', 'figure'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value')]
)
def update_gauge_chart(start_date, end_date, selected_reps_ids, tabela_preco_selecionado, empresa_selecionada,cfg_pedido_selecionado):
    
    # Chama a função total_metas para obter os valores atualizados
    total_metas_val, total_pedidos_val = total_metas(start_date, end_date, selected_reps_ids, tabela_preco_selecionado, empresa_selecionada,cfg_pedido_selecionado)
    
    # Usa os valores obtidos para criar o gráfico de velocímetro
    fig = create_gauge_chart_with_pointer(total_metas_val, total_pedidos_val)
    
    return fig


# Callback para atualizar o gráfico do Total de Devolução por Filial
@app.callback(
    Output('total-devolucao-por-filial', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value')]
)
def update_total_dev_por_filial(start_date, end_date, selected_reps_ids, tabela_preco_selecionado, empresa_selecionada,cfg_pedido_selecionado):
    figura = total_devolucao_por_filial.update_chart(start_date, end_date, selected_reps_ids, tabela_preco_selecionado, empresa_selecionada,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)

# Callback para atualizar o gráfico do Total de Despesas por filial
@app.callback(
    Output('total-despesas-por-filial', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-empresa', 'value'),]
)
def update_total_despesas_por_filial(start_date, end_date, empresa_selecionada):
    figura = total_despesas_por_filial.update_chart(start_date, end_date, empresa_selecionada)
    return dcc.Graph(figure=figura)

# Callback para atualizar o grafico de total de transação pro cpf e cnpj
@app.callback(
    Output('container-valor-total-cpf-cnpj', 'children'),
    [Input('date-picker-range-app', 'start_date'),
    Input('date-picker-range-app', 'end_date'),
    Input('filtro-representante', 'value'),
    Input('filtro-empresa', 'value'),
    Input('filtro-tabela-preco', 'value'),
    Input('filtro-configuracao-pedido', 'value')]
)
def update_total_vendas_cpf_cnpj(start_date, end_date, representantes_selecionados, estab_selecionado,filtro_tab_preco_selecionado,cfg_pedido_selecionado):
    figura = valor_total_transacao_cnpf_cpf.update_chart(start_date, end_date, representantes_selecionados, estab_selecionado,filtro_tab_preco_selecionado,cfg_pedido_selecionado)
    return dcc.Graph(figure=figura)


# Callback pra criar a distribuição de clientes por regiao
@app.callback(
    Output('container-mapa-clientes-regiao', 'children'),
    [Input('interval-component', 'n_intervals')]  # Atualiza baseado em intervalos definidos
)
def update_distribuicao_clientes_regiao(n):
    # Chama a função que busca os dados e retorna um DataFrame
    dataframe = distribuicao_clientes_por_regiao.mapa_regiao()
    # Passa o DataFrame para a função que cria o layout do mapa
    figura = distribuicao_clientes_por_regiao.create_layout(dataframe)
    return figura



# Callback pra criar o crescimento da base de clientes
@app.callback(
    Output('container-crescimento-clientes', 'children'),
    [Input('interval-component', 'n_intervals')]  # Atualiza baseado em intervalos definidos
)
def update_distribuicao_clientes_regiao(n):
    # Chama a função que busca os dados e retorna um DataFrame
    dataframe = crescimento_base_clientes.crescimento_cliente()
    # Passa o DataFrame para a função que cria o layout do gráfico de linha
    figura = crescimento_base_clientes.create_line_chart(dataframe)
    # Retorna o gráfico encapsulado em um componente dcc.Graph com o id especificado
    return dcc.Graph(figure=figura, id='container-crescimento-clientes')


# ================INICIO CRIAÇÃO ABA=============================== #
# Callback pras abas principais
@app.callback(
    Output("conteudo-principal", "children"),
    [Input("tabs-principal", "active_tab")]
)
def renderizar_conteudo_principal(active_tab):
    if active_tab == "tab-vendas":
        return layout_vendas()
    elif active_tab == "tab-compras":
        return layout_compras()
    elif active_tab == "tab-estoque":
        return layout_estoque()
    elif active_tab == "tab-clientes":
        return layout_clientes()
    elif active_tab == "tab-contas":
        return layout_contas()
    elif active_tab == "tab-meta":
        return layout_meta()
# ================FIM CRIAÇÃO ABA=============================== #

# ============FIM Callback============ #

# Inicialização do Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(update_app, 'interval', minutes=60)
scheduler.start()

# ============Run Server============ #
if __name__ == '__main__':
    # ,host='0.0.0.0', port=8050
    app.run_server(debug=True)
