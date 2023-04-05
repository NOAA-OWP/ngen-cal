# Entry point to validating NGen catchment,nexus, and realization files

import sys, json
from typing import Dict
from ngen.config.realization import NgenRealization
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic import Point, Polygon, LineString, MultiPoint, MultiPolygon, MultiLineString

def validate_feature_collection(data):
    type2feat = {"Point":            Point,
                "Polygon":          Polygon,
                "LineString":       LineString,
                "MultiPoint":       MultiPoint,
                "MultiPolygon":     MultiPolygon,                
                "MultiLineString":  MultiLineString
    }
        
    fc = FeatureCollection(features=data['features'])
        
    # Validate each feature
    for j,jfeat in enumerate(fc.features):
        jfeat_json = data['features'][j]
        type = jfeat.geometry.type              
        model = Feature[type2feat[type], Dict]

        feat_model = model(**jfeat_json) # Actual validation step


def validate_catchment(catch,catch_subset):
    """
    Validates the catchment config file and catchment subset
    """

    # Validate the catchment config
    with open(catch) as fp:
        data = json.load(fp)

        assert data['type'] == "FeatureCollection", "catchment_config requires the type to be FeatureCollection"
        assert data['name'] == "catchment_data", "catchment_config requires the type to be FeatureCollection"

        # TODO: crs validation

        validate_feature_collection(data)


    # Validate catchment subset
    # Get list of catchments
    nfeat = len(data['features'])
    catchments = []
    pairs = []
    for jfeat in range(nfeat):
        id   = data['features'][jfeat]['id']
        toid = data['features'][jfeat]['properties']['toid']
        pairs.append([id,toid])
        catchments.append(id)
    
    # Convert to list
    subset_list = catch_subset.split(',')
    msg = 'Catchment subset includes catchments that were not found in nexus config'
    msg += f'\nCatchments from config {catchments}\nCatchments in subset {subset_list}'
    assert all([jcatch in catchments for jcatch in subset_list]), msg

    return pairs, subset_list

def validate_nexus(nexus,nexus_subset):
    """
    Validates the nexus config file and nexus subset
    """
    # Validate the nexus config
    with open(nexus) as fp:
        data = json.load(fp)

        assert data['type'] == "FeatureCollection", "nexus_config requires the type to be FeatureCollection"
        assert data['name'] == "nexus_data", "nexus_config requires the type to be FeatureCollection"

        # TODO: crs validation

        validate_feature_collection(data)

    # Validate catchment subset
    # Get list of catchments
    nfeat = len(data['features'])
    nexi = []
    pairs = []
    for jfeat in range(nfeat):
        id   = data['features'][jfeat]['id']
        toid = data['features'][jfeat]['properties']['toid']
        pairs.append([toid,id])
        nexi.append(id)
    
    # Convert to list
    subset_list = nexus_subset.split(',')
    msg = 'Nexus subset includes nexus that were not found in nexus config'
    msg += f'\nNexus from config {nexi}\nNexus in subset {nexus_subset}'
    assert all([jnex in nexi for jnex in subset_list]), msg

    return pairs, subset_list

def validate_catchmentnexus(catch_pair,nexus_pair,catch_sub,nexus_sub):
    """
    Validate that the provided nexus and catchments match
    """
    # Validate all nexus in catchment config match those provided 
    msg = 'Nexus-Catchment pairs do not match! Check Catchment and Nexus config files!'
    msg += f'\nPairs from catchment config:{catch_pair}\nPairs from nexus config:{nexus_pair}'
    assert all([jpair in catch_pair for jpair in nexus_pair]), msg
    assert all([jpair in nexus_pair for jpair in catch_pair]), msg

    # Validate the sub selected catchments and nexus are consistent
    for jpair in catch_pair:
        jcatch, jnexus = jpair
        if jcatch in catch_sub:
            assert jnexus in nexus_sub, 'Sub selected catchments/nexuses do not match!'

    for jpair in nexus_pair:
        jcatch, jnexus = jpair
        if jnexus in nexus_sub:
            assert jcatch in catch_sub, 'Sub selected catchments/nexuses do not match!'        


def validate_realization(conf):
    """
    Validate that the provided realization file
    """
    #Read the calibration specific info
    with open(conf) as fp:
        data = json.load(fp)
    ngen_realization = NgenRealization(**data)

    # Validate crosswalk
    #TODO

if __name__ == "__main__":
    # 0 conf_validation.py 
    # 1 ./data/catchment_data.geojson 
    # 2 "cat-67,cat-27" 
    # 3 ./data/nexus_data.geojson 
    # 4 "nex-26,nex-34" 
    # 5 ./data/refactored_example_realization_config.json

    # Validate Catchment config
    catchment_file = sys.argv[1]
    catchment_subset_file = sys.argv[2]
    catch_pair, catch_sub = validate_catchment(catchment_file,catchment_subset_file)

    # Validate Nexus config
    nexus_file = sys.argv[3]
    nexus_subset_file = sys.argv[4]
    nexus_pair, nexus_sub = validate_nexus(nexus_file,nexus_subset_file)

    # Validate Catchment-Nexus pairs
    validate_catchmentnexus(catch_pair,nexus_pair,catch_sub,nexus_sub)

    # Validate Realization file
    rel_file = sys.argv[5]
    validate_realization(rel_file)

    print(f'NGen config validation complete')

