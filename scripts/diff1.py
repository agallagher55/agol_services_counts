def get_layer_data(my_items=False, owner='**', title='', access='', max_items=999, item_type='LAYER'):
    """
    :param my_items: Get data belonging to current user
    :param owner: Owner account
    :param title:
    :param access: ['private', 'shared', 'public']
    :param max_items:
    :param item_type: MAP, APP
    :return: list of map objects - [{}, {}, {},...] title, type, id, created date, access attributes
    Filter maps by created date, modified date, creator, access
    """

    print(f"Running {get_layer_data.__name__} function...")
    valid_item_types = {
        'MAP': 'Web Map', 'APP': 'Web Mapping Application',
        'LAYER': 'Feature Service', 'COLLECTION': 'Feature Collection'
    }

    assert item_type.upper() in valid_item_types.keys()
    if my_items is True:
        owner = gis.users.me.username

    access_types = ['private', 'shared', 'public']
    if access not in access_types and len(access) > 0:
        raise Exception(f"{access} is not recognized as a valid access type -> {', '.join(access_types)}")

    query = f'owner:{owner} AND NOT owner:esri AND title:{title}* AND access:{access}*'

    # Filter maps by title, creator, access
    item_objs = gis.content.search(query=query, item_type=valid_item_types[item_type.upper()],
                                   max_items=max_items, outside_org=False)
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
            'type': obj.type,
            'url': obj.url,
            'description_ids': agol_ids
        }

        if data_obj not in data_objs:
            data_objs.append(data_obj)

    return data_objs

