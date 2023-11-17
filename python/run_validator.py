import json, os, argparse
from ngen.config.realization import NgenRealization
from ngen.config.hydrofabric import CatchmentGeoJSON , NexusGeoJSON 
from ngen.config.validate import validate_paths
import re

def validate(catchment_file,nexus_file,realization_file=None):

    print(f'Validating {catchment_file}')
    serialized_catchments = CatchmentGeoJSON.parse_file(catchment_file)

    catchments = []
    for jfeat in serialized_catchments.features:
        id   = jfeat.id
        if id is None: id = jfeat.properties.id # discrepancy between geopandas and pydantic
        catchments.append(id)

    print(f'Done\nValidating {nexus_file}')
    serialized_nexus = NexusGeoJSON.parse_file(nexus_file) 
    relative_dir     = os.path.dirname(os.path.dirname(realization_file))

    print(f'Done\nValidating {realization_file}')
    serialized_realization = NgenRealization.parse_file(realization_file)
    serialized_realization.resolve_paths(relative_to=relative_dir)
    val = validate_paths(serialized_realization)
    if len(val) > 0:
        raise Exception(f'{val[0].value} does not exist!')
            
    print(f'Done\nValidating individual catchment forcing paths')
    foring_dir    = os.path.join(relative_dir,serialized_realization.global_config.forcing.path)
    forcing_files = [x for _,_,x in os.walk(foring_dir)][0]
    for jcatch in catchments:
        found_match = False
        jid         = re.findall(r'\d+', jcatch)[0]
        pattern     = serialized_realization.global_config.forcing.file_pattern
        jcatch_pattern = pattern.replace('{{id}}',jid)
        compiled       = re.compile(jcatch_pattern)                
        for jfile in forcing_files:
            if jfile.find('.tar.gz') >= 0: 
                forcing_files.remove(jfile)
                continue
            kid = re.findall(r'\d+', jfile)[0]
            if kid == jid:
                found_match = True
                assert bool(compiled.match(jfile)), f"Forcing file {jfile} does not match pattern specified {pattern}"
                forcing_files.remove(jfile)
        if not found_match :
            raise Exception(f'No matching forcing id found for catchment {jcatch}')
        
    if len(forcing_files) > 0:
        print(f'These forcing files exist, but no corresponding catchment has been defined.\n{forcing_files}')
    else:
        print('Done')

    print(f'\nNGen run folder is valid\n')

def validate_data_dir(data_dir):

    forcing_files    = []
    catchment_file   = None
    nexus_file       = None
    realization_file = None
    for path, _, files in os.walk(data_dir):
        for jfile in files:
            jfile_path = os.path.join(path,jfile)
            if jfile_path.find('config') >= 0:
                if jfile_path.find('catchments') >= 0:
                    if catchment_file is None:                         
                        catchment_file = jfile_path
                    else: 
                        raise Exception('This run directory contains more than a single catchment file, remove all but one.')
                if jfile_path.find('nexus') >= 0: 
                    if nexus_file is None: 
                        nexus_file = jfile_path
                    else: 
                        raise Exception('This run directory contains more than a single nexus file, remove all but one.')
                if jfile_path.find('realization') >= 0: 
                    if realization_file is None: 
                        realization_file = jfile_path
                    else: 
                        raise Exception('This run directory contains more than a single realization file, remove all but one.')
            if jfile_path.find('forcing') >= 0 and jfile_path.find('forcing_metadata') < 0: 
                forcing_files.append(jfile_path) 

    file_list = [catchment_file,nexus_file,realization_file]
    if any([x is None for x in file_list]):
        raise Exception(f'Missing configuration file!')
    
    validate(catchment_file,nexus_file,realization_file)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir",
        dest="data_dir", 
        type=str,
        help="Path to the ngen input data folder", 
        required=False
    )
    parser.add_argument(
        "--tarball",
        dest="tarball", 
        type=str, 
        help="Path to tarball to be validated as ngen input data folder", 
        required=False
    )
    args = parser.parse_args()

    if args.data_dir:
        data_dir = args.data_dir
        ii_delete_folder = False
    elif args.tarball:
        data_dir = '/tmp/ngen_data_dir'
        if os.path.exists(data_dir): 
            os.system(f'rm -rf {data_dir}')
        os.mkdir(data_dir)
        os.system(f'tar -xzf {args.tarball} -C {data_dir}')
        ii_delete_folder = True
    elif args.data_dir and args.tarball:
        raise Exception('Must specify either data folder path or tarball path, not both.')
    else:
        raise Exception('No options set!')
    
    assert os.path.exists(data_dir), f"{data_dir} is an invalid directory"

    validate_data_dir(data_dir)

    if ii_delete_folder: os.system('rm -rf /tmp/ngen_data_dir')
