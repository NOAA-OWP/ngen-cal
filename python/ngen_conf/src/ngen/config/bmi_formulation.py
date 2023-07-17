from pydantic import BaseModel, FilePath, DirectoryPath, PyObject, Field, root_validator, validator
from typing import Mapping, Optional, Union, Sequence, Any
from pathlib import Path
from sys import platform

import logging
logger = logging.getLogger('bmi_formulation')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

class BMIParams(BaseModel, smart_union=True, allow_population_by_field_name = True):
    """The base of all BMI paramterized ngen model configurations.

        This class holds the common configuiration requirements for general BMI models
        used in by the ngen model framework.

    The class args here set configuration options of the BaseModel meta class.

    smart_union (bool): 
        Use smart_union capabilities https://pydantic-docs.helpmanual.io/usage/model_config/#smart-union
    
    allow_population_by_field_name (bool): 
        Initialize the allow_population_by_field_name config of the BaseModel meta class.
        Allows objects to be created with keyword args which match the python class attribute
        names or the field name/alias
        https://pydantic-docs.helpmanual.io/usage/model_config/#:~:text=default%3A%20False)-,allow_population_by_field_name,-whether%20an%20aliased
    """

    #required fields
    name: str
    model_name: str = Field(alias='model_type_name')
    main_output_variable: str
    config: Union[Path] = Field(alias='init_config') #Bmi config, can be a file or a str pattern
    
    #reasonable defaultable fields
    allow_exceed_end_time: bool = False
    fixed_time_step: bool = False
    uses_forcing_file: bool = False
    name_map: Mapping[str, str] = Field(None, alias='variables_names_map')

    #strictly optional fields (null/none) by default
    output_vars: Optional[Sequence[str]] = Field(None, alias="output_variables")
    output_headers: Optional[Sequence[str]] = Field(None)
    model_params: Optional[Mapping[str, str]]

    #non exposed fields, derived from fields and used to build up and validate certain components
    #such as configuration path/file
    _config_prefix: Optional[DirectoryPath] = Field(default=None, alias="config_prefix")
    _output_map: Optional[Mapping[str, str]] = Field(None, alias="output_map")

    def resolve_paths(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        if isinstance(self.config, Path):
            #Not sure why this is needed, but I found one case
            #where a forumulation has an empty string config...
            self.config = self.config.resolve()

    @root_validator(pre=True)
    def validate_output_fields(cls, values):
        """Build the output_vars and output_headers from a mapping type if provided.

            Since this is a pre validator, this will apply before any other validation happens
            so the output fields will get further validated once set here.

        Args:
            values (dict): The values being used to initialize the class.

        Returns:
            dict: The values dict with `output_headers` and `output_vars` set from `output_map` if provided.
        """
        output_map = values.get("output_map", {})
        output_headers = values.get("output_headers", [])
        output_vars = values.get("output_vars", [])
        if output_map:
            if output_vars:
                logger.info("BMIParams provided output map and output variables list.  List values will be ignored")
            output_vars = []
            output_headers = []
            for k,v in output_map.items():
                output_vars.append(k)
                if v != '':
                    output_headers.append(v)
                else:
                    output_headers.append(k)
            values['output_vars'] = output_vars
            values['output_headers'] = output_headers
        return values
    
    @validator("name_map", always=True, pre=True)
    def update_name_map(cls, name_map: Mapping[str, str]) -> Mapping[str, str]:
        """Update any default name map, ensuring the provided keys are overridden by the given `name_map`.

            If `name_map` contains keys that exist in the default name map, the default mapping gets
            updated by the values in `name_map`.  If the default keys are not in `name_map` then they
            will exist in the objects `variables_names_map` alongside the mappings in `name_map`

            This validator runs "always", even if the class isn't provided a `name_map` argument.
            It also runs prior to other validation, so the name_map is still subject to validating
            as a Mapping[str, str].

        Args:
            name_map (Mapping[str, str]): The desired name mapping.

        Returns:
            Mapping[str, str]: The default name map updated with key/value pairs in `name_map`
        """
        if hasattr(cls, "_variable_names_map"):
            if name_map:
                #need to copy here or we end up overwriting the class attribute for the
                #life of the interperter...not really the indended semantics...
                names = cls._variable_names_map.copy()
                names.update(name_map)
                return names
            return cls._variable_names_map
        return name_map


    @root_validator(pre=True)
    def build_config_path(cls, values: Mapping[str, Any]):
        """Build a complete path for the init_config file if a prefix is provided.

            Join the `config_prefix` and the `config` fields to make complete path for `config`.
            If no `config_prefix` is provided to the class, then `config` is left unchanged.

        Args:
            values (Mapping[str, Any]): All attributes being assigned to this class

        Returns:
            Mapping[str, Any]: Attributes to assign to the class, with a (possibly) modified `config` attribute
        """
        prefix = values.get('config_prefix')
        if prefix:
            values['config'] = prefix.joinpath(values['config'])
            conf_str = str(values['config'])
            #not the most efficient...but need to know if we need to type cast to a str
            #or look for a filepath
            if "{{" in conf_str and "}}" in conf_str:
                values['config'] = conf_str
        return values

    @classmethod
    def get_system_lib_extension(cls) -> str:
        """Detect and return the dynamic library extension for the current platformm

        Returns:
            str: The dynamic library extension used on the system (.so for `linux`, .dylib for `darwin`)
        """
        if platform == "linux":
            return '.so'
        elif platform == "darwin":
            return '.dylib'

class BMILib(BMIParams):
    """Intermidiate type for BMI parameters requiring library files
    """
    #required
    #try file path first, otherwise use str and find extension
    library: Path = Field(alias="library_file")
    #optional
    _library_prefix: Optional[DirectoryPath] = Field(None, alias="library_prefix")
    
    def resolve_paths(self):
        super().resolve_paths()
        self.library = self.library.resolve()

    @root_validator(pre=True)
    def build_library_path(cls, values: Mapping[str, Any]) -> Mapping[str, Any]:
        """Build a complete path for the library file if a prefix is provided.

            Join the `library_prefix` and the `library` fields to make complete path for `library`.
            If no `library_prefix` is provided to the class, then `library` is left unchanged.

            Additionally, this method will change the library suffix based on the detectable platform.
            On `linux`, the library suffix will be `.so`
            on `darwin`, the library suffix will be `.dylib`

        Args:
            values (Mapping[str, Any]): All attributes being assigned to this class

        Returns:
            Mapping[str, Any]: Attributes to assign to the class, with a (possibly) modified `library` attribute
        """
        lib_path = values.get('library_prefix')
        lib = values.get('library') or values.get('library_file')
        if lib_path:
            lib = lib_path.joinpath(lib)
        values['library'] = Path(lib).with_suffix( cls.get_system_lib_extension() )
        return values

class BMIC(BMILib):
    """Intermediate type for BMI C library configurations
        This class adds a `registration_function` requirement,
        as well as fixes the `name` of the `BMIParams` attribute to a constant, `bmi_c`
        for all subclasses
    """
    registration_function: str
    name = Field("bmi_c", const=True)

class BMIFortran(BMILib):
    """Interrmediate type for BMI Fortran library configurations
        This class fixes the `name` of the `BMIParams` attribute to a constant, `bmi_fortran`
        for all subclasses
    """
    name:str = Field("bmi_fortran", const=True)

class BMIPython(BMIParams):
    """Intermediate type for BMI Python library configurations
        This class adds a `python_type` requirement,
        as well as fixes the `name` of the `BMIParams` attribute to a constant, `bmi_python`
        for all subclasses
    """
    python_type: Union[PyObject, str]
    name: str = Field("bmi_python", const=True)

class BMICxx(BMILib):
    """Intermediate type for BMI C++ library configurations
        This class adds a `registration_function` requirement,
        as well as fixes the `name` of the `BMIParams` attribute to a constant, `bmi_c++`
        for all subclasses
    """
    registration_function: str
    name: str = Field("bmi_c++", const=True)
