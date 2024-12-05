��    k      t  �   �       	    !	  �  =
  X  ;  �  �  �   �  �   l  �  a  �  6  �   �  *  �     �$     �$     %     %  g   /%     �%  
   �%     �%  	   �%     �%     �%     �%     �%     &     &     #&     7&     O&     g&     �&     �&     �&     �&     �&     '     '     8'     J'     ^'     p'     �'  	   �'  '   �'  )   �'  )   �'     (     1(      B(     c(  0   }(     �(  	   �(  %   �(  <   �(     ;)     D)     Q)  &   ])  %   �)     �)     �)     �)     �)     *     '*     3*     9*     O*     b*     |*     �*     �*     �*     �*     �*     �*     �*     �*  /   �*  B   *+  ?   m+  E   �+     �+  @   	,     J,     S,     j,     �,     �,     �,     �,     �,     �,     �,     �,  
   �,     
-  	   -     $-     --     ;-     G-     U-     a-     n-     �-    �-    �.    �/  \  �1  )  )3  �   S9  �   >:  7  );  �  a>  �   �E  �  �F     �L     �L     �L     �L  �   M     �M  
   �M     �M     �M  	   �M     �M     �M     N  	   2N     <N     SN     iN     �N     �N     �N     �N     �N     O     0O     LO     ZO     rO     �O     �O     �O     �O     �O  )   �O  &   	P  +   0P     \P     xP  #   �P     �P  :   �P      Q      Q  "   )Q  E   LQ     �Q  
   �Q     �Q  "   �Q  $   �Q  !   �Q     R     8R     VR      kR     �R     �R     �R     �R     �R     �R     �R     S     S     %S     6S     QS     ZS  
   gS  9   rS  F   �S  ?   �S  J   3T     ~T  @   �T  	   �T     �T     �T     U     U     +U  
   ?U     JU     VU  !   _U     �U  
   �U     �U  	   �U     �U     �U     �U     �U     �U     �U     V     !V        X          $                   B      i   \       ^      O          G   #      S      g   7   ?   e   E      M   )       W                         &           @   9       :   5       +   J   h   '   %   !   a   I       F      [   >   Z   _   Y   U   <   	                             k   N      T       1       =                          4   ;          L   ,   V   "      .   /              D       R   c   C          f   3                         -   (   b   `   A   j   8             H   2   
   d               P   ]       0   *      K           Q       6    
                                All substance data and classifications from
                                [CoolProp](http://www.coolprop.org) or
                                [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                                 
                            Definitions and methodology of the exergy analysis based on
                            [Morosuk and Tsatsaronis (2019)](https://doi.org/10.1016/j.energy.2018.10.090),
                            its implementation in TESPy described in [Witte and Hofmann et al. (2022)](https://doi.org/10.3390/en15114087)
                            and pedagogically prepared in [Witte, Freißmann and Fritz (2023)](https://fwitte.github.io/TESPy_teaching_exergy/).
                             
                            Methodology for cost calculation analogous to
                            [Kosmadakis et al. (2020)](https://doi.org/10.1016/j.enconman.2020.113488),
                            based on [Bejan et al. (1995)](https://www.wiley.com/en-us/Thermal+Design+and+Optimization-p-9780471584674).
                             
                    #### Instructions

                    You are now on the design simulation interface
                    for your heat pump. In the left sidebar, next to the
                    dimensioning and the choice of refrigerant, several central parameters
                    for the cycle process must be specified.

                    These include, for example, the temperatures of the heat source and sink,
                    but also the associated network pressures. Additionally, an internal
                    heat exchanger can be optionally added. The resulting superheat of the
                    evaporated refrigerant must also be specified.

                    Once the design simulation is successfully completed, the
                    generated results are processed graphically in state diagrams
                    and quantified. Key metrics such as the coefficient of performance (COP),
                    as well as relevant heat flows and power outputs, will be shown.
                    Furthermore, thermodynamic state variables at each process step will
                    be listed in a table.

                    After the design simulation, a button will appear allowing you to switch
                    to the partial load interface. This can also be done via the
                    dropdown menu in the sidebar. Information on how to perform
                    partial load simulations is available on the start page of this interface.
                     
                    All substance data and classifications from
                    [CoolProp](http://www.coolprop.org) or
                    [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                     
                    Parameterization of the partial load calculation:
                    + Percentage share of partial load
                    + Range of source temperature
                    + Range of sink temperature
                     
                #### Simulation Results:

                Numerical simulations are calculations performed using appropriate
                iterative methods based on the specified boundary conditions and parameters.
                In some cases, it is not possible to account for all possible influences,
                so deviations from real-world experience may occur and should be taken into
                account when evaluating the results. The results provide sufficient to exact
                insights into the heat pump's general behavior, COP, and state variables in
                each component. Nevertheless, all information and results are provided
                without guarantee.
                 
                #### Used Software:

                The open-source software TESPy is used for modeling and simulating the systems.
                Additionally, a number of other Python packages are used for data processing,
                preparation, and visualization.

                ---

                #### TESPy:

                TESPy (Thermal Engineering Systems in Python) is a powerful
                simulation tool for thermal process engineering, such as power plants,
                district heating systems, or heat pumps. The TESPy package allows for
                system design and steady-state operation simulation. After that,
                part load behavior can be determined based on the characteristics of
                each component of the system. The component-based structure combined
                with the solution method offers great flexibility regarding the
                system topology and parameterization. More information on TESPy can
                be found in its [online documentation](https://tespy.readthedocs.io) (in English).

                #### Other Packages:

                - [Streamlit](https://docs.streamlit.io) (Graphical User Interface)
                - [NumPy](https://numpy.org) (Data Processing)
                - [pandas](https://pandas.pydata.org) (Data Processing)
                - [SciPy](https://scipy.org/) (Interpolation)
                - [scikit-learn](https://scikit-learn.org) (Regression)
                - [Matplotlib](https://matplotlib.org) (Data Visualization)
                - [FluProDia](https://fluprodia.readthedocs.io) (Data Visualization)
                - [CoolProp](http://www.coolprop.org) (Fluid Properties)
                 
                To perform a partial load simulation, a heat pump must first be
                designed. Please switch to the "Design" mode first.
                 
            The heat pump simulator *heatpumps* is a powerful simulation software
            for analyzing and evaluating heat pumps.

            This dashboard allows you to control a variety of complex
            thermodynamic plant models using numerical methods via a
            simple interface, without requiring expert knowledge.
            This includes both the design of heat pumps
            as well as the simulation of their steady-state part load operation. The
            simulation results provide insights into the pump's behavior, COP,
            state variables, and costs of individual components as well as
            total investment costs. This enables access to complex questions
            that frequently arise in the design and planning of heat pumps.

            ### Key Features

            - Steady-state design and part load simulation based on [TESPy](https://github.com/oemof/tespy)
            - Parameterization and result visualization via a [Streamlit](https://github.com/streamlit/streamlit) dashboard
            - Common circuit topologies used in industry, research, and development
            - Subcritical and transcritical processes
            - Large selection of working fluids thanks to [CoolProp](https://github.com/CoolProp/CoolProp) integration
             #### High-Temperature Circuit #### Low-Temperature Circuit *heatpumps* Ambient Conditions (Exergy) An error occurred during the heat pump simulation. Please correct the input parameters and try again.

 Base Topology Compressor Constant Copyright Design Design New Heat Pump Design Results Design of the Heat Pump Diagrams Economic Assessment Efficiency $\eta_s$ Efficiency $\eta_{s,1}$ Efficiency $\eta_{s,2}$ Efficiency $\eta_{s,HTK,1}$ Efficiency $\eta_{s,HTK,2}$ Efficiency $\eta_{s,HTK}$ Efficiency $\eta_{s,NTK,1}$ Efficiency $\eta_{s,NTK,2}$ Efficiency $\eta_{s,NTK}$ End Temperature Exergy Analysis Partial Load Exergy Assessment Forward Temperature Grassmann Diagram Heat Pump Dashboard Heat Pump Model Heat Sink Heat Transfer Coefficient (Evaporation) Heat Transfer Coefficient (Miscellaneous) Heat Transfer Coefficient (Transcritical) Internal Heat Exchange Log(p)-h Diagram No. {i}: Superheating/Subcooling Operating Characteristics Parameter 'scale' must be either 'lin' or 'log'. Parameters for Cost Calculation Part Load Part Load Simulation of the Heat Pump Partial load simulation is running... This may take a while. Partload Process Type Refrigerant Refrigerant (High Temperature Circuit) Refrigerant (Low Temperature Circuit) Results are being visualized... Results by Component Results of the Exergy Analysis Return Temperature Running simulation... Select Mode Setup Simulate Partial Load Source Temperature Specific Investment Costs Start Start Design Start Temperature State Diagrams State Quantities Superheating/Subcooling T in °C T-s Diagram Temperature The heat pump design simulation was successful. The return temperature must be lower than the forward temperature. The simulation of the heat pump characteristics was successful. The temperature of the heat sink must be higher than the heat source. Thermal Nominal Power To calculate the partial load, click on "Simulate Partial Load". Topology Topology & Refrigerant Total Investment Costs Transcritical Transcritical Pressure Used Software Value in MW Value in bar Variable Visualizing results... Waterfall Diagram h in kJ/kg is not allowed. m in kg/s p in bar s in kJ/(kgK) subcritical transcritical v in m³/kg vol in m³/s 🧮 Execute Design 🧮 Simulate Part Load Project-Id-Version: PACKAGE VERSION
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: LANGUAGE <LL@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Generated-By: pygettext.py 1.5
 
                                Alle Stoffdaten und Klassifikationen aus
                                [CoolProp](http://www.coolprop.org) oder
                                [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                                 
                            Definitionen und Methodik der Exergieanalyse basierend auf
                            [Morosuk und Tsatsaronis (2019)](https://doi.org/10.1016/j.energy.2018.10.090),
                            dessen Implementation in TESPy beschrieben in [Witte und Hofmann et al. (2022)](https://doi.org/10.3390/en15114087)
                            und didaktisch aufbereitet in [Witte, Freißmann und Fritz (2023)](https://fwitte.github.io/TESPy_teaching_exergy/).
                             
                            Methodik zur Berechnung der Kosten analog zu
                            [Kosmadakis et al. (2020)](https://doi.org/10.1016/j.enconman.2020.113488),
                            basierend auf [Bejan et al. (1995)](https://www.wiley.com/en-us/Thermal+Design+and+Optimization-p-9780471584674).
                             
                #### Anleitung

                Sie befinden sich auf der Oberfläche zur Auslegungssimulation
                Ihrer Wärmepumpe. Dazu sind links in der Sidebar neben der
                Dimensionierung und der Wahl des zu verwendenden Kältemittels
                verschiedene zentrale Parameter des Kreisprozesse vorzugeben.

                Dies sind zum Beispiel die Temperaturen der Wärmequelle und -senke,
                aber auch die dazugehörigen Netzdrücke. Darüber hinaus kann
                optional ein interner Wärmeübertrager hinzugefügt werden. Dazu ist
                weiterhin die resultierende Überhitzung des verdampften
                Kältemittels vorzugeben.

                Ist die Auslegungssimulation erfolgreich abgeschlossen, werden die
                generierten Ergebnisse graphisch in Zustandsdiagrammen
                aufgearbeitet und quantifiziert. Die zentralen Größen wie die
                Leistungszahl (COP) sowie die relevanten Wärmeströme und Leistung
                werden aufgeführt. Darüber hinaus werden die thermodynamischen
                Zustandsgrößen in allen Prozessschritten tabellarisch aufgelistet.

                Im Anschluss an die Auslegungsimulation erscheint ein Knopf zum
                Wechseln in die Teillastoberfläche. Dies kann ebenfalls über das
                Dropdownmenü in der Sidebar erfolgen. Informationen zur
                Durchführung der Teillastsimulationen befindet sich auf der
                Startseite dieser Oberfläche.
                     
                    Alle Stoffdaten und Klassifikationen aus
                    [CoolProp](http://www.coolprop.org) oder
                    [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                     
                    Parametrisierung der Teillastberechnung:
                    + Prozentualer Anteil Teillast
                    + Bereich der Quelltemperatur
                    + Bereich der Senkentemperatur
                     
                #### Simulationsergebnisse:

                Numerische Simulationen sind Berechnungen mittels geeigneter
                Iterationsverfahren in Bezug auf die vorgegebenen und gesetzten
                Randbedingungen und Parameter. Eine Berücksichtigung aller
                möglichen Einflüsse ist in Einzelfällen nicht möglich, so dass
                Abweichungen zu Erfahrungswerten aus Praxisanwendungen
                entstehen können und bei der Bewertung berücksichtigt werden
                müssen. Die Ergebnisse geben hinreichenden bis genauen
                Aufschluss über das prinzipielle Verhalten, den COP und
                Zustandsgrößen in den einzelnen Komponenten der Wärmepumpe.
                Dennoch sind alle Angaben und Ergebnisse ohne Gewähr.
                 
                #### Verwendete Software:

                Zur Modellerstellung und Berechnung der Simulationen wird die
                Open Source Software TESPy verwendet. Des Weiteren werden
                eine Reihe weiterer Pythonpakete zur Datenverarbeitung,
                -aufbereitung und -visualisierung genutzt.

                ---

                #### TESPy:

                TESPy (Thermal Engineering Systems in Python) ist ein
                leistungsfähiges Simulationswerkzeug für thermische
                Verfahrenstechnik, zum Beispiel für Kraftwerke,
                Fernwärmesysteme oder Wärmepumpen. Mit dem TESPy-Paket ist es
                möglich, Anlagen auszulegen und den stationären Betrieb zu
                simulieren. Danach kann das Teillastverhalten anhand der
                zugrundeliegenden Charakteristiken für jede Komponente der
                Anlage ermittelt werden. Die komponentenbasierte Struktur in
                Kombination mit der Lösungsmethode bieten eine sehr hohe
                Flexibilität hinsichtlich der Anlagentopologie und der
                Parametrisierung. Weitere Informationen zu TESPy sind in dessen
                [Onlinedokumentation](https://tespy.readthedocs.io) in
                englischer Sprache zu finden.

                #### Weitere Pakete:

                - [Streamlit](https://docs.streamlit.io) (Graphische Oberfläche)
                - [NumPy](https://numpy.org) (Datenverarbeitung)
                - [pandas](https://pandas.pydata.org) (Datenverarbeitung)
                - [SciPy](https://scipy.org/) (Interpolation)
                - [scikit-learn](https://scikit-learn.org) (Regression)
                - [Matplotlib](https://matplotlib.org) (Datenvisualisierung)
                - [FluProDia](https://fluprodia.readthedocs.io) (Datenvisualisierung)
                - [CoolProp](http://www.coolprop.org) (Stoffdaten)
                 
                Um eine Teillastsimulation durchzuführen, muss zunächst eine
                Wärmepumpe ausgelegt werden. Wechseln Sie bitte zunächst in den
                Modus "Auslegung".
                 
            Der Wärmepumpensimulator *heatpumps* ist eine leistungsfähige Simulationssoftware
            zur Analyse und Bewertung von Wärmepumpen.

            Mit diesem Dashboard lassen sich eine Vielzahl komplexer
            thermodynamischer Anlagenmodelle mithilfe numerischer Methoden über eine
            einfache Oberfläche steuern, ohne Fachkenntnisse über diese
            vorauszusetzen. Dies beinhaltet sowohl die Auslegung von Wärmepumpen,
            als auch die Simulation ihres stationären Teillastbetriebs. Dabei geben
            die Ergebnisse der Simulationen Aufschluss über das prinzipielle
            Verhalten, den COP, Zustandsgrößen und Kosten der einzelnen Komponenten
            sowie Gesamtinvestitionskosten der betrachteten Wärmepumpe. Damit
            wird Zugang zu komplexen Fragestellungen ermöglicht, die regelmäßig in
            der Konzeption und Planung von Wärmepumpen aufkommen.

            ### Key Features

            - Stationäre Auslegungs- und Teillastsimulation basierend auf [TESPy](https://github.com/oemof/tespy)
            - Parametrisierung and Ergebnisvisualisierung mithilfe eines [Streamlit](https://github.com/streamlit/streamlit) Dashboards
            - In der Industrie, Forschung und Entwicklung gängige Schaltungstopologien
            - Sub- und transkritische Prozesse
            - Große Auswahl an Arbeitsmedien aufgrund der Integration von [CoolProp](https://github.com/CoolProp/CoolProp)
                 #### Hochtemperaturkreis #### Niedertemperaturkreis *Wärmepumpe* Umgebungsbedingungen (Exergie) Bei der Simulation der Wärmepumpe ist der nachfolgende Fehler aufgetreten. Bitte korrigieren Sie die Eingangsparameter und versuchen es erneut.


 Grundtopologie Verdichter Konstant Urheberrecht Auslegung Neue Wärmepumpe auslegen Ergebnisse der Auslegung Auslegung der Wärmepumpe Diagramme Ökonomische Bewertung Wirkungsgrad $\eta_s$ Wirkungsgrad $\eta_{s,1}$ Wirkungsgrad $\eta_{s,2} Wirkungsgrad $\eta_{s,HTK,1}$ Wirkungsgrad $\eta_{s,HTK,2}$ Wirkungsgrad $\eta_{s,HTK}$ Wirkungsgrad $\eta_{s,NTK,1}$ Wirkungsgrad $\eta_{s,NTK,2}$ Wirkungsgrad $\eta_{s,NTK}$ Endtemperatur Exergieanalyse Teillast Exergiebewertung Temperatur Vorlauf Grassmann Diagramm Wärmepumpen Dashboard Wärmepumpenmodell Wärmesenke Wärmedurchgangskoeffizient (Verdampfung) Wärmedurchgangskoeffizient (Sonstige) Wärmedurchgangskoeffizient (Transkritisch) Interne Wärmerübertragung Log(p)-h Diagramm Nr. {i}: Überhitzung/Unterkühlung Betriebscharakteristik Der Parameter 'scale' muss entweder 'lin' oder 'log' sein. Parameter zur Kostenkalkulation Teillast Teillastsimulation der Wärmepumpe Teillastsimulation wird durchgeführt... Dies kann eine Weile dauern. Teillast Prozessart Kältemittel Kältemittel (Hochtemperaturkreis) Kältemittel (Niedertemperaturkreis) Ergebnisse werden visualisiert... Ergebnisse nach Komponente Ergebnisse der Exergieanalyse Temperatur Rücklauf Simulation wird durchgeführt... Auslegung der Wärmepumpe Setup Teillast simulieren Quellentemperatur Spez. Investitionskosten Start Auslegung starten Starttemperatur Zustandsdiagramme Zustandsgrößen Überhitzung/Unterkühlung T in °C T-s Diagramm Temperatur Die Simulation der Wärmepumpenauslegung war erfolgreich. Die Rücklauftemperatur muss niedriger sein, als die Vorlauftemperatur Die Simulation der Wärmepumpencharakteristika war erfolgreich. Die Temperatur der Wärmesenke muss höher sein, als die der Wärmequelle. Wärmequelle Um die Teillast zu berechnen, drücke auf "Teillast simulieren". Topologie Topologie & Kältemittel Gesamtinvestitionskosten Transkritisch Traskritischer Druck Verwendete Software Wert in MW Wert in bar Variabel Ergebnisse werden visualisiert... Wasserfall Diagramm h in kJ/kg ist nicht erlaubt. m in kg/s p in bar s in kJ/(kgK) subkritisch transkritisch v in m³/kg vol in m³/s 🧮 Auslegung ausführen 🧮 Teillast simulieren 