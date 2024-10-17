from typing import Union

from .cfe import CFE
from .pet import PET
from .lstm import LSTM
from .noahowp import NoahOWP
from .multi import MultiBMI
from .topmod import Topmod
from .sloth import SLOTH
from .sft import SFT
from .smp import SMP
from .lasam import LASAM


#NOTE the order of this union is important for validation
#unless the model class is using smart_union!
KnownFormulations = Union[Topmod, CFE, PET, NoahOWP, LSTM, SLOTH, MultiBMI, SFT, SMP, LASAM]

#See notes in multi.py and formulation.py about the recursive
#type of MultiBMI modules and how the forward_refs are handled.
