import arcpy
from arcgis.gis import GIS
from scripts import AGOL_maps_layers

"""
Update service ID with MAP/APP connections
- Get map connection to app
- 1) Get connections from appid_serviceid table
- 2) **Query App id, scrape agol_ids (map_ids)
- Write service description
- Update - append to current description
"""

gis = GIS('pro')


def scrape_mapids_from_lookup(app_id, lookup_table):
    matches = []
    where_clause = f"APP_ID LIKE '{app_id}'"
    app_service_fields = ['APP_ID', 'SERVICE_ID']
    with arcpy.da.SearchCursor(lookup_table, app_service_fields, where_clause=where_clause) as cursor:
        for appid, serviceid in cursor:
            matches.append(serviceid)
    return matches


def get_mapids_from_appid(app_id, app_map_lookup_table):
    # Scrape ids from app service description
    agol_ids = AGOL_maps_layers.scrape_ids_from_description(app_id)
    ids_from_server_description = agol_ids.split('|') if agol_ids else None

    # Scrape mapids from lookup table
    ids_from_lookup = scrape_mapids_from_lookup(app_id=app_id, lookup_table=app_map_lookup_table)
    all_ids = list(set(ids_from_server_description + ids_from_lookup)) if ids_from_server_description else ids_from_lookup

    return all_ids


def update_description(map_ids):
    # Format service description
    description = '\n'.join([str(f"MAP: {gis.content.get(x).title} - ID: {x}") for x in map_ids])

    app_item = gis.content.get('b2bd8b72c7864c86956ba541b53ec556')

    # Update - append to current description
    new_description = f"{app_item.description.strip()}<br><br><i>Auto Format:</i><br> {description}"
    if description not in app_item.description:
        item_update_success = app_item.update({'description': f"{new_description}"})

        if item_update_success:
            print(f"Update successful;\n{description}")
        else:
            print("Update FAILED")
    else:
        print("App description already formatted.")


def update_app_description(app_id, app_map_lookup_table):
    map_ids = get_mapids_from_appid(app_id, app_map_lookup_table)
    update_description(map_ids=map_ids)


if __name__ == "__main__":
    update_app_description('b2bd8b72c7864c86956ba541b53ec556',
                           r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\appid_serviceids')
