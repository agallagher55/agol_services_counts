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

    app_service_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\appid_serviceids'
    layers_maps_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\layerid_mapid'
    app_service_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\appid_serviceids'

    # a) Get APP Data
    app_objs = AGOL_maps_layers.get_map_app_data(item_type='app')

    # b) Send app data to db
    AGOL_maps_layers.remove_all_rows(app_feature)
    AGOL_maps_layers.map_app_data_to_db(app_objs, app_feature)

    # 1) Get MAP Data
    map_objs = AGOL_maps_layers.get_map_app_data(item_type='map')
    # pprint.pprint(map_objs)

    # 2) Send map data to db
    AGOL_maps_layers.remove_all_rows(map_feature)
    AGOL_maps_layers.map_app_data_to_db(data=map_objs, table=map_feature)

    # 3) Send layer data to db
    # AGOL_maps_layers.remove_all_rows(layer_feature)
    # layers_inserted = 0
    # for obj in map_objs:
    #     print(obj)
    #     layer_data = AGOL_maps_layers.get_layers_from_mapid(obj['id'])['layer_data']
    #     layers_inserted += AGOL_maps_layers.layer_data_to_db(layer_data, layer_feature)
    #     # pprint.pprint(layer_data)
    # print(f"\n{layers_inserted} layers inserted in total")

    # # 4) Build map - layers lookup table
    # AGOL_maps_layers.remove_all_rows(layers_maps_table)
    # AGOL_maps_layers.layer_map_to_db(map_objs, layers_maps_table)
    #
    # # x) Build app - map lookup table
    # AGOL_maps_layers.remove_all_rows(app_service_table)
    # AGOL_maps_layers.appid_serviceid_to_db(app_feature, app_service_table)
    #
    # # 5) Check for duplicates
    # AGOL_maps_layers.check_duplicates(app_feature)
    # AGOL_maps_layers.check_duplicates(map_feature)
    # AGOL_maps_layers.check_duplicates(layer_feature)
    # AGOL_maps_layers.check_duplicates(layers_maps_table)
    # AGOL_maps_layers.check_duplicates(app_service_table)

    # quality_assurance.appid_mapid_populate(app_feature, map_feature, update_tables=False, update_description=False)

    print(datetime.datetime.now())

# TO DO
# Merge functions for app_data_to_db, map_data_to_db

# Implement default values using OR operator

# ADD populate_appid_mapid_table

# Remove description IDs from Apps table - impacts QA Script
# If map references app id, add map id if not present in app table
# Merge functions - function cleanup

# ALL APPS SHOULD HAVE A REFERENCE ID TO MAP - CHECK PERSONAL APPS
# Decorator logging function

# SETUP - See which layers are in which apps
# Join lookup table to map table
# Add relate from layer table to lookup table
