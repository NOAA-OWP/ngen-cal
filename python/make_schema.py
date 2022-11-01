from ngen.cal.configuration import General
from ngen.cal.ngen import Ngen

with open("General.schema.json", 'w') as fp:
    fp.write(General.schema_json(indent=2))

with open("Ngen.schema.json", 'w') as fp:
    fp.write(Ngen.schema_json(indent=2))
