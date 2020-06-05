import pprint
import arcpy
import datetime
from arcgis.gis import GIS
from scripts import AGOL_maps_layers

"""
Appropriate layers are found and recorded in layers table,
View Plane, Community Plan Area, missing IDs
Server layers have no layerID

Get layer id from url??
https://services2.arcgis.com/11XBiaBYA9Ep0yNJ/arcgis/rest/services/Community_Plan_Areas/FeatureServer/0

Can tie layers to maps uug, get_layers_from_mapid, but need to find an alternate way to reference layer when id field
is not available -> url,
Search layer data for matching url, pull id from layer table?? <- how is layer table populated?

Some maps will yield a layer id for a layer, other maps will not yield layer id for same layer?
"""

gis = GIS('pro')

app_feature = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\apps_agol'
app_service_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\appid_serviceids'

# map_ids = ['f5882f245099474bb6dae79a0359ddb9']  # Land Use Planning & Development Map
# map_ids = ['20fdd9fc89b84d678193a36947622fa4']  # Parks & Recreation Map
# map_ids = ['8546bcfb9d4a4bdabf51dc121010d789']  # Asset Investment Planning Map
map_ids = ['704629472b9a4b62ae9e2e3b11d6d9b3']  # Government & Admin Map


# Get layers in Land Use Planning Map/App
layer_data = AGOL_maps_layers.get_layers_from_mapid(map_ids[0])
pprint.pprint(layer_data['layer_data'])
pprint.pprint([x['title'] for x in layer_data['layer_data']])


# https://developers.arcgis.com/rest/users-groups-and-items/items-and-item-types.htm
# Query all layers from org.?


def get_layer_data():
    query = f'owner:** AND NOT owner:esri AND title:* AND access:*'
    item_objs = gis.content.search(query=query, item_type='Feature Service', max_items=1000,
                                   outside_org=False)

    data_objs = []
    for obj in item_objs:
        agol_ids = AGOL_maps_layers.scrape_ids_from_description(obj.id)
        # print(dir(obj))
        # print(f"\nobj.name: {obj.name}")
        # print(f"obj.layers: {obj.layers}")
        # # print(f"obj.layers: {obj.keys()}")
        # if 'layerDefinition' in obj.keys():
        #     if 'definitionExpression' in obj.layerDefinition.keys():
                # result['definition'] = obj.layerDefinition.definitionExpression
                # print(f"DEF EXPRESSION: {obj.layerDefinition.definitionExpression}")

        data_obj = {
            'id': obj.id,
            'title': obj.title,
            'owner': obj.owner,
            'access': obj.access,
            'num_views': obj.numViews,
            'date_created': obj.created / 1000,
            'date_modified': obj.modified / 1000,
            'type': obj.type,
            'url': obj.url,
            'definition': '',
            'description_ids': agol_ids
        }

        if data_obj not in data_objs:
            data_objs.append(data_obj)

    return data_objs


def layer_data_to_db(data, table):
    """
    Transfer data to db
    :param data: list of objects [{}, {}, {},...]
    :param table: gdb table
    :return: Number of records inserted
    Account for deleted maps? Bulk refresh? Append new?
    """

    print(f"Running {layer_data_to_db.__name__}...")

    # Need to identify appropriate table fields for records
    fields = ['ID', 'TITLE', 'ACCESS', 'CREATED_DATE', 'MODIFIED_DATE', 'OWNER', 'NUM_VIEWS', 'TYPE', 'DESCRIPTION_IDS',
              'URL'] # 'DEFINITION_EXPRESSION'
    current_ids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]
    # Filter out ids already in target table
    data = [obj for obj in data if obj['id'] not in current_ids and obj['id'] != 0]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0
        new_rows_added = []

        # Iterate over input data
        for record in data:
            if record not in new_rows_added:
                # Data Sanitization
                # if record['assumed_id'] is False:
                #     definition_val = record['definition'][:295] + '...' if record['definition'] else False

                # Data Sanitizing
                desc_ids = record['description_ids']
                if desc_ids is not None:
                    desc_ids = desc_ids[:297] + '...' if len(desc_ids) > 300 else record['description_ids']
                else:
                    desc_ids = ''

                    add_row = (record['id'],
                               record['title'],
                               record['access'].upper(),
                               datetime.datetime.fromtimestamp(record['date_created']),
                               datetime.datetime.fromtimestamp(record['date_modified']),
                               record['owner'],
                               int(record['num_views']),
                               record['type'],
                               desc_ids,
                               record['url']
                               # definition_val,
                               )
                    cursor.insertRow(add_row)
                    print(f"\t\tInserted record: {record['id']}")
                    new_rows_added.append(add_row)
                    count += 1

    if count > 0:
        print(f"\t\t{count} record(s) inserted.")
    return count


# layer_data = get_layer_data()
# pprint.pprint(layer_data)
#
# layer_feature = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\layers_agol_testing'
# AGOL_maps_layers.remove_all_rows(layer_feature)
# layer_data_to_db(layer_data, layer_feature)
