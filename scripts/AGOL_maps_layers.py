import pprint
import arcpy
import datetime
import re
from arcgis.gis import GIS
from arcgis.mapping import WebMap

gis = GIS('pro')


# Utility Functions
def scrape_ids_from_description(item_id):
    """
    :param item_id: id of AGOL item
    :return: string of ids separated by '|'
    """
    item = gis.content.get(item_id)
    pattern = r'\b\w{32}\b'

    print(f"Running {scrape_ids_from_description.__name__} function on {item_id}...")

    agol_ids = ''
    if item.description is not None:
        agol_ids = '|'.join(set(filter(lambda x: x != item.id, re.findall(pattern, item.description))))

    if agol_ids:
        print(f"\tAGOL IDs found: {agol_ids}")
        return agol_ids


def check_duplicates(feature):
    print(f"Running {check_duplicates.__name__} function on {feature}...")
    fields = [f.name for f in arcpy.ListFields(feature) if f.name != 'OBJECTID']
    data = [row for row in arcpy.da.SearchCursor(feature, fields)]
    dups = len(data) - len(set(data))

    if dups > 0:
        print(f"\t{dups} duplicate rows found in {feature}")
        return dups


def remove_all_rows(table):
    """
    Remove all rows from table
    :param table:
    :return: number of rows deleted
    """
    print(f"Running {remove_all_rows.__name__} function on {table}...")
    with arcpy.da.UpdateCursor(table, "*") as cur:
        del_count = 0
        for row in cur:
            cur.deleteRow()
            del_count += 1
    print(f"\tDeleted {del_count} records")
    del cur
    return del_count


# GET DATA FROM AGOL
def get_map_app_data(my_items=False, owner='**', title='', access='', max_items=999, item_type='MAP'):
    """
    :param my_items: Get maps the belong to current user
    :param owner: Owner account
    :param title:
    :param access: ['private', 'shared', 'public']
    :param max_items:
    :param item_type: MAP, APP
    :return: list of map objects - title, type, id, created date, access attributes
    Filter maps by created date, modified date, creator, access
    """

    print(f"Running {get_map_app_data.__name__} function...")

    valid_item_types = {'MAP': 'Web Map', 'APP': 'Web Mapping Application'}
    assert item_type.upper() in valid_item_types.keys()

    if my_items is True:
        owner = gis.users.me.username

    access_types = ['private', 'shared', 'public']
    if access not in access_types and len(access) > 0:
        raise Exception(f"{access} is not recognized as a valid access type -> {', '.join(access_types)}")

    query = f'owner:{owner} AND NOT owner:esri AND title:{title}* AND access:{access}*'

    # Filter maps by title, creator, access
    item_objs = gis.content.search(query=query, item_type=valid_item_types[item_type.upper()], max_items=max_items, outside_org=False)
    data_objs = []

    for obj in item_objs:
        agol_ids = scrape_ids_from_description(obj.id)

        data_obj = {
            'id': obj.id,
            'title': obj.title,
            'owner': obj.owner,
            'access': obj.access,
            'num_views': obj.numViews,
            'date_created': obj.created / 1000,
            'date_modified': obj.modified / 1000,
            'date_created_formatted': datetime.datetime.fromtimestamp(obj.created / 1000).strftime(
                "%A, %B %d, %Y %I:%M:%S"),
            'date_modified_formatted': datetime.datetime.fromtimestamp(obj.modified / 1000).strftime(
                "%A, %B %d, %Y %I:%M:%S"),
            'type': obj.type,
            'url': obj.url,
            'description_ids': agol_ids
        }

        if data_obj not in data_objs:
            data_objs.append(data_obj)

    return data_objs


def search_maps_for_layers(layer_id, maps_data):
    """
    Search for maps that contain a layer
    :param layer_id: id of layer you wish to query maps for
    :param maps_data: list of map objects to search
    :return: {layer_id: [map_id: map_title]}
    """

    print(f"Running {search_maps_for_layers.__name__}...")

    map_data = {layer_id: []}
    layer_title = gis.content.get(layer_id).title

    for obj in maps_data:
        print(obj)
        # if layer_id in [x['id'] for x in obj['layers']]:
        if layer_id == obj['id']:
            print(f"Found layer {layer_title} in {obj['title']} map")
            map_data[layer_id].append({obj['id']: obj['title']})

    pprint.pprint(map_data)
    return map_data


def clean_layer_data(layer_data):
    """
    - Interpolate missing layer ids
    - If layer has no id, it may be a copy of a layer
    - Remove layer that has same url of other layer that also has an id?
    :param layer_data: list output from get_map_layer_data function
    :return: list of dictionaries with interpolated results - updated id field, updated agol_url field, id_assumed field
    """
    for layer in layer_data:
        if 'id' is False or 'id' not in list(layer.keys()):

            # Iterate through data again to find original layer - layer with same url but with an id
            for x in layer_data:
                if x['url'] == layer['url'] and 'id' in list(x.keys()):
                    layer['id'] = x['id']
                    layer['agol_url'] = f"https://hrm.maps.arcgis.com/home/item.html?id={layer['id']}"
                    layer['assumed_id'] = True

    return layer_data


def get_layers_from_mapid(map_id):
    """
    :param map_id: AGOL unique item ID
    :return: list of objects containing layer information associated with map ID
            {'title': wm_item.item.title,
            'map_id': map_id,
            'layer_data': cleaned_results}
    """
    wm_item = WebMap(gis.content.get(map_id))
    print(f"\nProcessing {get_layers_from_mapid.__name__} for map: {wm_item.item.title}...")

    results = []

    if wm_item.layers:
        for layer in wm_item.layers:
            result = {'id_name': layer.id,
                      'layer': layer.title,
                      'type': False,
                      'definition': False,
                      'url': False,
                      'id': False,
                      'agol_url': False,
                      'assumed_id': False
                      }

            if "layerType" in layer.keys():
                result['type'] = layer.layerType

            if "itemId" in list(layer.keys()):
                result['id'] = layer.itemId
                result['agol_url'] = f"https://hrm.maps.arcgis.com/home/item.html?id={result['id']}"

            if 'url' in layer.keys():
                result['url'] = layer.url

            if 'layerDefinition' in layer.keys():
                if 'definitionExpression' in layer.layerDefinition.keys():
                    result['definition'] = layer.layerDefinition.definitionExpression

            results.append(result)

    cleaned_results = clean_layer_data(results)
    return {'title': wm_item.item.title,
            'map_id': map_id,
            'layer_data': cleaned_results}


# EXPORT DATA TO DB
def layer_data_to_db(data, table):
    """
    Transfer map data from json to db
    :param data: List of dictionaries
    :param table: gdb table
    :return: number of inserted records

    Bugs
    Account for deleted maps? Bulk refresh? Append new?
    Multiple Ids recorded
    """

    print(f"Running {layer_data_to_db.__name__}...")

    fields = ['ID', 'LAYER_NAME', 'AGOL_URL', 'TYPE', 'SERVICE_URL', 'DEFINITION_EXPRESSION']
    current_layerids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0

        for record in data:
            if record['id'] != 0 and record['id'] not in current_layerids and record['assumed_id'] is False:
                # print(f"\t{record}")

                if record['definition']:
                    definition_val = record['definition'][:295] + '...'
                else:
                    definition_val = False

                cursor.insertRow((record['id'],
                                  record['layer'],
                                  record['agol_url'],
                                  record['type'],
                                  record['url'],
                                  definition_val,
                                  ))
                print(f"\t\tInserted layer: {record['layer']}")
                count += 1

    if count > 0:
        print(f"\t\t{count} record(s) inserted.")
    return count


def app_data_to_db(data, table):
    """
    Transfer app data from json to db
    :param data: list of dictionaries
    :param table: gdb table
    :return: Number of records inserted
    """
    print(f"Running {app_data_to_db.__name__}")

    fields = ['ID', 'TITLE', 'ACCESS', 'CREATED_DATE', 'MODIFIED_DATE', 'OWNER', 'NUM_VIEWS', 'TYPE', 'URL', 'DESCRIPTION_IDS']
    current_appids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0
        for record in data:
            if record['id'] not in current_appids:
                desc_ids = record['description_ids']
                if desc_ids is not None:
                    if len(desc_ids) > 300:
                        desc_ids = desc_ids[:297] + '...'
                else:
                    desc_ids = ''
                cursor.insertRow((record['id'],
                                  record['title'],
                                  record['access'].upper(),
                                  datetime.datetime.fromtimestamp(record['date_created']),
                                  datetime.datetime.fromtimestamp(record['date_modified']),
                                  record['owner'],
                                  int(record['num_views']),
                                  record['type'],
                                  record['url'],
                                  desc_ids
                                  ))
                print(f"\tInserted app: {record['id']}")
                count += 1
    if count > 0:
        print(f"\t\t{count} records inserted.")


def map_data_to_db(data, table):
    """
    Transfer map data from json to db
    :param data: list of dictionaries
    :param table: gdb table
    :return: Number of records inserted
    Account for deleted maps? Bulk refresh? Append new?
    """
    print(f"Running {map_data_to_db.__name__}")

    fields = ['ID', 'TITLE', 'ACCESS', 'CREATED_DATE', 'MODIFIED_DATE', 'OWNER', 'TYPE', 'DESCRIPTION_IDS', 'NUM_VIEWS', 'URL']
    current_mapids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0
        for record in data:
            if record['id'] not in current_mapids:
                desc_ids = record['description_ids']
                if desc_ids is not None:
                    if len(desc_ids) > 300:
                        desc_ids = desc_ids[:297] + '...'
                else:
                    desc_ids = ''
                cursor.insertRow((record['id'],
                                  record['title'],
                                  record['access'].upper(),
                                  datetime.datetime.fromtimestamp(record['date_created']),
                                  datetime.datetime.fromtimestamp(record['date_modified']),
                                  record['owner'],
                                  record['type'],
                                  desc_ids,
                                  record['num_views'],
                                  record['url']
                                  ))
                print(f"\tInserted map: {record['id']}")
                count += 1
    if count > 0:
        print(f"\t\t{count} records inserted.")


def layer_map_to_db(map_data, table):
    print(f"Running {layer_map_to_db.__name__}")

    fields = ['LAYER_ID', 'MAP_ID']

    added_rows = []

    for obj in map_data:
        mapid = obj['id']
        map_layers = get_layers_from_mapid(mapid)
        layers = map_layers['layer_data']
        current_rows = [row for row in arcpy.da.SearchCursor(table, fields)]
        # print(current_rows)

        if mapid:
            with arcpy.da.InsertCursor(table, fields) as cur:
                for layer in layers:
                    add_row = (layer['id'], mapid)

                    if layer['id'] and add_row not in current_rows and add_row not in added_rows:
                        cur.insertRow(add_row)
                        added_rows.append(add_row)
                        print(f"Added: {add_row}")

    print(f"Added {len(added_rows)} rows")


def appid_serviceid_to_db(app_table, appid_serviceid_table):
    """
    Send APP_IDs, related SERVICE_IDs to separate table
    :param app_table: Table with app data
    :param appid_serviceid_table:
    :return: total rows added
    """

    print(f"Running {appid_serviceid_to_db.__name__}")

    app_fields = ['ID']
    app_service_fields = ['APP_ID', 'SERVICE_ID']
    app_service_data = [row for row in arcpy.da.SearchCursor(appid_serviceid_table, app_service_fields)]

    with arcpy.da.SearchCursor(app_table, field_names=app_fields) as cursor:
        uCur = arcpy.da.InsertCursor(appid_serviceid_table, app_service_fields)

        for row in cursor:
            app_id = row[0]
            print(f"\nAPP ID: {app_id}")

            agol_ids = scrape_ids_from_description(app_id)
            rows_inserted = 0

            if agol_ids:
                service_ids = agol_ids.split('|')

                if agol_ids[0] != '':
                    print(f"{app_id}: {service_ids}")

                    if len(service_ids) == 1:
                        add_row = (app_id, service_ids[0])

                        if add_row not in app_service_data:
                            uCur.insertRow(add_row)
                            rows_inserted += 1
                            print(f"\tADDED ROW: {add_row}")

                    else:
                        for id in service_ids:
                            add_row = (app_id, id)

                            if add_row not in app_service_data:
                                uCur.insertRow(add_row)
                                rows_inserted += 1
                                print(f"\tADDED ROW: {add_row}")

        del uCur
        return rows_inserted