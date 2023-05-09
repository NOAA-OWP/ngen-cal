import sys, os
from ngen.config.realization import NgenRealization
from ngen.config.hydrofabric import CatchmentGeoJSON , NexusGeoJSON 

def validate_paths(dict_obj, key_list):
    """
    Validate properties optionally
    """
    for jkey in key_list:
        if hasattr(dict_obj,jkey):
            # TODO: confirm the os.getcwd(), maybe we want to pass this as an arg
            full_path = os.path.join(os.getcwd(),getattr(dict_obj,jkey))
            assert os.path.exists(full_path), f'{jkey} file path could not be validated! : {dict_obj.jkey}'

def validate(catchment_file,catchment_subset,nexus_file,nexus_subset,realization_file=None):
    """
    validate the three config files and sub selections
    """
    # Validate Catchment config
    serialized_catchments = CatchmentGeoJSON.parse_file(catchment_file)

    # Validate catchment subset
    # Get list of catchments
    catchments = []
    catchment_pairs = []
    for jfeat in serialized_catchments.features:
        id   = jfeat.id
        if id is None: id = jfeat.properties.id # discrepancy between geopandas and pydantic
        toid = jfeat.properties.toid
        catchment_pairs.append([id,toid])
        catchments.append(id)

    # Convert to list
    if len(catchment_subset) > 0:
        catch_subset_list = catchment_subset.split(',')
        msg = 'Catchment subset includes catchments that were not found in nexus config'
        msg += f'\nCatchments from config {catchments}\nCatchments in subset {catchment_subset}'
        assert all([jcatch in catchments for jcatch in catch_subset_list]), msg

    # Validate Nexus config
    serialized_nexus = NexusGeoJSON.parse_file(nexus_file)

    # Validate nexus subset
    nexi = []
    nexus_pairs = []
    for jfeat in serialized_nexus.features:
        id   = jfeat.id
        if id is None: id = jfeat.properties.id # discrepancy between geopandas and pydantic
        toid = jfeat.properties.toid
        nexi.append(id)

    # Convert to list
    if len(nexus_subset) > 0:
        nex_subset_list = nexus_subset.split(',')
        msg = 'Nexus subset includes nexus that were not found in nexus config'
        msg += f'\nNexus from config {nexi}\nNexus in subset {nexus_subset}'
        assert all([jnex in nexi for jnex in nex_subset_list]), msg

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
    if realization_file is not None:

        serialized_realization = NgenRealization.parse_file(realization_file)

        if True: # Turn off path validation if ya want
            fm = serialized_realization.global_config.formulations
            for j,jform in enumerate(fm):
                parms = jform.params
                mods = jform.params.modules
                # We can configuire the key list as to what properties we want to validate
                validate_paths(parms,['config','init_config','library_file'])
                for jmod in mods:
                    validate_paths(jmod.params,['config','init_config','library','library_file'])

        if hasattr(serialized_realization,'catchments'):
            catch_property = serialized_realization.catchments
            realization_catchments = list(catch_property.keys())

            # Verify that all subset catchments are in realization file.
            if len(catchment_subset) > 0:
                msg = f'At least one of the catchments within the subset({catch_subset_list}) is not found within the realization file!'
                assert all([jcatch in realization_catchments for jcatch in catch_subset_list]), msg

            # Verify that all realization catchments are in the catchment geojson
            msg = f'At least one of the catchments within the realization file is not found within the catchment geojson!'
            assert all([jcatch in catchments for jcatch in realization_catchments]), msg

            # Verify that a file exists for every catchment provided in the realization file
            # The forcing path can either be explicit or to a folder to lookin to match a filename pattern
            for jcatch in catch_property:
                ii_found = False
                forcing_path = os.path.join(os.getcwd(),catch_property[jcatch].forcing.path)
                id = jcatch.split('-')[1]

                for jfile in os.listdir(forcing_path):
                    jfile_id = jfile.split('_')[1][:-4]
                    if jfile_id == id: 
                        ii_found = True
                        break

                if not ii_found:
                    raise Exception(f'Could not locate forcing file for {jcatch} in {forcing_path}')
        else:
            pass

    else:
        print('Did not validate realization file!!!')

    print(f'NGen config validations complete')

if __name__ == "__main__":

    if len(sys.argv) > 4:
        catchment_file   = sys.argv[1]
        catchment_subset = sys.argv[2]
        nexus_file       = sys.argv[3]
        nexus_subset     = sys.argv[4]
        realization_file = sys.argv[5]
    else:
        catchment_file = os.environ.get('CATCH_CONF')
        catchment_subset = os.environ.get('CATCH_SUB')
        nexus_file = os.environ.get('NEX_CONF')
        nexus_subset = os.environ.get('NEX_SUB')
        realization_file = os.environ.get('REALIZATION')

    validate(catchment_file,catchment_subset,nexus_file,nexus_subset,realization_file)
