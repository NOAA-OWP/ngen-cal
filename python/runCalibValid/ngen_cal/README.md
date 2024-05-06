## ngen.cal package

<font size="4"> This standalone tool carries out parameter calibration for different NextGen model formulations. It expands and extends the functionalities of an earlier version of [ngen.cal](https://github.com/NOAA-OWP/ngen-cal/tree/master/python/ngen_cal) with the additional features as follows: </font>

- <font size="4"> Adds a statistical module with sixteen metrics for assessing hydrologic model performance </font>
- <font size="4"> Adds a visualization module to generate plots for different calibration and validation outputs, such as hydrograph, flow duration curve, figures of statistical metrics, and calibration parameters (calibration run), etc. </font>
- <font size="4"> Implements grey wolf optimizer (GWO) and associted interfaces for potential implementional of the other swarm optmization algorithms </font>
- <font size="4"> Improves restart capability to clean up the calibration output files and resume the crashed calibration run. Restart functionality is currently implemented for DDS and GWO. </font>
- <font size="4"> Installs capabilites to support the exection of validation runs using the default and best parameter sets, respectively </font>


