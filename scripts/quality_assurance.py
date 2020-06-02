def appid_mapid_populate(app_table, map_table, update_tables=False, update_description=False):
    """
    - If app references map id, add app id in map table if not already present
    - IF MORE THAN ONE REFERENCE ID
    - IN APPS TABLE - CHECK REFERENCE IDS FOR MAP ID
    - IN MAPS TABLE - CHECK REFERENCE IDS FOR APP ID
    :return: Object: Map record missing appropriate appid - {APPID: MAPID}
    """

    print(f"Running {appid_mapid_populate.__name__}")

    import arcpy
    import pprint
    from arcgis.gis import GIS

    gis = GIS('pro')

    missing_map_records = []
    no_app_reference = {}
    map_ids = [row[0] for row in arcpy.da.SearchCursor(map_table, ["ID"])]

    print("\nChecking apps table..")

    apps_expression = "DESCRIPTION_IDS <> ''"
    with arcpy.da.SearchCursor(app_table, ["ID", "DESCRIPTION_IDS"], where_clause=apps_expression) as cursor:
        for app_id, desc_ids in cursor:
            map_ref_ids = desc_ids.split('|')

            print(f"\nApp ID: {app_id}")
            print(f"Map Reference IDs: {map_ref_ids}")

            # Check map table for reverse reference to that app
            print("Checking maps table for app reference...")
            for map_id in map_ref_ids:
                if map_id in map_ids:   # We have map id in AGOL maps table
                    # Get app id references for matching map record
                    expression = f"ID LIKE '{map_id}'"
                    app_id_references = [row[0].split('|') for row in arcpy.da.SearchCursor(map_table, ["DESCRIPTION_IDS"], where_clause=expression)][0]

                    if app_id not in app_id_references:
                        no_app_reference[app_id] = map_id

                        if update_tables:
                            # EDIT MAPS TABLE TO ADD APP REFERENCE
                            with arcpy.da.UpdateCursor(map_table, field_names=["ID", "DESCRIPTION_IDS"], where_clause=expression) as uCur:
                                for record in uCur:
                                    if record[1] != '':
                                        record[1] = record[1] + "|" + app_id
                                    else:
                                        record[1] = app_id
                                    uCur.updateRow(record)

                        # EDIT ITEM DESCRIPTION
                        if update_description:
                            item = gis.content.get(app_id)
                            if str(app_id) not in item.description:
                                item.update({'description': item.description + f'<br>APP - ID {str(app_id)}'})
                            else:
                                print("Description already updated")
                else:
                    # REFERENCE IS MADE TO MAP IN APP TABLE, BUT THE MAP IS NOT FOUND IN MAP TABLE
                    missing_map_records.append(map_id)

    print(f"\nMissing map records: {missing_map_records}")
    print("No App reference in map table - {APPID: MAPID}:")
    pprint.pprint(no_app_reference)
    return no_app_reference
