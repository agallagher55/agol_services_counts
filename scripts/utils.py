import arcpy
import re

from arcgis.gis import GIS

import scripts.decorators as decorators

gis = GIS('pro')


@decorators.logger
def scrape_ids_from_description(item_id):
    """
    Scrape service IDs from service description
    :param item_id: id of AGOL item
    :return: string of ids separated by '|'
    """

    item = gis.content.get(item_id)
    pattern = r'\b\w{32}\b'

    if item.description is not None:
        agol_ids = '|'.join(set(filter(lambda x: x != item.id, re.findall(pattern, item.description))))

        if agol_ids:
            print(f"\tAGOL IDs found: {agol_ids}")
            return agol_ids


@decorators.logger
def remove_duplicates(feature, remove=False):
    fields = [f.name for f in arcpy.ListFields(feature) if f.name != 'OBJECTID']
    data = [row for row in arcpy.da.SearchCursor(feature, fields)]
    dups = len(data) - len(set(data))

    if dups > 0:
        print(f"\t{dups} duplicate rows found in {feature}")

        if remove:
            del_count = 0
            rows_processed = []

            with arcpy.da.UpdateCursor(feature, fields) as cursor:
                for row in cursor:
                    if row not in rows_processed:
                        rows_processed.append(row)
                    else:
                        cursor.deleteRow()
                        del_count += 1
            print(f"\tDeleted {del_count} records")
            del cursor
            return del_count

        else:
            return dups


@decorators.logger
def remove_all_rows(table):
    """
    Remove all rows from table
    :param table:
    :return: number of rows deleted
    """

    # GET row count, delete if > 0
    data = [row for row in arcpy.da.SearchCursor(table, "OBJECTID")]
    del_count = 0

    if len(data) > 0:
        with arcpy.da.UpdateCursor(table, "OBJECTID") as cur:
            for row in cur:
                cur.deleteRow()
                del_count += 1

        print(f"\tDeleted {del_count} records")
        del cur

    return del_count
