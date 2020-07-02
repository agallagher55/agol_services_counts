"""
MODE SHARE APP
return: urls, layer names, map names
"""

from arcgis.gis import GIS
from arcgis.mapping import WebMap
import pprint
import os
import csv

gis = GIS('pro')

mode_share_app_id = '595b4bf77e9d42e3af401da5e5f724c7'
app_main = gis.content.get(mode_share_app_id)


# 1) Get all apps within main app
mode_share_sources = [
    {'app': 'Base',
    'appid': '97fc75ddc204d48bb9e47fdaa17a8e8b6',
    'mapid': '5af6050417f24ba1a161d2a7769a55c1',
     'map': None,
     'layer_names': [],
     'layer_urls': []},
    {'app': 'Walking',
    'appid': '9e46cf5f1b5e4eb3ae4e8c66267366ea',
    'mapid': '72e8cc6e4f324a4a83456624474e41f3',
     'map': None,
     'layer_names': [],
     'layer_urls': []},
    {'app': 'Passengers',
    'appid': '786572992718405faf9647df67af415a',
    'mapid': '8f0d2acb33ae4b8cabb149a5325a3c28',
     'map': None,
     'layer_names': [],
     'layer_urls': []},
    {'app': 'Drivers',
    'appid': '56ff4e4f08644004b8e7978051320a90',
    'mapid': '4dbe33aa38f34938928b33c1bc031761',
     'map': None,
     'layer_names': [],
     'layer_urls': []},
    {'app': 'Transit',
    'appid': '18071c8ea0d24749a726126d8accf7d1',
    'mapid': 'e84ab594feda493e85b8d2a256f9aaae',
     'map': None,
     'layer_names': [],
     'layer_urls': []},
    {'app': 'Bicycling',
    'appid': '2568a7ac95b744fa8c43aff13c0ac427',
    'mapid': 'ba7277ba059a41939a1c2d09973741d2',
     'map': None,
     'layer_names': [],
     'layer_urls': []},
]

# 2) Get name of map in each app
map_ids = [x['mapid'] for x in mode_share_sources]
map_items = [gis.content.get(item['mapid']) for item in mode_share_sources]
map_titles = [x['title'] for x in map_items]
print(map_titles)

# 3) Get name and url of each layer in each map
for mapid in map_ids:
    web_map = WebMap(gis.content.get(mapid))
    print(web_map.item.title)

    layers = web_map.layers
    layer_data = [{x.title: x.url} for x in layers]
    layer_names = [x['title'] for x in layers]
    layer_urls = [x['url'] for x in layers]

    for obj in mode_share_sources:
        if obj['mapid'] == mapid:
            obj['map'] = web_map.item.title
            obj['layer_data'] = layer_data

pprint.pprint(mode_share_sources)

# 4) Export to csv
excel_file = os.path.join(os.path.dirname(os.path.realpath(__file__)))

for obj in mode_share_sources:
    excel_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), f"{obj['app']}.csv")
    with open(excel_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['APP', 'APP_ID', 'MAP', 'LAYERS', 'URLS'])

        writer.writerow([obj['app'], obj['appid'], obj['map']])
        for data in obj['layer_data']:
            writer.writerow(['', '', '', list(data.keys())[0], list(data.values())[0]])


