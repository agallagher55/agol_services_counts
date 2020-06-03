import arcpy, datetime


def map_app_data_to_db(data, table):
    """
    Transfer data to db
    :param data: list of objects [{}, {}, {},...]
    :param table: output table - [mapinfo]/[appinfo]
    :return: Number of records inserted
    Account for deleted maps? Bulk refresh? Append new?
    """

    print(f"Running {map_app_data_to_db.__name__}")

    # Need to identify appropriate table fields for records
    fields = ['ID', 'TITLE', 'ACCESS', 'CREATED_DATE', 'MODIFIED_DATE', 'OWNER', 'NUM_VIEWS', 'TYPE', 'DESCRIPTION_IDS',
              'URL']
    current_ids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]
    # Filter out ids already in target table
    data = [obj for obj in data if obj['id'] not in current_ids and obj['id'] != 0]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0
        new_rows_added = []

        # Iterate over input data
        for record in data:
            if record not in new_rows_added:
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
                           )
                cursor.insertRow(add_row)
                print(f"\tInserted record: {record['id']}")
                new_rows_added.append(add_row)
                count += 1
    if count > 0:
        print(f"\t\t{count} record(s) inserted.")
    return count