# Entry point to validating NGen catchment,nexus, and realization files
import sys, json
from ngen.config.realization import NgenRealization
from ngen.config.hydrofabric import NGenCatchmentFile, NGenNexusFile

def main(catchment_file,catchment_subset,nexus_file,nexus_subset,rel_file):
    """
    validate the three config files and sub selections
    """
    # Validate Catchment config
    with open(catchment_file) as fp:
        data = json.load(fp)
        NGenCatchmentFile(**data)

        # Validate catchment subset
        # Get list of catchments
        nfeat = len(data['features'])
        catchments = []
        catchment_pairs = []
        for jfeat in range(nfeat):
            id   = data['features'][jfeat]['id']
            toid = data['features'][jfeat]['properties']['toid']
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
        NGenNexusFile(**data)  

        # Validate catchment subset
        # Get list of catchments
        nfeat = len(data['features'])
        nexi = []
        nexus_pairs = []
        for jfeat in range(nfeat):
            id   = data['features'][jfeat]['id']
            toid = data['features'][jfeat]['properties']['toid']
            nexus_pairs.append([toid,id])
            nexi.append(id)
        
        # Convert to list
        subset_list = nexus_subset.split(',')
        msg = 'Nexus subset includes nexus that were not found in nexus config'
        msg += f'\nNexus from config {nexi}\nNexus in subset {nexus_subset}'
        assert all([jnex in nexi for jnex in subset_list]), msg

    # Validate all nexus in catchment config match those provided 
    msg = 'Nexus-Catchment pairs do not match! Check Catchment and Nexus config files!'
    msg += f'\nPairs from catchment config:{catchments}\nPairs from nexus config:{nexi}'
    assert all([jpair in catchment_pairs for jpair in nexus_pairs]), msg
    assert all([jpair in nexus_pairs for jpair in catchment_pairs]), msg

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
    with open(rel_file) as fp:
        data = json.load(fp)
        NgenRealization(**data)  

    print(f'NGen config validations complete')

if __name__ == "__main__":

    catchment_file   = sys.argv[1]
    catchment_subset = sys.argv[2]
    nexus_file       = sys.argv[3]
    nexus_subset     = sys.argv[4]
    rel_file         = sys.argv[5]

    main(catchment_file,catchment_subset,nexus_file,nexus_subset,rel_file)

    

