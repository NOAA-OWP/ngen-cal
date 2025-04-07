# V 0.3.X
- `ngen.cal` subpackage for `optmizers`
- `ngen.cal.optmizers` Grey Wolf Optimizer added

# V 0.2.1
- `ngen.cal` `Objective` enum now properly subclasses `str`. This fixes
  pydantic models' json schemas that use `Objective` as a field type. See #31
  for impacts.
- `ngen.cal` calibration strategy types: `NgenExplicit`, `NgenIndependent`, and
  `NgenUniform`, now have default `strategy` field values.

# V 0.2.0
- Allow ngen configuration to specify routing output file name to look for.
- `Evaluatable` objects are now responsible for maintaining the `evaluation_parms` property, including `evaluation_range`
- `evaluation_range` removed from `Meta`
- `eval_params` bundeled and moved to model config from global, these include the following configuration keys
    - `evaluation_start`
    - `evaluation_stop`
    - `objective`
- Add `bounds` property to `Adjustable` interface
- Use an `Agent` abstraction to connect model runtime, calibration objects, and evaluation criteria
- All model execution now happens in automatically generated subdirectory
- Introduce PSO global best serach, only applicable for `uniform` stragegy
- Allow additional search algorithm parameters to be configured by the user
    - For DDS, the configuration can supply the `neighborhood` parameter as follows, if not supplied, a default of 0.2 is used
    ```yaml
        strategy:
        type: estimation
        algorithm: dds
        parameters:
            neighborhood: 0.5
    ```
    - For PSO, the configuration can supply the following parameters
    ```yaml
        strategy:
        type: estimation
        algorithm: "pso"
        parameters:
            pool: 4 #number of processors to use (by default, uses 1)
            particles: 8 #number of particles to use (by default, uses 4)
            options: #the PSO parameters (defaults to c1: 0.5, c2: 0.3, w:0.9)
                c1: 0.1
                c2: 0.1
                w: 0.42
    ```
- Restart semantics have changed slightly.  Restart is only supported for DDS search, with the following caveats:
    If a user starts with an independent calibration strategy
    then restarts with a uniform strategy, this will "work" but probably shouldn't.
    it works cause the independent writes a param df for the nexus that uniform also uses,
    so data "exists" and it doesn't know its not conistent...
    Conversely, if you start with uniform then try independent, it will start back at
    0 correctly since not all basin params can be loaded.
    There are probably some similar issues with explicit and independent, since they have
    similar data semantics.
- Fix issue with independent strategy not writing ngen forcing configs for target catchments in a way that ngen can handle.
