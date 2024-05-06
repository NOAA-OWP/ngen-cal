## CreateInput

<font size="4"> CreateInput is a Python package to generate all the necessary data and files needed for performing the model parameter calibration and validation in the NextGen modeling framework. </font>

## Files in this Subpackage 
- <font size="4">___Examples_ Directory__
  - <font size="4">_create_input.py_: Main script to read master configuration file _input.config_ and call functions in _ginputfunc.py_ to generate the required input data and files. </font>
  - <font size="4">_config/input.config_: This input configuration file contains all kinds of options related to the basin, calibration settings, hydrofabric file, forcing data, and formulation libraries, etc. </font>
- <font size="4">___src_ Directory__
  - <font size="4">_ginputfunc.py_: Contians various funcitons to create crosswalk file, generate or process BMI initial configuration files, as well as create t-route configuration file, main realization file, and calibration configuration file. </font>
  - <font size="4">_noaa_owp.py_: Contains function to generate BMI initial configuraiton for Noah-OWP-Modular model. </font>
