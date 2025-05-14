import os

from CoolProp.CoolProp import PropsSI as PSI

if __name__ == '__main__':
    from HeatPumpBase import HeatPumpBase
else:
    from .HeatPumpBase import HeatPumpBase

class HeatPumpCascadeBase(HeatPumpBase):
    """Super class of all concrete two stage heat pump models."""

    def _init_fluids(self):
        """Initialize fluid attributes."""
        self.wf1 = self.params['fluids']['wf1']
        self.wf2 = self.params['fluids']['wf2']
        self.si = self.params['fluids']['si']
        self.so = self.params['fluids']['so']

    def _init_dir_paths(self):
        """Initialize paths and directories."""
        self.subdirname = (
            f"{self.params['setup']['type']}_"
            + f"{self.params['setup']['refrig1'].replace('::', '_')}_"
            + f"{self.params['setup']['refrig2'].replace('::', '_')}"
            )
        self.design_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'stable', f'{self.subdirname}_design'
            ))
        self.validate_dir()

    def generate_state_diagram(self, refrig='', diagram_type='logph',
                               style='light', figsize=(16, 10), fontsize=10,
                               legend=True, legend_loc='upper left',
                               return_diagram=False, savefig=True,
                               open_file=True, **kwargs):
        """
        Generate log(p)-h-diagram of heat pump process.

        Parameters
        ----------

        refrig : str
            Name of refrigerant to use for plot. Can be left as an empty string
            in single cycle heat pumps.

        diagram_type : str
            Fluid property diagram type. Either 'logph' or 'Ts'. Default is
            'logph'.

        style : str
            Diagram style to chose. Either 'light' or 'dark'. Default is
            'light'.

        figsize : tuple/list of numbers
            Size of matplotlib figure in inches. Default is (16, 10), so the
            figure is 16 inches wide and 10 inches tall.

        fontsize : int/float
            Size of main fonts in points. Title is 20% larger and tick labels
            as well as state annotations are 10% smaller. Default is 10pts.

        legend : bool
            Flag to set if legend should be shown. Default is `True`.

        legend_loc : str
            Location to place legend to. Accepts options as matplotlib allows.
            Default is 'upper left'. Is only used if 'legend' parameter is set
            to `True`.

        return_diagram : bool
            Flag to set if diagram object should be returned by method. Default
            is False.

        savefig : bool
            Flag to set if diagram should be saved to disk. Default is `False`.

        filepath : str
            Path to save the file to. If `None` and `savefig` is `True`, a
            default name is given and saved to the current working directory.
            Default is `None`.

        open_file : bool
            Flag to set if saved file should be opend by the os. Default is
            `False`.

        **kwargs
            Additional keyword arguments to pass through to the
            `get_plotting_states` method of the heat pump class.
        """
        kwargs1 = {}
        kwargs2 = {}
        if 'xlims' in kwargs:
            kwargs1['xlims'] = kwargs['xlims'][0]
            kwargs2['xlims'] = kwargs['xlims'][1]
        if 'ylims' in kwargs:
            kwargs1['ylims'] = kwargs['ylims'][0]
            kwargs2['ylims'] = kwargs['ylims'][1]
        if return_diagram:
            diagram1 = super().generate_state_diagram(
                refrig=self.params['setup']['refrig1'],
                style=style, figsize=figsize, fontsize=fontsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=1, **kwargs1
            )
            diagram2 = super().generate_state_diagram(
                refrig=self.params['setup']['refrig2'],
                style=style, figsize=figsize, fontsize=fontsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=2, **kwargs2
            )
            return diagram1, diagram2
        else:
            super().generate_state_diagram(
                refrig=self.params['setup']['refrig1'],
                style=style, figsize=figsize, fontsize=fontsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=1, **kwargs1
            )
            super().generate_state_diagram(
                refrig=self.params['setup']['refrig2'],
                style=style, figsize=figsize, fontsize=fontsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=2, **kwargs2
            )

    def check_mid_temperature(self, wf):
        """Check if the intermediate pressure is below the critical pressure."""
        T_crit = PSI('T_critical', wf) - 273.15
        if self.T_mid > T_crit:
            raise ValueError(
                f'Intermediate temperature of {self.T_mid:1f} °C must be below '
                + f'the critical temperature of {wf} of {T_crit:.1f} °C.'
            )
