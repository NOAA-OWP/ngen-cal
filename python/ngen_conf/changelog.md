# Version 0.1.9
- Fixed field discriminator issue in `ngen.config`'s `Formulation` model `params` field. 
  Note, during `Formulation` object creation if the `params` field is
  deserialized (e.g. `params`'s value is a dictionary), the `name` field is
  required. If `name` *is not* 'bmi_multi', the `model_type_name` field is also
  required. Neither are required if a concrete known formulation instance is
  provided (see #32).

# Version 0.1.8
- Fix bug when building MultiBmi's `model_name` field from passed `Formulation`
  objects (fixes #62).

# Version 0.1.6
- `BMIParams`'s `fixed_time_step` now defaults to `True` (fixes #47).

# Version 0.1.5
- Added optional arguement, `relative_to` to `resolve_paths` allowing a path prefix to be passes before attempting to resolve the absoulte path.

# Version 0.1.2
- Better path/pattern handling
- `resolve_paths` function added to resolve potential relative paths into absolute paths if needed
- Fix unit test path for `test_cfe_sloth`
