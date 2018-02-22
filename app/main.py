import random

import bottle
import os
from pypaths import astar


DIRECTION_MAP = {
    (0, -1): 'up',
    (0, 1): 'down',
    (-1, 0): 'left',
    (1, 0): 'right'
}

ZOMBIE_NAME = 'ZOMBIE'
ZOMBIE_TAUNT = 'BRAAAAIIINS'


@bottle.route('/')
def static():
    return "the server is running"


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        'color': '#CCCCCC',
        'taunt': ZOMBIE_TAUNT,
        'head_url': head_url,
        'name': 'battlesnake-python'
    }


def get_valid_neighbours(coord, data):
    snake_coords = [(point['x'], point['y']) for snake in data['snakes']['data'] for point in snake['body']['data']]
    friendly_snake_heads = [point_to_coord(friend['body']['data'][0]) for friend in data['snakes']['data'] if ZOMBIE_NAME in friend['name'].upper() and friend['id'] != data['you']['id']]
    friendly_head_neighbors = [add_coords(head, dir_coord) for dir_coord in DIRECTION_MAP.keys() for head in friendly_snake_heads]
    all_neighbors = [add_coords(coord, dir_coord) for dir_coord in DIRECTION_MAP.keys()]

    valid_neighbours = [
        coord for coord in all_neighbors
        if 0 <= coord[0] < data['width']
           and 0 <= coord[1] < data['height']
           and coord not in snake_coords
           and coord not in friendly_head_neighbors  # TODO: Could remove this, if they're too hard
    ]

    return valid_neighbours


def add_coords(coord_one, coord_two):
    return tuple(map(lambda x, y: x + y, coord_one, coord_two))


def sub_coords(coord_one, coord_two):
    return tuple(map(lambda x, y: x - y, coord_one, coord_two))


def point_to_coord(point):
    return point['x'], point['y']


def get_paths_to_coords(finder, head_coords, target_coords):
    return [path for path in [finder(head_coords, coord) for coord in target_coords] if path[0]]


def get_paths_to_points(finder, head_coords, target_points):
    return get_paths_to_coords(finder, head_coords, [point_to_coord(point) for point in target_points])


@bottle.post('/move')
def move():
    data = bottle.request.json

    def get_neighbors(node):
        return get_valid_neighbours(node, data)

    finder = astar.pathfinder(neighbors=get_neighbors)

    you_coords = [point_to_coord(point) for point in data['you']['body']['data']]

    head_coords = you_coords[0]

    # Zombies only eat brains!
    enemy_snake_heads = [point_to_coord(snake['body']['data'][0]) for snake in data['snakes']['data'] if ZOMBIE_NAME not in snake['name'].upper()]
    enemy_head_neighbors = [add_coords(head, dir_coord) for dir_coord in DIRECTION_MAP.keys() for head in enemy_snake_heads]
    paths = get_paths_to_coords(finder, head_coords, enemy_head_neighbors)

    # TODO: Could add looping of no path to enemy head

    print 'Targets: %s' % enemy_head_neighbors

    if not paths:
        raise Exception

    path = min(paths, key=lambda x: x[0])

    next_coords = path[1][1]

    print 'Next move: %s' % str(next_coords)

    coord_delta = sub_coords(next_coords, head_coords)

    direction = DIRECTION_MAP[coord_delta]

    print direction
    return {
        'move': direction,
        'taunt': ZOMBIE_TAUNT
    }


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '192.168.0.19'),
        port=os.getenv('PORT', '8080'),
        debug = True)
