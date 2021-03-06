import pprint
import arcpy
import datetime
import re
from arcgis.gis import GIS
from arcgis.mapping import WebMap

import scripts.decorators as decorators
from scripts import utils

gis = GIS('pro')


# GET DATA FROM AGOL
@decorators.logger
def clean_layer_data(layer_data):
    """
    :param layer_data: list output from get_map_layer_data function
    :return: list of dictionaries with interpolated results - updated id, agol_url, & id_assumed fields
    - Interpolate missing layer ids
    - If layer has no id, it may be a copy of a layer
    - Remove layer that has same url of other layer that also has an id?
    """

    for layer in layer_data:
        print(layer)
        if layer['id'] is False or 'id' not in list(layer.keys()):  # REVIEW THIS LINE

            # Iterate through data again to find original layer - layer with same url but with an id
            for x in layer_data:
                if x['url'] == layer['url'] and 'id' in list(x.keys()):
                    layer['id'] = x['id']
                    layer['agol_url'] = f"https://hrm.maps.arcgis.com/home/item.html?id={layer['id']}"
                    layer['assumed_id'] = True

    return layer_data


# MAP, APP, LAYER DATA
@decorators.logger
def get_map_app_data(my_items=False, owner='**', title='', access='', max_items=999, item_type='MAP'):
    """
    :param my_items: Get maps the belong to current user
    :param owner: Owner account
    :param title: Search for services by item title
    :param access: ['private', 'shared', 'public']
    :param max_items:
    :param item_type: MAP, APP
    :return: list of objects - [{}, {}, {},...] title, type, id, created date, access attributes
    Filter maps by created date, modified date, creator, access
    """

    valid_item_types = {
        'MAP': 'Web Map',
        'APP': 'Web Mapping Application',
        'LAYER': 'Feature Service',
        'COLLECTION': 'Feature Collection'
    }

    if item_type.upper() not in valid_item_types.keys():
        raise Exception(f"{item_type.upper()} is not a valid service item type!")

    access_types = ['private', 'shared', 'public']

    if access not in access_types and len(access) > 0:
        raise Exception(f"{access} is not recognized as a valid access type -> {', '.join(access_types)}")

    if my_items:
        owner = gis.users.me.username

    query = f'owner:{owner} AND NOT owner:esri AND title:{title}* AND access:{access}*'

    # Filter services by title, creator, access
    item_objs = gis.content.search(query=query,
                                   item_type=valid_item_types[item_type.upper()],
                                   max_items=max_items,
                                   outside_org=False)
    data_objs = []

    for obj in item_objs:
        agol_ids = utils.scrape_ids_from_description(obj.id)

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
        }

        if agol_ids:
            data_obj['description_ids'] = agol_ids

        if data_obj not in data_objs:
            data_objs.append(data_obj)

    return data_objs


# LAYER DATA, FROM MAPS
@decorators.logger
def get_layers_from_mapid(map_id):
    """
    :param map_id: AGOL unique item ID
    :return: list of objects containing layer information (ARCGISFeatureLayers) associated with map ID
            {'title': web_map_item.item.title,
            'map_id': map_id,
            'layer_data': cleaned_results}
    """
    web_map_item = WebMap(gis.content.get(map_id))
    print(f"\nProcessing {get_layers_from_mapid.__name__} for map: {web_map_item.item.title}...")

    results = []

    if web_map_item.layers:
        query = f'owner:* AND NOT owner:esri AND title:* AND access:*'
        layer_search = gis.content.search(query=query,
                                          item_type='Feature Service',
                                          max_items=1000,
                                          outside_org=False)
        layer_url_ids = [{'url': layer.url, 'id': layer.id} for layer in layer_search]

        for layer in web_map_item.layers:

            result = {
                'id': layer.itemId if "itemId" in list(layer.keys()) else False,
                'assumed_id': False,
                'id_name': layer.id,
                'title': layer.title,
                'url': layer.url if 'url' in layer.keys() else False,
                'type': layer.layerType if "layerType" in layer.keys() else False
            }

            if 'layerDefinition' in layer.keys():
                if 'definitionExpression' in layer.layerDefinition.keys():
                    result['definition'] = layer.layerDefinition.definitionExpression

            # If no item id, cross reference with all layers table using url to get id
            if result['id'] is False:
                if result['url']:
                    result_url = result['url'].strip(r'/0')

                    # Search all layers (in current webmap) table for matching url
                    for url_id in layer_url_ids:
                        if result_url.upper() in url_id['url'].upper():
                            # print("\tMATCH FOUND")
                            result['id'] = url_id['id']
                            result['assumed_id'] = True
                            break

            results.append(result)

    cleaned_results = clean_layer_data(results)
    return {'title': web_map_item.item.title,
            'map_id': map_id,
            'layer_data': cleaned_results}


# EXPORT DATA
@decorators.logger
def map_app_data_to_db(data, table):
    """
    Transfer data to db
    :param data: list of objects [{}, {}, {},...]
    :param table: output table - [mapinfo/appinfo]
    :return: Number of records inserted
    Account for deleted maps? Bulk refresh? Append new?
    """

    # Need to identify appropriate table fields for records
    fields = ['ID', 'TITLE', 'ACCESS', 'CREATED_DATE', 'MODIFIED_DATE', 'OWNER', 'NUM_VIEWS', 'TYPE', 'DESCRIPTION_IDS',
              'URL']

    # Filter out ids already in target table
    current_ids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]
    data = [obj for obj in data if obj['id'] not in current_ids and obj['id'] != 0]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0
        new_rows_added = []

        # Iterate over input data
        for record in data:
            if record not in new_rows_added:

                # Data Sanitizing
                # if desc_ids is not None:
                if 'description_ids' in record:
                    desc_ids = record['description_ids']
                    desc_ids = desc_ids[:297] + '...' if len(desc_ids) > 300 else record['description_ids']
                else:
                    desc_ids = None

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
                           )
                cursor.insertRow(add_row)
                print(f"\tInserted record: {record['id']}")
                new_rows_added.append(add_row)
                count += 1
    if count > 0:
        print(f"\t\t{count} record(s) inserted.")
    return count


@decorators.logger
def layer_data_to_db(data, table, from_map_id=False):
    """
    Transfer data to db
    :param data: list of objects [{}, {}, {},...]
    :param table: gdb table
    :param from_map_id: sending data to table from get_layer_from_mapid function
    :return: Number of records inserted
    Account for deleted maps? Bulk refresh? Append new?
    """

    print(f"Running {layer_data_to_db.__name__}...")

    fields = ['ID', 'TITLE', 'ACCESS', 'DEFINITION_EXPRESSION', 'CREATED_DATE', 'MODIFIED_DATE',
              'OWNER', 'NUM_VIEWS', 'TYPE', 'DESCRIPTION_IDS', 'URL']

    current_ids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]

    # Filter out ids already in target table
    data = [obj for obj in data if obj['id'] not in current_ids and obj['id'] != 0]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0
        new_rows_added = []

        # Iterate over input data
        for record in data:
            if record not in new_rows_added:
                try:
                    # ALL RECORDS SHOULD HAVE ID, TITLE, TYPE, URL
                    record_id = record['id']
                    title = record['title']
                    record_type = record['type']
                    url = record['url']

                    # Check records for:'definition', 'description_ids', 'num_views', 'owner', 'date_modified',
                    # 'date_created', 'access'

                    definition = record['definition'][:295] + '...' if 'definition' in record else None
                    num_views = int(record['num_views']) if 'num_views' in record else None
                    owner = record['owner'] if 'owner' in record else None
                    date_modified = datetime.datetime.fromtimestamp(record['date_modified']) \
                        if 'date_modified' in record else None
                    date_created = datetime.datetime.fromtimestamp(record['date_created']) \
                        if 'date_created' in record else None
                    access = record['access'].upper() if 'access' in record else None
                    desc_ids = record['description_ids'][:295] + '...' \
                        if 'description_ids' in record and record['description_ids'] is not None else None

                    add_row = (record_id, title, access, definition, date_created, date_modified, owner, num_views,
                               record_type, desc_ids, url)


                    cursor.insertRow(add_row)
                    print(f"\t\tInserted record: {record['id']}")
                    new_rows_added.append(add_row)
                    count += 1

                except Exception as e:
                    print(f'ERROR: {e}')
                    print(record)
                    print(f"\t{add_row}")

    if count > 0:
        print(f"\t\t{count} record(s) inserted.")
    return count


@decorators.logger
def layer_map_to_db(map_data, table):
    """
    Transfer layer data to db
    :param map_data: list of map objects [{}, {}, {},...]
    :param table: output table
    :return: Number of rows inserted
    """
    print(f"Running {layer_map_to_db.__name__}")

    fields = ['LAYER_ID', 'MAP_ID']

    # layer_data = get_map_app_data(item_type='LAYER')

    added_rows = []

    for obj in map_data:
        mapid = obj['id']
        map_layers = get_layers_from_mapid(mapid)
        layers = map_layers['layer_data']
        current_rows = [row for row in arcpy.da.SearchCursor(table, fields)]

        if mapid:
            with arcpy.da.InsertCursor(table, fields) as cur:
                for layer in layers:
                    add_row = (layer['id'], mapid)

                    if layer['id'] and add_row not in current_rows and add_row not in added_rows:
                        cur.insertRow(add_row)
                        added_rows.append(add_row)
                        print(f"\tAdded: {add_row}")

    print(f"\tAdded {len(added_rows)} rows")


@decorators.logger
def appid_serviceid_to_db(app_table, appid_serviceid_table):
    """
    APP ID - Scraped Service IDs
    :param app_table: Table with app data
    :param appid_serviceid_table: output tables
    :return: total rows added
    """

    app_id_fields = ['ID', 'DESCRIPTION_IDS']
    app_service_fields = ['APP_ID', 'SERVICE_ID']
    app_service_data = [row for row in arcpy.da.SearchCursor(appid_serviceid_table, app_service_fields)]

    with arcpy.da.SearchCursor(app_table, field_names=app_id_fields) as cursor:
        ucur = arcpy.da.InsertCursor(appid_serviceid_table, app_service_fields)

        for row in cursor:
            app_id = row[0]
            agol_ids = row[1]
            print(f"\nAPP ID: {app_id}")
            print(f"AGOL IDs: {agol_ids}")

            if agol_ids and len(agol_ids) > 295:
                agol_ids = utils.scrape_ids_from_description(app_id)

            rows_inserted = 0

            if agol_ids and agol_ids[0] != '':
                agol_ids = agol_ids.split("|")

                if len(agol_ids) == 1:
                    add_row = (app_id, agol_ids[0])

                    if add_row not in app_service_data:
                        ucur.insertRow(add_row)
                        rows_inserted += 1
                        print(f"\tADDED ROW: {add_row}")

                else:  # App can reference multiple services
                    for agol_id in agol_ids:
                        add_row = (app_id, agol_id)

                        if add_row not in app_service_data:
                            ucur.insertRow(add_row)
                            rows_inserted += 1
                            print(f"\tADDED ROW: {add_row}")

        del ucur
        return rows_inserted


# def populate_appid_serviceid_table(app_table, appid_serviceid_table):
#     """
#     Send APP_IDs, related SERVICE_IDs to separate table
#     :param app_table: Table with app data
#     :param appid_serviceid_table:
#     :return: total rows added
#     """
#
#     # 1) Iterate through app table
#     app_fields = ['ID']
#     app_service_fields = ['APP_ID', 'SERVICE_ID']
#     app_service_data = [row for row in arcpy.da.SearchCursor(appid_serviceid_table, app_service_fields)]
#
#     with arcpy.da.SearchCursor(app_table, field_names=app_fields) as cursor:
#         uCur = arcpy.da.InsertCursor(appid_serviceid_table, app_service_fields)
#
#         for row in cursor:
#             app_id = row[0]
#             print(f"\nAPP ID: {app_id}")
#
#             agol_ids = AGOL_maps_layers.scrape_ids_from_description(app_id)
#             rows_inserted = 0
#
#             if agol_ids:
#                 service_ids = agol_ids.split('|')
#
#                 if agol_ids[0] != '':
#                     print(f"{app_id}: {service_ids}")
#
#                     if len(service_ids) == 1:
#                         add_row = (app_id, service_ids[0])
#
#                         if add_row not in app_service_data:
#                             uCur.insertRow(add_row)
#                             rows_inserted += 1
#                             print(f"\tADDED ROW: {add_row}")
#
#                     else:
#                         for id in service_ids:
#                             add_row = (app_id, id)
#
#                             if add_row not in app_service_data:
#                                 uCur.insertRow(add_row)
#                                 rows_inserted += 1
#                                 print(f"\tADDED ROW: {add_row}")
#
#         del uCur
#         return rows_inserted
