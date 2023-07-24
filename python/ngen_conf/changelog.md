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
