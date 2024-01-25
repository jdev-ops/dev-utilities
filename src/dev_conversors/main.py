import pydot
from jinja2 import Environment, DictLoader
import sys

d2_template = """
direction: right
{% for key, value in nodes %}
{{ key }}: {{ value }}
{{ key }}.shape: oval
{% endfor %}
{% for key, value in edges %}
{{ key }} -> {{ value }}
{% endfor %}
"""


def dot_to_d2():
    env = Environment(loader=DictLoader({"d2": d2_template}))
    graphs = pydot.graph_from_dot_data(sys.stdin.read())
    graph = graphs[0]
    nodes = []
    for node in graph.get_nodes():
        if node.get_name().strip() not in ["graph", '"\\n"']:
            nodes.append((node.get_name()[1:-1], node.get_label()[1:-1]))
    edges = []
    for i in graph.get_edges():
        edges.append((i.get_source()[1:-1], i.get_destination()[1:-1]))
    template = env.get_template("d2")
    print(template.render(nodes=nodes, edges=edges))
