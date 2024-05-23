## NextGen_Model_Calibration
>>>>>>> d0a6192 (Add readme and changlog info from development work)

## __Context__
<font size="4"> This branch currently contains the scripts and files from NextGen_Model_Calibration package and [ngen-cal](https://github.com/NOAA-OWP/ngen-cal/) repo. Detailed information on [ngen-cal]((https://github.com/NOAA-OWP/ngen-cal/) can be found on the master branch. This page focuses on the introduction for NextGen_Model_Calibration. </font> 

## __NextGen_Model_Calibration__
<font size="4"> NextGen_Model_Calibration is a model-agnostic Python software supporting automatic calibration of a variety of Next Generation Water Modeling Framework (NextGen) formulations. </font> 

### Main Features
- <font size="4"> Creates a plethora of input data and configuration files. </font>
- <font size="4"> Calibrates parameters for different NextGen model and model components such as Conceptual Functional Equivalent (CFE), TOPMODEL, Noah-OWP-Modular, Lumped Arid/Semi-arid Model (LASAM), soil freeze-thaw model (SFT) and soil moisture profile (SMP). </font>
- <font size="4"> Implements three parameter optimization algorithms, including dynamically dimensioned search (DDS), particle swarm optimization (PSO) and grey wolf optimizer (GWO). </font>
- <font size="4"> Supports three calibration strategies, including uniform, independent and explicit. </font>
- <font size="4"> Provides statistical evaluation tool to calculate a number of metrics to measure model performance.
- <font size="4"> Installs interface to choose objective function from the statistical tool, such as KGE, NSE, MAE, RMSE, RSR, correlation coefficient, etc. </font>
- <font size="4"> Provides visualization tool to plot different output files from calibration and validation runs.</font>

### Subpackages
- <font size="4">__createInput__ (Source code in _python/createInput_): This subpackage generates the required input data and configuration files for the specified formulation and basin. </font>
- <font size="4">__ngen.cal__ (Source code in _python/runCalibValid/ngen_cal_): This subpackge executes simulation through model engine, evaluates streamflow performance and optimizes model parameters. It also performs validation runs using the default and the calibrated best parameter set, respectively. </font>
- <font size="4">__ngen.config__ (Source code in _python/runCalibValid/ngen_conf_): This subpackage parses and validates realization configurations of a wide range of NextGen model and model components. </font>

### Installation
<font size="4"> Create and activate the Python virtual environment </font>

``` bash
python3 -m venv venv-cal 
source venv-cal/bin/activate
```
<font size="4"> Grab source code from the [PR branch](https://github.com/NOAA-OWP/ngen-cal/tree/4cb1c44280e56fd0ac640f0d4e6b5cc57fb3dbd8)</font>
``` bash
git clone https://github.com/NOAA-OWP/ngen-cal.git
cd ngen-cal
git fetch origin pull/123/head:123
git checkout 123
```
<font size="4"> Install each subpackage into the virtual environment </font>
```bash
cd python/createInput
pip install .
cd python/runCalibValid/ngen_cal
pip install .
cd python/runCalibValid/ngen_conf
pip install .
```
### Documentation
<font size="4"> This calibration tool provides an easily operated interface to perform model parameter optimization. The detailed instructions on installation, configuration and execution of calibration workflow are described in the [User's Guide](https://github.com/NOAA-OWP/ngen-cal/blob/b5b056e4af0e7d5952b19d574d03f8638e31a0c7/doc/NextGen_Model_Calibration_User_Guide.pdf). This document also describes preparation of data and files, as well as explains the scripts used in each subpackage. </font>
    
### Examples
<font size="4"> A [shell script](https://github.com/NOAA-OWP/ngen-cal/blob/8541009f70a23e7f50ac6e0ea712c00704a410dc/examples/run_calibration.sh) in examples directory demonstrates the process to generate input file for the specified basin, and execute calibration and validation job runs using the functionalities in this tool. </font>
    
