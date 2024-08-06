from __future__ import annotations

from typing import Union

from ngen.config.cfe import CFE
from ngen.config.lgar import LGAR
from ngen.config.lstm import LSTM
from ngen.config.multi import MultiBMI
from ngen.config.noahowp import NoahOWP
from ngen.config.pet import PET
from ngen.config.sloth import SLOTH
from ngen.config.soil_freeze_thaw import SoilFreezeThaw
from ngen.config.soil_moisture_profile import SoilMoistureProfile
from ngen.config.topmod import Topmod

#NOTE the order of this union is important for validation
#unless the model class is using smart_union!
KnownFormulations = Union[Topmod, CFE, PET, NoahOWP, LSTM, SLOTH, LGAR, SoilFreezeThaw, SoilMoistureProfile, MultiBMI]

#See notes in multi.py and formulation.py about the recursive
#type of MultiBMI modules and how the forward_refs are handled.
