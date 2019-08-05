import networkx
# import matplotlib.pyplot as plot
from networkx.readwrite import json_graph
from networkx.readwrite import gexf
import ujson
import os
import sys


# def visualize(dict_graph, save_path=None):
#     graph = convert_graph(dict_graph)
# 
#     # Plotting with matplotlib.pyplot just doesn't work. It generates a too small image
#     # TODO: Need to find another way
# 
#     # # Plot
#     # plot.subplot(111)
#     # plot.figure(num=None, figsize=(512, 256), dpi=256)
#     # plot.axis('off')
#     #
#     # fig = plot.figure(1)
#     # pos = networkx.spring_layout(graph)
#     # networkx.draw_networkx_nodes(graph, pos)
#     # networkx.draw_networkx_edges(graph, pos)
#     # networkx.draw_networkx_labels(graph, pos)
#     #
#     # cut = 1.00
#     # x_max = cut * max(xx for xx, yy in pos.values())
#     # y_max = cut * max(yy for xx, yy in pos.values())
#     # plot.xlim(0, x_max)
#     # plot.ylim(0, y_max)
#     #
#     # # networkx.draw(graph, with_labels=True, font_weight='bold')
#     #
#     # # Save plotted image
#     # if save_path:
#     #     plot.savefig(save_path + 'graph.png', format="png")  # it can be saved in .pdf .svg .png or .ps formats
#     #
#     # # Show plot
#     # plot.show()
#     #
#     # # Close
#     # plot.close()
#     # del fig


_module_root_dir = None


def _get_module_root_dir():
    global _module_root_dir
    if not _module_root_dir:
        _module_root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    return _module_root_dir


def convert_graph(dict_graph):
    # Build networkx Directional Graph
    graph = networkx.DiGraph()
    for source, nodes in dict_graph.items():
        for node in nodes:
            graph.add_edge(source, node)
    return graph


# Save graph
# Convert the graph to json ready format using networkx.readwrite.json_graph
# Serialize the result using ujson
def save_graph(graph, save_path=_get_module_root_dir(), no_verbose=False):
    if not save_path or not graph:
        if not no_verbose:
            print('Failed to save graph:\nsave_path =', save_path, '\ngraph =', graph)
        return
    if not save_path.endswith('/'):
        save_path += '/'
    with open(save_path + 'graph.json', 'w') as file:
        try:
            file.write(ujson.dumps(json_graph.node_link_data(graph)))
        except IOError as e:
            if not no_verbose:
                print('Failed to save graph: ', e.reason)


def load_graph(load_path=_get_module_root_dir(), no_verbose=False):
    if not load_path:
        if not no_verbose:
            print('Failed to save graph:\nsave_path =', load_path)
        return None
    if not load_path.endswith('/'):
        load_path += '/'
    with open(load_path + 'graph.json') as file:
        try:
            json = ujson.load(file)
            return json_graph.node_link_graph(json)
        except IOError as e:
            if not no_verbose:
                print('Failed to save graph: ', e.reason)
    return None


# Save a gexf file for opening it in Gephi or similar tools
def export_graph(graph, save_path=_get_module_root_dir(), no_verbose=False):
    if not save_path or not graph:
        if not no_verbose:
            print('Failed to save graph:\nsave_path =', save_path, '\ngraph =', graph)
        return
    if not save_path.endswith('/'):
        save_path += '/'
    try:
        gexf.write_gexf(graph, save_path + 'graph.gexf')
    except IOError as e:
        if not no_verbose:
            print('Failed to save graph: ', e.reason)
