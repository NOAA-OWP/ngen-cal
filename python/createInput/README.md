## CreateInput

<font size="4"> CreateInput is a Python package to generate the data and files needed for performing the model parameter calibration and validation in the NextGen modeling framework. </font>

## Files in this Subpackage 
- <font size="4">___configs_ Directory__ 
    - <font size="4">_input.config_: This input configuration file contains all kinds of options related to the selected basin, working directory, formulation, optimization algorithm, objective function, iteration number, simulation time period, hydrofabric and forcing data, executable and libraries, etc. </font>
- <font size="4">___src_ Directory__
    - <font size="4">_ginputfunc.py_: Contains various functions to create crosswalk file, generates or process BMI initial configuration files, as well as create t-route configuration file, model realization configuration file, and calibration configuration file. </font>
  - <font size="4">_create_input.py_: Main script to read configuration file _input.config_ and call functions in _ginputfunc.py_ to generate the required input data and files. </font>
    
 
