import networkx
import matplotlib.pyplot as plot


subplot = 1


def visualize(dict_graph, save_path=None):
    graph = networkx.DiGraph()
    for source, nodes in dict_graph:
        for node in nodes:
            graph.add_edge(source, node)
    global subplot
    plot.subplot(subplot)
    subplot += 1
    networkx.draw(graph, with_labels=True, font_weight='bold')
    plot.show()
    if save_path:
        plot.savefig(save_path + '/graph.png')
