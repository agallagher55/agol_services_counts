import arcpy, datetime


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
    fields = ['ID', 'LAYER_NAME', 'AGOL_URL', 'TYPE', 'SERVICE_URL', 'DEFINITION_EXPRESSION']
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
                if record['assumed_id'] is False:
                    definition_val = record['definition'][:295] + '...' if record['definition'] else False
                    add_row = (record['id'],
                               record['layer'],
                               record['agol_url'],
                               record['type'],
                               record['url'],
                               definition_val,
                               )
                    cursor.insertRow(add_row)
                    print(f"\t\tInserted record: {record['layer']}")
                    new_rows_added.append(add_row)
                    count += 1

    if count > 0:
        print(f"\t\t{count} record(s) inserted.")
    return count
