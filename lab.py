#!/usr/bin/env python3
from util import read_osm_data, great_circle_distance

# NO ADDITIONAL IMPORTS!


ALLOWED_HIGHWAY_TYPES = {
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
    'residential', 'living_street', 'motorway_link', 'trunk_link',
    'primary_link', 'secondary_link', 'tertiary_link',
}


DEFAULT_SPEED_LIMIT_MPH = {
    'motorway': 60,
    'trunk': 45,
    'primary': 35,
    'secondary': 30,
    'residential': 25,
    'tertiary': 25,
    'unclassified': 25,
    'living_street': 10,
    'motorway_link': 30,
    'trunk_link': 30,
    'primary_link': 30,
    'secondary_link': 30,
    'tertiary_link': 25,
}


def build_internal_representation(nodes_filename, ways_filename):
    """
    Create any internal representation you you want for the specified map, by
    reading the data from the given filenames (using read_osm_data)
    """
    '''Internal representation will be a large dictinoary with the ID numbers as the keys to each node/way
    i.e. {1234567: {'nodes:[], 'tags{}}}
    
    Assumptions to account for: we will only work with roadways'''
    node_data = {}
    #Add nodes to dataset
    for x in read_osm_data(nodes_filename):
        node_data[x['id']] = {'lat': x['lat'], 'lon': x['lon'], 'tags': x['tags'], 'children':[]}

    ways_data = {}
    #Add ways to ways_data and initialize children property to node_data
    for x in read_osm_data(ways_filename):
        #Only account for roadways
        if 'highway' in x['tags'] and x['tags']['highway'] in ALLOWED_HIGHWAY_TYPES:
            ways_data[x['id']] = {'nodes': x['nodes'], 'tags': x['tags']}

            #initialize the children property of node_data
            for y in range(len(x['nodes'])):
                #The only adjacent node on a one way road is y + 1 node
                if 'oneway' in x['tags'] and x['tags']['oneway'] == 'yes':
                    #Account for last iteration where y + 1 doesn't exist
                    if y + 1 < len(x['nodes']) and x['nodes'][y+1] not in node_data[x['nodes'][y]]['children']:
                        node_data[x['nodes'][y]]['children'].append(x['nodes'][y+1])
                else:
                    #Account for last iteration where y + 1 does not exist
                    if y + 1 < len(x['nodes']) and x['nodes'][y+1] not in node_data[x['nodes'][y]]['children']:
                        node_data[x['nodes'][y]]['children'].append(x['nodes'][y+1])
                    #Account for first iteration where index = 0 then there is no y - 1 just catch error and continue
                    if y - 1 >= 0 and x['nodes'][y-1] not in node_data[x['nodes'][y]]['children']:
                        node_data[x['nodes'][y]]['children'].append(x['nodes'][y-1])
                    

    return (node_data, ways_data)

def get_distance(node1, node2):
    #Gets great_cricle_distance between two nodes
    coord1 = (node1['lat'], node1['lon'])
    coord2 = (node2['lat'], node2['lon'])
    distance = great_circle_distance(coord1, coord2)
    return distance

def find_nearest_nodes(map_rep, loc, loc2):
    #Finds the nearest node given a coordinate location
    node_data = map_rep[0]
    ways_data = map_rep[1]
    #I want to check if a node is on a relevant highway which are the highways in ways_data so I'll make a list of those nodes
    relevant_nodes = []
    for way in ways_data:
        relevant_nodes = relevant_nodes + ways_data[way]['nodes']
    #I want to be able to check if a node is in the list quickly so I'll turn it into a set
    relevant_nodes = set(relevant_nodes)
    
    min_distance1 = 100000000000
    min_distance2 = 100000000000
    nearest_node1 = None
    nearest_node2 = None
    for node in node_data:
        #Check if node is in a relevant highway
        if node in relevant_nodes:
            coord = (node_data[node]['lat'], node_data[node]['lon'])
            distance1 = great_circle_distance(loc, coord)
            distance2 = great_circle_distance(loc2, coord)
            if distance1 < min_distance1:
                min_distance1 = distance1
                nearest_node1 = node
            if distance2 < min_distance2:
                min_distance2 = distance2
                nearest_node2 = node
    return (nearest_node1, nearest_node2)

def find_short_path_nodes(map_rep, node1, node2):
    """
    Return the shortest path between the two nodes

    Parameters:
        map_rep: the result of calling build_internal_representation
        node1: node representing the start location
        node2: node representing the end location

    Returns:
        a list of node IDs representing the shortest path (in terms of
        distance) from node1 to node2
    """
    #Initialize relevant map_rep data
    node_data = map_rep[0]
    #Initizlize agenda. Paths will have the form of ([nodes], cost)
    agenda = [([node1], 0)]
    #Initialize empty expanded set
    expanded_set = set()

    #Repeat until agenda is empty
    while len(agenda) != 0:
        lowest_cost_path = agenda.pop(0)
        termial_vertex = lowest_cost_path[0][-1]
        #If this path's terminal vertex is the expanded set, ignore it and move on to the next path
        if termial_vertex in expanded_set:
            continue
        #If this path's termnial vertex satisfies the goal condition, return that path
        elif termial_vertex == node2:
            return lowest_cost_path[0]
        #Otherwise add its terminal vertex to expanded set
        else:
            expanded_set.add(termial_vertex)

        #For each of the children nodes of the terminal vertex, if it's in expanded set skip it, otherwise add associated path and cost to agenda
        children_nodes = node_data[termial_vertex]['children']
        for node in children_nodes:
            if node in expanded_set:
                continue
            else:
                agenda.append((lowest_cost_path[0] + [node], lowest_cost_path[1] + get_distance(node_data[termial_vertex], node_data[node])))
        #Sort the agenda so the lowest cost path is always first in the agenda
        agenda.sort(key=lambda x: x[1])

    #If search failed return nothing
    return None


def find_short_path(map_rep, loc1, loc2):
    """
    Return the shortest path between the two locations

    Parameters:
        map_rep: the result of calling build_internal_representation
        loc1: tuple of 2 floats: (latitude, longitude), representing the start
              location
        loc2: tuple of 2 floats: (latitude, longitude), representing the end
              location

    Returns:
        a list of (latitude, longitude) tuples representing the shortest path
        (in terms of distance) from loc1 to loc2.
    """
    node_data = map_rep[0]
    #We want to get the two nodes that are nearest to loc1 and loc2
    node1, node2 = find_nearest_nodes(map_rep, loc1, loc2)
    
    #Let's get the shortest path of nodes between these two nodes
    short_path_nodes = find_short_path_nodes(map_rep, node1, node2)

    #initilize location list
    loc_list = []
    #Add tuple (lat, lon) locations of short_path_nodes
    for node in short_path_nodes:
       loc_list.append((node_data[node]['lat'], node_data[node]['lon']))
    return loc_list

if __name__ == '__main__':
    # additional code here will be run only when lab.py is invoked directly
    # (not when imported from test.py), so this is a good place to put code
    # used, for example, to generate the results for the online questions.
    #data = build_internal_representation('resources/mit.nodes', 'resources/mit.ways')
    #print(find_short_path_nodes(data, 2, 8))
    #data = build_internal_representation('resources/midwest.nodes', 'resources/midwest.ways')
    #print(data[0])
    #print(find_short_path(data, (42.3575, -71.0952), (42.355, -71.1009)))
    pass