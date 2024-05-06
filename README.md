## NextGen_Model_Calibration
>>>>>>> d0a6192 (Add readme and changlog info from development work)

<font size="4"> NextGen_Model_Calibration is a model-agnostic Python software supporting automatic calibration of a variety of NextGen formulations. </font>

## Main Features
- <font size="4"> Calibrates parameters for different NextGen model and model components such as Conceptual Functional Equivalent (CFE), TOPMODEL, Noah-OWP-Modular, Lumped Arid/Semi-arid Model (LASAM), soil freeze-thaw model (SFT) and soil moisture profile (SMP). </font>
- <font size="4"> Implements three parameter optimization algorithms, including dynamically dimensioned search (DDS), particle swarm optimization (PSO) and grey wolf optimizer (GWO). </font>
- <font size="4"> Provides interface to choose different objective functions such as KGE, NSE, RMSE, etc. </font>
- <font size="4"> Installs statistical and visualization tools to monitor and explore calibration and validation simulation performance. </font>

## Overview of packages
- <font size="4">__createInput__: This subpackage generates the required input data and configuration files to perform calibation. </font>
- <font size="4">__ngen.cal__: This subpackge calibrates NextGen formulations parameters using the specified calibration settings through BMI. It also implements functionalities to perform validation runs using the default and best parameter set, respectively. </font>
- <font size="4">__ngen.config__: This subpackage parses and validates realization configurations of versatile NextGen model and model components. </font>
        
## Usage
<font size="4"> This calibration tool provides an easily operated interface to perform model parameter estimation. [User's Guide](https://github.com/NOAA-OWP/NextGen_Model_Calibration/tree/master/doc) in _doc_ folder describes 
the instructions on installation, configuration and execution of calibration workflow in detail. This documentation also describes all the subpackages and scripts plus the required libraries and data. A shell script in _examples_ folder demonstrates the procedure to generate input for the specified basin and NextGen formulation, and execute calibration and validation runs using the functionalities in this tool. <font size="4"> 
    
