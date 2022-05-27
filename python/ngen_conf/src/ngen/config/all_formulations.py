from typing import Union

from ngen.config.cfe import CFE
from ngen.config.lstm import LSTM
from ngen.config.noahowp import NoahOWP
from ngen.config.multi import MultiBMI
from ngen.config.topmod import Topmod

#NOTE the order of this union is important for validation
#unless the model class is using smart_union!
KnownFormulations = Union[Topmod, CFE, NoahOWP, LSTM, MultiBMI]

#See notes in multi.py and formulation.py about the recursive
#type of MultiBMI modules and how the forward_refs are handled.
