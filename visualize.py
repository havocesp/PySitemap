import networkx
import matplotlib.pyplot as plot
from networkx.readwrite import json_graph
from networkx.readwrite import gexf
import ujson


def visualize(dict_graph, save_path=None):
    # Build networkx Directional Graph
    graph = networkx.DiGraph()
    for source, nodes in dict_graph.items():
        for node in nodes:
            graph.add_edge(source, node)

    # Save graph
    # Convert the graph to json ready format using networkx.readwrite.json_graph
    # Serialize the result using ujson
    # Also save a gexf file for opening it in Gephi or similar tools
    if save_path:
        if not save_path.endswith('/'):
            save_path += '/'
        with open(save_path + 'graph.json', 'w') as file:
            file.write(ujson.dumps(json_graph.node_link_data(graph)))
        gexf.write_gexf(graph, save_path + 'graph.gexf')

    # Plot
    plot.subplot(111)
    plot.figure(num=None, figsize=(512, 256), dpi=256)
    plot.axis('off')

    fig = plot.figure(1)
    pos = networkx.spring_layout(graph)
    networkx.draw_networkx_nodes(graph, pos)
    networkx.draw_networkx_edges(graph, pos)
    networkx.draw_networkx_labels(graph, pos)

    cut = 1.00
    x_max = cut * max(xx for xx, yy in pos.values())
    y_max = cut * max(yy for xx, yy in pos.values())
    plot.xlim(0, x_max)
    plot.ylim(0, y_max)

    # networkx.draw(graph, with_labels=True, font_weight='bold')

    # Save plotted image
    if save_path:
        plot.savefig(save_path + 'graph.png', format="png")  # it can be saved in .pdf .svg .png or .ps formats

    # Show plot
    plot.show()

    # Close
    plot.close()
    del fig


def save_graph(graph, save_path):
    if not save_path or not graph:
        return None
    if not save_path.endswith('/'):
        save_path += '/'
    with open(save_path + 'graph.json', 'w') as file:
        file.write(ujson.dumps(json_graph.node_link_data(graph)))


def load_graph(load_path):
    if not load_path:
        return None
    if not load_path.endswith('/'):
        load_path += '/'
    with open(load_path + 'graph.json') as file:
        json = ujson.load(file)
    return json_graph.node_link_graph(json)
