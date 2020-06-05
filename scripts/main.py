import pprint
import datetime
from arcgis.gis import GIS
from scripts import AGOL_maps_layers
from scripts import quality_assurance

gis = GIS('pro')

if __name__ == '__main__':
    print(datetime.datetime.now())

    # VARIABLES
    app_feature = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\apps_agol'
    map_feature = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\maps_agol'
    layer_feature = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\layers_agol'
    layer_feature_testing = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\layers_agol_testing'

    app_service_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\appid_serviceids'
    layers_maps_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\layerid_mapid'
    app_service_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\appid_serviceids'

    # Remove Data
    # AGOL_maps_layers.remove_all_rows(layer_feature)
    # # AGOL_maps_layers.remove_all_rows(layer_feature_testing)
    # AGOL_maps_layers.remove_all_rows(app_feature)
    # AGOL_maps_layers.remove_all_rows(map_feature)
    # AGOL_maps_layers.remove_all_rows(layers_maps_table)
    # AGOL_maps_layers.remove_all_rows(app_service_table)
    #
    # # GET DATA
    # # a) Get APP Data
    # app_objs = AGOL_maps_layers.get_map_app_data(item_type='app')
    #
    # # # 1) Get MAP Data
    # map_objs = AGOL_maps_layers.get_map_app_data(item_type='map')
    # # pprint.pprint(map_objs)
    #
    # # X) Get ALL layer data
    # layer_data = AGOL_maps_layers.get_map_app_data(item_type='LAYER')
    #
    # # Layer data from maps
    # for obj in map_objs:
    #     # Get Layers from map
    #     obj_data = AGOL_maps_layers.get_layers_from_mapid(obj['id'])['layer_data']
    #     for data in obj_data:
    #         layer_data.append(data)
    #
    # pprint.pprint(layer_data)
    # # Send all layer data to db
    # AGOL_maps_layers.layer_data_to_db(layer_data, layer_feature)
    #
    # # Send data to DB
    # # b) Send app data to db
    # AGOL_maps_layers.map_app_data_to_db(app_objs, app_feature)
    #
    # # 2) Send map data to db
    # AGOL_maps_layers.map_app_data_to_db(data=map_objs, table=map_feature)
    #
    # # 4) Build map - layers lookup table
    # AGOL_maps_layers.layer_map_to_db(map_objs, layers_maps_table)
    #
    # # x) Build app - map lookup table
    # AGOL_maps_layers.appid_serviceid_to_db(app_feature, app_service_table)

    # # 5) Check for duplicates
    AGOL_maps_layers.check_duplicates(app_feature)
    AGOL_maps_layers.check_duplicates(map_feature)
    AGOL_maps_layers.check_duplicates(layer_feature)
    # AGOL_maps_layers.check_duplicates(layer_feature_testing)
    AGOL_maps_layers.check_duplicates(layers_maps_table)
    AGOL_maps_layers.check_duplicates(app_service_table)

    AGOL_maps_layers.remove_duplicates(layer_feature)

    # quality_assurance.appid_mapid_populate(app_feature, map_feature, update_tables=False, update_description=False)

    print(datetime.datetime.now())

# TO DO
# Merge get layer data function with get map/app data?
# Number of connections for id

# ADD populate_appid_mapid_table

# If map references app id, add map id if not present in app table

# ALL APPS SHOULD HAVE A REFERENCE ID TO MAP - CHECK PERSONAL APPS
# Decorator logging function

# Rewrite def layer_map_to_db(map_data, table): to incpororate ALL layer data -> layer data from
# get_map_app_data(layer)

# Duplicates in layers table --> 91dd3d978e3d4324bdb88f9fc5e675e4
