import os


if __name__ == '__main__':
    from HeatPumpBase import HeatPumpBase
else:
    from .HeatPumpBase import HeatPumpBase


class SingleWorkingFluidHeatPump(HeatPumpBase):
    """Super class of all concrete heat pump models."""

    def __init__(self, params):
        """Initialize model and set necessary attributes."""
        super().__init__(params)

        self.subdirname = (
            f"{self.params['setup']['type']}_"
            + f"{self.params['setup']['refrig']}"
            )
        self.design_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'stable', f'{self.subdirname}_design'
            ))
        self.validate_dir()

        self.wf = self.params['fluids']['wf']
        self.si = self.params['fluids']['si']
        self.so = self.params['fluids']['so']
