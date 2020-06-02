def get_app_data(my_items=False, owner='**', title='', access='', max_items=999):
    print(f"Running {get_app_data.__name__} function...")

    if my_items is True:
        owner = gis.users.me.username

    access_types = ['private', 'shared', 'public']
    if access not in access_types and len(access) > 0:
        raise Exception(f"{access} is not recognized as a valid access type -> {', '.join(access_types)}")

    query = f'owner:{owner} AND NOT owner:esri AND title:{title}* AND access:{access}*'

    # Filter maps by title, creator, access
    item_objs = gis.content.search(query=query, item_type='Web Mapping Application', max_items=max_items, outside_org=False)
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
