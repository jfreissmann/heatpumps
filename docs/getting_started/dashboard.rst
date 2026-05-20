~~~~~~~~~
Dashboard
~~~~~~~~~

The dashboard is the easiest way to explore heatpumps vast collection of heat
pump models and you can try it out right now in your browser!

.. image:: https://static.streamlit.io/badges/streamlit_badge_black_white.svg
   :target: https://heatpumps.streamlit.app/
   :alt: Streamlit App

If you want to have more control over your experience with heatpumps or if you
plan to use its part load simulation features or the model classes directly,
you can install it locally as described in the
:ref:`previous section on installation <installation_label>`. If you have
completed the steps described there and your virtual environment is activated,
you can use the following command to start the heatpumps dashboard in a new
browser tab:

.. code-block:: console

    heatpumps-dashboard

This is a convenience short-cut that wraps the full streamlit command, that
looks like this when executed from the root package directory:

.. code-block:: console

    streamlit run src\heatpumps\hp_dashboard.py

Either command should succeed in starting up the dashboard in your browser.
There you'll find yourself on the landing page and you can switch to a design
simulation by clicking on the main button or using the dropdown navigation in
the sidebar to the left. In contrast to the online version mentioned above, the
local installation allows you to start a part-load simulation routine, if you
click the respective button below your design simulation results. Again, you
can also use the navigation in the sidebar to achieve the same. After the
switch you'll see different parametrization options in the sidebar. You can set
the minimun and maximum part-load as well as wether you want to variate the
heat source and sink temperatures and within which range if so. When those are
set up as you wish, you can start the off-design simulation run, which can take
quite some time depending on how large your variation ranges are.
