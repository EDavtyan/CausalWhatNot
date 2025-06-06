import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import networkx as nx
import pytest

from utils.loaders import load_dataset
from algorithms import pc, ges, cosmo
try:
    from algorithms import notears
except ImportError:  # causalnex not installed
    notears = None

ALGOS = [pc, ges, cosmo]
if notears is not None:
    ALGOS.append(notears)


@pytest.mark.parametrize('algo_module', ALGOS)
def test_algorithms_asia(algo_module):
    data, true_graph = load_dataset('asia', n_samples=200, force=True)
    if algo_module is notears and sys.version_info >= (3, 11):
        with pytest.raises(ImportError):
            algo_module.run(data)
        return
    pred_graph, _ = algo_module.run(data)
    assert set(pred_graph.nodes()) == set(true_graph.nodes())
    assert nx.is_directed_acyclic_graph(pred_graph)


def test_notears_small():
    if notears is None:
        pytest.skip('causalnex not installed')
    df = pd.DataFrame(np.random.randn(200, 5), columns=[f'x{i}' for i in range(5)])
    if sys.version_info >= (3, 11):
        with pytest.raises(ImportError):
            notears.run(df)
        return
    g, _ = notears.run(df)
    assert set(g.nodes()) == set(df.columns)
    assert nx.is_directed_acyclic_graph(g)


def test_notears_torch_seed_deterministic():
    if notears is None:
        pytest.skip('causalnex not installed')
    df = pd.DataFrame(np.random.randn(100, 4), columns=list('ABCD'))
    if sys.version_info >= (3, 11):
        with pytest.raises(ImportError):
            notears.run(df, torch_seed=1)
        return
    g1, info1 = notears.run(df, torch_seed=1)
    g2, info2 = notears.run(df, torch_seed=1)
    arr1 = nx.to_numpy_array(g1, nodelist=df.columns)
    arr2 = nx.to_numpy_array(g2, nodelist=df.columns)
    assert np.array_equal(arr1, arr2)
    assert np.allclose(info1['weights'], info2['weights'])


def test_cosmo_small():
    df = pd.DataFrame(np.random.randn(100, 3), columns=list('ABC'))
    g, _ = cosmo.run(df, seed=0)
    assert set(g.nodes()) == set(df.columns)
    assert nx.is_directed_acyclic_graph(g)


def test_discrete_default_params(monkeypatch):
    df, _ = load_dataset('asia', n_samples=50, force=True)

    recorded = {}

    def dummy_pc(data, alpha=0.05, indep_test=None, stable=True):
        recorded['pc'] = indep_test

        class CG:
            pass

        CG.G = type('G', (), {'graph': np.zeros((data.shape[1], data.shape[1]))})()
        return CG()

    monkeypatch.setattr(pc, 'pc', dummy_pc)
    pc.run(df)
    assert recorded['pc'] == 'chisq'

    pc.run(df, indep_test='fisherz')
    assert recorded['pc'] == 'fisherz'

    def dummy_ges(data, score_func=None):
        recorded['ges'] = score_func

        Gobj = type('G', (), {'graph': np.zeros((data.shape[1], data.shape[1]))})()
        return {'G': Gobj}

    monkeypatch.setattr(ges, 'ges', dummy_ges)
    ges.run(df)
    assert recorded['ges'] == 'local_score_BDeu'

    ges.run(df, score_func='bic')
    assert recorded['ges'] == 'local_score_BIC'


def test_alarm_discrete_metadata(monkeypatch):
    df, _ = load_dataset('alarm', n_samples=50, force=True)

    def dummy_pc(data, alpha=0.05, indep_test=None, stable=True):
        class CG:
            pass

        CG.G = type('G', (), {'graph': np.zeros((data.shape[1], data.shape[1]))})()
        return CG()

    monkeypatch.setattr(pc, 'pc', dummy_pc)
    _, meta_pc = pc.run(df)
    assert meta_pc['indep_test'] == 'chisq'

    def dummy_ges(data, score_func=None):
        Gobj = type('G', (), {'graph': np.zeros((data.shape[1], data.shape[1]))})()
        return {'G': Gobj}

    monkeypatch.setattr(ges, 'ges', dummy_ges)
    _, meta_ges = ges.run(df)
    assert meta_ges['score_func'] == 'bdeu'

