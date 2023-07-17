from abc import ABC, abstractmethod
from ngen.cal.meta import JobMeta
from ngen.cal.configuration import Model
from ngen.cal.utils import pushd
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence, Optional, Mapping, Any
    from pandas import DataFrame
    from pathlib import Path
    from ngen.cal.calibratable import Adjustable

class BaseAgent(ABC):

    @property
    def adjustables(self) -> 'Sequence[Adjustable]':
        return self.model.adjustables

    def restart(self) -> int:
        with pushd(self.job.workdir):
            starts = []
            for adjustable in self.adjustables:
                starts.append(adjustable.restart())
        if all( x == starts[0] for x in starts):
            #if everyone agress on the iteration...
            return starts[0]
        else:
            return 0
    
    @property
    @abstractmethod
    def model(self) -> 'Model':
        pass

    @property
    @abstractmethod
    def job(self) -> 'JobMeta':
        pass
    
    def update_config(self, i: int, params: 'DataFrame', id: str):
        """
            For a given calibration iteration, i, update the input files/configuration to prepare for that iterations
            calibration run.

            parameters
            ---------
            i: int
                current iteration of calibration
            params: pandas.DataFrame
                DataFrame containing the parameter name in `param` and value in `i` columns
        """
        return self.model.update_config(i, params, id, path=self.job.workdir)
    
    @property
    def best_params(self) -> str:
        return self.model.best_params

class Agent(BaseAgent):

    def __init__(self, model_conf, workdir: 'Path', log: bool=False, restart: bool=False, parameters: 'Optional[Mapping[str, Any]]' = {}):
        self._workdir = workdir
        self._job = None
        if restart:
            # find prior ngen workdirs
            # FIXME if a user starts with an independent calibration strategy
            # then restarts with a uniform strategy, this will "work" but probably shouldn't.
            # it works cause the independent writes a param df for the nexus that uniform also uses,
            # so data "exists" and it doesn't know its not conistent...
            # Conversely, if you start with uniform then try independent, it will start back at
            # 0 correctly since not all basin params can be loaded.
            # There are probably some similar issues with explicit and independent, since they have
            # similar data semantics
            workdirs = list(Path.glob(workdir, model_conf['type']+"_*_worker"))
            if( len(workdirs) > 1) :
                print("More than one existing workdir, cannot restart")
            elif( len(workdirs) == 1):
                self._job = JobMeta(model_conf['type'], workdir, workdirs[0], log=log)

        if(self._job is None):
            self._job = JobMeta(model_conf['type'], workdir, log=log)
        model_conf['workdir'] = self.job.workdir
        self._model = Model(model=model_conf)
        self._model.model.resolve_paths()
        self._params = parameters
    
    @property
    def parameters(self) -> 'Mapping[str, Any]':
        return self._params

    @property
    def workdir(self) -> 'Path':
        return self._workdir

    @property
    def job(self) -> JobMeta:
        return self._job
    
    @property
    def model(self) -> Model:
        return self._model.model

    @property
    def cmd(self) -> str:
        """
            Proxy method to build command from contained model binary and args
        """
        return "{} {}".format(self.model.get_binary(), self.model.get_args())

    def duplicate(self) -> 'Agent':
        #serialize a copy of the model
        #FIXME ??? if you do self.model.resolve_paths() here, the duplicated agent
        #doesn't have fully qualified paths...but if you do it in constructor, it works fine...
        data = self.model.__root__.copy(deep=True)
        #return a new agent, which has a unique Model instance
        #and its own Job/workspace
        return Agent(data.dict(by_alias=True), self._workdir)
