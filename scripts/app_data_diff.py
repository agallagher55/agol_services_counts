def app_data_to_db(data, table):
    """
    Transfer data from json to db
    :param data: list of dictionaries
    :param table: gdb table
    :return: Number of records inserted
    """
    print(f"Running {app_data_to_db.__name__}")

    fields = ['ID', 'TITLE', 'ACCESS', 'CREATED_DATE', 'MODIFIED_DATE', 'OWNER', 'NUM_VIEWS', 'TYPE', 'DESCRIPTION_IDS', 'URL']
    current_ids = [row[0] for row in arcpy.da.SearchCursor(table, 'ID')]

    with arcpy.da.InsertCursor(table, fields) as cursor:
        count = 0
        for record in data:
            if record['id'] not in current_ids:
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
                                  desc_ids,
                                  record['url']
                                  ))
                print(f"\tInserted record: {record['id']}")
                count += 1
    if count > 0:
        print(f"\t\t{count} records inserted.")