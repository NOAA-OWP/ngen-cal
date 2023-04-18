# Entry point to validating NGen catchment,nexus, and realization files
import sys, json
from ngen.config.realization import NgenRealization
from ngen.config.hydrofabric import CatchmentGeoJSON , NexusGeoJSON 

def validate(catchment_file,catchment_subset,nexus_file,nexus_subset,rel_file=None):
    """
    validate the three config files and sub selections
    """
    # Validate Catchment config
    with open(catchment_file) as fp:
        data = json.load(fp)
        CatchmentGeoJSON(**data)

        serialized_catchments = CatchmentGeoJSON.parse_file(catchment_file)

        # Validate catchment subset
        # Get list of catchments
        catchments = []
        catchment_pairs = []
        for jfeat in serialized_catchments.features:
            id   = jfeat.id
            if id is None: id = jfeat.properties.id # descrapancy between geopandas and pydantic
            toid = jfeat.properties.toid
            catchment_pairs.append([id,toid])
            catchments.append(id)

        # Convert to list
        subset_list = catchment_subset.split(',')
        msg = 'Catchment subset includes catchments that were not found in nexus config'
        msg += f'\nCatchments from config {catchments}\nCatchments in subset {subset_list}'
        assert all([jcatch in catchments for jcatch in subset_list]), msg

    # Validate Nexus config
    with open(nexus_file) as fp:
        data = json.load(fp)
        NexusGeoJSON(**data)  

        serialized_nexus = NexusGeoJSON.parse_file(nexus_file)

        # Validate nexus subset
        # Get list of catchments
        nexi = []
        nexus_pairs = []
        for jfeat in serialized_nexus.features:
            id   = jfeat.id
            if id is None: id = jfeat.properties.id # descrapancy between geopandas and pydantic
            toid = jfeat.properties.toid
            nexi.append(id)
        
        # Convert to list
        subset_list = nexus_subset.split(',')
        msg = 'Nexus subset includes nexus that were not found in nexus config'
        msg += f'\nNexus from config {nexi}\nNexus in subset {nexus_subset}'
        assert all([jnex in nexi for jnex in subset_list]), msg

    # Validate all nexus in catchment config match those provided 
    msg = 'Nexus-Catchment pairs do not match! Check Catchment and Nexus config files!'
    msg += f'\nPairs from catchment config:{catchments}\nPairs from nexus config:{nexi}'
    assert all([jpair[1] in nexi for jpair in catchment_pairs]), msg

    # Validate the sub selected catchments and nexus are consistent
    for jpair in catchment_pairs:
        jcatch, jnexus = jpair
        if jcatch in catchment_subset:
            assert jnexus in nexus_subset, 'Sub selected catchments/nexuses do not match!'

    for jpair in nexus_pairs:
        jcatch, jnexus = jpair
        if jnexus in nexus_subset:
            assert jcatch in catchment_subset, 'Sub selected catchments/nexuses do not match!'        

    # Validate Realization config
    if rel_file is not None:
        with open(rel_file) as fp:
            data = json.load(fp)
            NgenRealization(**data)  
    else:
        print(f'Did not validate realization file!!!')

    print(f'NGen config validations complete')

if __name__ == "__main__":

    catchment_file   = sys.argv[1]
    catchment_subset = sys.argv[2]
    nexus_file       = sys.argv[3]
    nexus_subset     = sys.argv[4]
    rel_file         = sys.argv[5]

    validate(catchment_file,catchment_subset,nexus_file,nexus_subset,rel_file)

    

