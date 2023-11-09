# ngen :: config
This subpackage provides a library and cli utility for generating and validating ngen realization configuration files.

## ngen run validator
The [run_validator](./run_validator.py) is a tool to ensure the target folder or tarball is valid based on the standard ngen run folder as outlined [here](https://github.com/CIROH-UA/ngen-datastream/tree/main). To run this tool, issue the following command:

```
python run_validator.py <path to folder or tarball>

```

What this tool does:
1) Enforce that only of of each of these files exist: \
./config/catchments.geojson \
./config/nexus.geojson \
./config/realization.json
2) Enforce the ngen_conf pydantic models for each file above
3) Validate that the forcings file pattern and path provided in the realization match the forcings file names provided.
4) Validate that each catchment specified in the catchments.geojson file has a corresponding forcings file
