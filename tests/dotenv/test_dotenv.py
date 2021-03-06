import mlbriefcase
import pytest
import os

@pytest.fixture
def test_subdir():
    # change to tests/ subdir so we can resolve the yaml
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

def test_dotenv(test_subdir):
    ws = mlbriefcase.Briefcase()

    # resolve from .env file
    assert ws['dummy1'].get_secret() == 'secret1'
    assert ws['dummy2'].get_secret() == 'secret2'

    # also support arbitrary properties
    assert ws['dummy1'].url == 'http://my.host'