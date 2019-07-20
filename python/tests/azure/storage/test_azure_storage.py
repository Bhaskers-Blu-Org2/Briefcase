import pyworkspace
import keyring
import os
import pytest

@pytest.fixture
def test_subdir():
    # change to tests/ subdir so we can resolve the yaml
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

def test_service_prinicpal(test_subdir):
    ws = pyworkspace.Workspace()

    svc1 = ws['myvault1']
    assert len(svc1.get_secret("workspacetest1")) > 0

def test_service_csv1(test_subdir):
    ws = pyworkspace.Workspace()

    df = ws['csv1'].to_pandas_dataframe()
    assert (df.columns == ['a', 'b', 'c']).all()
    assert df.shape == (2, 3)