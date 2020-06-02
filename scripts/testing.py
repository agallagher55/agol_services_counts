import pprint
import datetime
from arcgis.gis import GIS
from scripts import AGOL_maps_layers
import arcpy

gis = GIS('pro')

app_feature = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\apps_agol'
app_service_table = r'C:\Users\gallaga\Desktop\MapsandLayers\maps_layers_agol\maps_layers_agol.gdb\appid_serviceids'

map_ids = ['ef11225bc2ff4325bce25022a8143078', '972e2d88a5304d42b1aa644e4099b309']


def populate_appid_serviceid_table(app_table, appid_serviceid_table):
    """
    Send APP_IDs, related SERVICE_IDs to separate table
    :param app_table: Table with app data
    :param appid_serviceid_table:
    :return: total rows added
    """

    # 1) Iterate through app table
    app_fields = ['ID']
    app_service_fields = ['APP_ID', 'SERVICE_ID']
    app_service_data = [row for row in arcpy.da.SearchCursor(appid_serviceid_table, app_service_fields)]

    with arcpy.da.SearchCursor(app_table, field_names=app_fields) as cursor:
        uCur = arcpy.da.InsertCursor(appid_serviceid_table, app_service_fields)

        for row in cursor:
            app_id = row[0]
            print(f"\nAPP ID: {app_id}")

            agol_ids = AGOL_maps_layers.scrape_ids_from_description(app_id)
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


AGOL_maps_layers.get_map_app_data(max_items=5)

