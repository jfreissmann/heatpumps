
import pytest

from heatpumps.models import (HeatPumpCascade, HeatPumpCascade2IHX,
                              HeatPumpCascade2IHXTrans, HeatPumpCascadeEcon,
                              HeatPumpCascadeEconIHX,
                              HeatPumpCascadeEconIHXTrans,
                              HeatPumpCascadeEconTrans, HeatPumpCascadeFlash,
                              HeatPumpCascadeFlashTrans, HeatPumpCascadeIC,
                              HeatPumpCascadeICTrans, HeatPumpCascadeIHXEcon,
                              HeatPumpCascadeIHXEconTrans,
                              HeatPumpCascadeIHXPC, HeatPumpCascadeIHXPCIHX,
                              HeatPumpCascadeIHXPCIHXTrans,
                              HeatPumpCascadeIHXPCTrans, HeatPumpCascadePC,
                              HeatPumpCascadePCIHX, HeatPumpCascadePCIHXTrans,
                              HeatPumpCascadePCTrans, HeatPumpCascadeTrans,
                              HeatPumpEcon, HeatPumpEconIHX,
                              HeatPumpEconIHXTrans, HeatPumpEconTrans,
                              HeatPumpFlash, HeatPumpFlashTrans, HeatPumpIC,
                              HeatPumpICTrans, HeatPumpIHX, HeatPumpIHXEcon,
                              HeatPumpIHXEconTrans, HeatPumpIHXPC,
                              HeatPumpIHXPCIHX, HeatPumpIHXPCIHXTrans,
                              HeatPumpIHXPCTrans, HeatPumpIHXTrans, HeatPumpPC,
                              HeatPumpPCIHX, HeatPumpPCIHXTrans,
                              HeatPumpPCTrans, HeatPumpSimple,
                              HeatPumpSimpleTrans)
from heatpumps.parameters import get_params


class TestHeatPumpCascade:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascade')
        return HeatPumpCascade(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascade2IHX:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascade2IHX')
        return HeatPumpCascade2IHX(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascade2IHXTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascade2IHXTrans')
        return HeatPumpCascade2IHXTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEcon', econ_type='closed')
        return HeatPumpCascadeEcon(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEcon', econ_type='open')
        return HeatPumpCascadeEcon(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconIHXClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEconIHX', econ_type='closed')
        return HeatPumpCascadeEconIHX(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconIHXOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEconIHX', econ_type='open')
        return HeatPumpCascadeEconIHX(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconIHXTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEconIHXTrans', econ_type='closed')
        return HeatPumpCascadeEconIHXTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconIHXTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEconIHXTrans', econ_type='open')
        return HeatPumpCascadeEconIHXTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEconTrans', econ_type='closed')
        return HeatPumpCascadeEconTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeEconTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeEconTrans', econ_type='open')
        return HeatPumpCascadeEconTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeFlash:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeFlash')
        return HeatPumpCascadeFlash(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeFlashTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeFlashTrans')
        return HeatPumpCascadeFlashTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIC:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIC')
        return HeatPumpCascadeIC(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeICTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeICTrans')
        return HeatPumpCascadeICTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXEconClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXEcon', econ_type='closed')
        return HeatPumpCascadeIHXEcon(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXEconOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXEcon', econ_type='open')
        return HeatPumpCascadeIHXEcon(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXEconTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXEconTrans', econ_type='closed')
        return HeatPumpCascadeIHXEconTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXEconTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXEconTrans', econ_type='open')
        return HeatPumpCascadeIHXEconTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPC', econ_type='closed')
        return HeatPumpCascadeIHXPC(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPC', econ_type='open')
        return HeatPumpCascadeIHXPC(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCIHXClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPCIHX', econ_type='closed')
        return HeatPumpCascadeIHXPCIHX(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCIHXOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPCIHX', econ_type='open')
        return HeatPumpCascadeIHXPCIHX(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCIHXTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPCIHXTrans', econ_type='closed')
        return HeatPumpCascadeIHXPCIHXTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCIHXTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPCIHXTrans', econ_type='open')
        return HeatPumpCascadeIHXPCIHXTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPCTrans', econ_type='closed')
        return HeatPumpCascadeIHXPCTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeIHXPCTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeIHXPCTrans', econ_type='open')
        return HeatPumpCascadeIHXPCTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePC', econ_type='closed')
        return HeatPumpCascadePC(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePC', econ_type='open')
        return HeatPumpCascadePC(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCIHXClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePCIHX', econ_type='closed')
        return HeatPumpCascadePCIHX(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCIHXOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePCIHX', econ_type='open')
        return HeatPumpCascadePCIHX(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCIHXTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePCIHXTrans', econ_type='closed')
        return HeatPumpCascadePCIHXTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCIHXTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePCIHXTrans', econ_type='open')
        return HeatPumpCascadePCIHXTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePCTrans', econ_type='closed')
        return HeatPumpCascadePCTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadePCTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadePCTrans', econ_type='open')
        return HeatPumpCascadePCTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpCascadeTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpCascadeTrans')
        return HeatPumpCascadeTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEcon', econ_type='closed')
        return HeatPumpEcon(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEcon', econ_type='open')
        return HeatPumpEcon(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconIHXClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEconIHX', econ_type='closed')
        return HeatPumpEconIHX(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconIHXOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEconIHX', econ_type='open')
        return HeatPumpEconIHX(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconIHXTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEconIHXTrans', econ_type='closed')
        return HeatPumpEconIHXTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconIHXTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEconIHXTrans', econ_type='open')
        return HeatPumpEconIHXTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEconTrans', econ_type='closed')
        return HeatPumpEconTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpEconTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpEconTrans', econ_type='open')
        return HeatPumpEconTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpFlash:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpFlash')
        return HeatPumpFlash(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpFlashTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpFlashTrans')
        return HeatPumpFlashTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIC:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIC')
        return HeatPumpIC(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpICTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpICTrans')
        return HeatPumpICTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHX:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHX')
        return HeatPumpIHX(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXEconClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXEcon', econ_type='closed')
        return HeatPumpIHXEcon(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXEconOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXEcon', econ_type='open')
        return HeatPumpIHXEcon(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXEconTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXEconTrans', econ_type='closed')
        return HeatPumpIHXEconTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXEconTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXEconTrans', econ_type='open')
        return HeatPumpIHXEconTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPC', econ_type='closed')
        return HeatPumpIHXPC(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPC', econ_type='open')
        return HeatPumpIHXPC(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCIHXClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPCIHX', econ_type='closed')
        return HeatPumpIHXPCIHX(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCIHXOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPCIHX', econ_type='open')
        return HeatPumpIHXPCIHX(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCIHXTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPCIHXTrans', econ_type='closed')
        return HeatPumpIHXPCIHXTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCIHXTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPCIHXTrans', econ_type='open')
        return HeatPumpIHXPCIHXTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPCTrans', econ_type='closed')
        return HeatPumpIHXPCTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXPCTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXPCTrans', econ_type='open')
        return HeatPumpIHXPCTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpIHXTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpIHXTrans')
        return HeatPumpIHXTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPC', econ_type='closed')
        return HeatPumpPC(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPC', econ_type='open')
        return HeatPumpPC(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCIHXClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPCIHX', econ_type='closed')
        return HeatPumpPCIHX(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCIHXOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPCIHX', econ_type='open')
        return HeatPumpPCIHX(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCIHXTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPCIHXTrans', econ_type='closed')
        return HeatPumpPCIHXTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCIHXTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPCIHXTrans', econ_type='open')
        return HeatPumpPCIHXTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCTransClosed:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPCTrans', econ_type='closed')
        return HeatPumpPCTrans(params=self.params, econ_type='closed')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpPCTransOpen:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpPCTrans', econ_type='open')
        return HeatPumpPCTrans(params=self.params, econ_type='open')

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpSimple:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpSimple')
        return HeatPumpSimple(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()


class TestHeatPumpSimpleTrans:

    @pytest.fixture
    def hp_model(self):
        self.params = get_params('HeatPumpSimpleTrans')
        return HeatPumpSimpleTrans(params=self.params)

    def test_run_model(self, hp_model):
        hp_model.run_model()

