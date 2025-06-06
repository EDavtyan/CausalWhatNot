import numpy as np
import networkx as nx
from utils.helpers import causallearn_to_dag, edge_differences


def test_causallearn_to_dag_simple():
    amat = np.array([[0, 1], [-1, 0]])
    dag, meta = causallearn_to_dag(amat, ['X', 'Y'])
    assert list(dag.edges()) == [('X', 'Y')]
    assert meta['undirected_edges'] == set()


def test_causallearn_to_dag_undirected():
    amat = np.array([[0, 1], [1, 0]])
    dag, meta = causallearn_to_dag(amat, ['A', 'B'])
    assert list(dag.edges()) == [('A', 'B')]
    assert meta['undirected_edges'] == {('A', 'B')}


def test_edge_differences():
    true = nx.DiGraph([('A', 'B'), ('B', 'C')])
    pred = nx.DiGraph([('A', 'B'), ('C', 'B'), ('A', 'C')])
    extra, missing, rev = edge_differences(pred, true)
    assert extra == {('A', 'C')}
    assert missing == set()
    assert rev == {('C', 'B')}

