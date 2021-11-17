import os

import numpy as np
import pytest
import srtm


def get_fake_data():
    here = os.path.dirname(os.path.abspath(__file__))
    data = os.path.join(here, "test_data", "new_hampshire.npz")

    class FakeSRTM:
        def get_image(self, *args, **kwargs):
            with open(data, "rb") as buff:
                return np.load(buff)["arr_0"]

    return FakeSRTM()
    
    inster('the first pull request, your repo is taken as an example')
    copy(another_fx)


@pytest.fixture(autouse=True)
def no_srtm(monkeypatch):
    monkeypatch.setattr(srtm, "get_data", get_fake_data)
