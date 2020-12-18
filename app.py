import pandas as pd
import plotly.express as px
import plotly as pl
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
 


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#arquivo csv contendo os vértices do grafo
nodes = pd.read_csv('https://raw.githubusercontent.com/ritallopes/OFPFINAL/main/nodes.csv?token=AJ4IH5ROYO6VM2CSIOV7JAK73RBOC')
#configurando nome de colunas e index
nodes.columns = ['index', 'name', 'position']
nodes.set_index('index', inplace=True)
nodes.position = nodes.position.str.extract(r'\[(.+)\]').iloc[:,0]
edges = pd.read_csv('https://raw.githubusercontent.com/ritallopes/OFPFINAL/main/edges.csv?token=AJ4IH5RJ2VOFUIHXUOTSW3K73RBLQ')
edges.columns  = ['source', 'target', 'lib', 'version']
#adicionando propriedade versão a partir de lib source
edges.iloc[:,3] = edges.iloc[:, 2].str.extract(r'\-(\d+.+)').iloc[:,0]

# pegando packages que são alvo de mais de 200 pacotes
more_target = pd.Series(edges.target.value_counts() > 200)
edges = edges[edges.target.isin(more_target[more_target].index)]
edges['name_source'] = 'NaN'
edges.name_source = [nodes.loc[nodes.index == i,['name']].iloc[0,0] for i in edges.source]
edges['name_target'] = 'NaN'
edges.name_target = [nodes.loc[nodes.index == i,['name']].iloc[0,0] for i in edges.target]
edges = edges[edges.name_source.notna()]  #remove nan of source
edges = edges[edges.name_target.notna()]  #remove nan of source
nodes = nodes[nodes.name.notna()] #removing names with na of nodes

#Construindo grafo
G = nx.DiGraph()
G.add_nodes_from(nodes.name)
nx.set_node_attributes(G, pd.Series(list(nodes.position.str.split(",")), index=nodes.name).to_dict(), 'pos')
G.add_edges_from([(s,t) for s,t in zip(edges.name_source, edges.name_target)]) # adicionando as arestas
G.remove_nodes_from(list(nx.isolates(G)))# removendo nós isolados


app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='ego',
                options=[{'label': i, 'value': i} for i in list(['Todos','requests', 'Pyinstaller', 'labkit'])],
                value='Todos'
            )
        ],
        style={'display': 'none'}),
   
    html.Div([
           dcc.Graph(id='indicator-graphic'),
        ],
        style={'width': '100%', 'height': '100%','display': 'inline-block', 'float':'right',  'margin':'0'}),
    ])  
], style={'width': '100%', 'height': '100%'})

@app.callback(
    Output('indicator-graphic', 'figure'),
    [Input('ego', 'value')])
def update_graph(ego):
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='Electric',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Pacotes conectados',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
            
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(str(len(adjacencies[1]))+' conexões')

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text
    node_trace.marker.size = node_adjacencies
    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='<br>Grafo de dependência Python',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        text="Grafo de rede de dependência de pacotes Python",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )

    return fig
if __name__ == '__main__':
    app.run_server(debug=True)