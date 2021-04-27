from itertools import combinations, product
from copy import deepcopy
import matplotlib.pyplot as plt


def parse_file(path):
    with open(path) as f:
        _, num_of_vehicles, capacity = map(lambda x: int(x.strip()), f.readline().split())
        customers = []
        for line in f.readlines():
            values = list(map(lambda x: int(x.strip()), line.split()))
            customers.append({'id': values[0], 'x': values[1], 'y': values[2], 'demand': values[3],
                              'ready_time': values[4], 'due_time': values[5], 'service_time': values[6]})

        return {'num_of_vehicles': num_of_vehicles,
                'capacity': capacity,
                'customers': customers}


def total_func(paths, data, penalty, penalty_mult):
    total_res = 0
    weight = 0
    for path in range(len(paths)):
        for i in range(len(paths[path]) - 1):
            total_res += count_dist(paths[path][i], paths[path][i + 1], data['customers'])
            total_res += data['customers'][paths[path][i]]['service_time']
        tweight = count_weight(data, paths[path])
        if data['capacity'] < tweight:
            weight += tweight - data['capacity']
    total_res += (penalty + weight) * penalty_mult
    return total_res


def count_dist(a, b, customers):
    return ((customers[a]['x'] - customers[b]['x']) ** 2 + (customers[a]['y'] - customers[b]['y']) ** 2) ** (1 / 2)


def find_closest(start, unvisited, capacity, time_counter, customers):
    closest = None
    min_dist = None
    for i in unvisited:
        dist = count_dist(start, i, customers)
        if (capacity >= customers[i]['demand'] and
                abs(customers[i]['ready_time'] - time_counter) < 200 and time_counter + dist <= customers[i][
                    'due_time']):
            if min_dist is None or dist < min_dist:
                min_dist = dist
                closest = i
    return closest, min_dist


def greedy(data):
    unvisited_customers = list(range(1, len(data['customers'])))
    capacities = [data['capacity'] for i in range(data['num_of_vehicles'])]
    time_counters = [0 for i in range(data['num_of_vehicles'])]
    paths = [[0] for i in range(data['num_of_vehicles'])]
    while unvisited_customers:
        for i in range(data['num_of_vehicles']):
            if unvisited_customers:
                v, dist = find_closest(paths[i][-1], unvisited_customers, capacities[i], time_counters[i],
                                       data['customers'])
                if v is None:
                    continue
                paths[i].append(v)
                capacities[i] -= data['customers'][v]['demand']
                time_counters[i] += dist + data['customers'][v]['service_time']
                unvisited_customers.remove(v)
            else:
                break
    for p in paths:
        p.append(0)
    return paths


def count_penalty(data, paths):
    total_penalty = 0
    for path in paths:
        time_counter = data['customers'][0]['ready_time']
        for i in range(1, len(path)):
            time_counter += count_dist(path[i - 1], path[i], data['customers'])
            if time_counter < data['customers'][path[i]]['ready_time']:
                time_counter = data['customers'][path[i]]['ready_time'] + data['customers'][path[i]]['service_time']
            elif time_counter <= data['customers'][path[i]]['due_time']:
                time_counter += data['customers'][path[i]]['service_time']
            else:
                total_penalty += time_counter - data['customers'][path[i]]['due_time']
                time_counter += data['customers'][path[i]]['service_time']
    return total_penalty


def find_best_swap(data, paths, stm, penalty_mult):
    paths = deepcopy(paths)
    best_paths = None
    dist = None
    best_a = None
    best_b = None
    for path1, path2 in combinations(list(range(len(paths))), 2):
        for a, b in product(list(range(1, len(paths[path1]) - 1)), list(range(1, len(paths[path2]) - 1))):
            f = False
            for i in stm:
                if paths[path1][a] in i or paths[path2][b] in i:
                    f = True
                    break
            if f:
                continue
            tmp_paths = deepcopy(paths)
            tmp_paths[path1][a] = paths[path2][b]
            tmp_paths[path2][b] = paths[path1][a]
            # if count_weight(data, tmp_paths[path1]) > data['capacity'] or count_weight(data, tmp_paths[path2]) > data['capacity']:
            #     continue
            tdist = total_func(tmp_paths, data, count_penalty(data, tmp_paths), penalty_mult)
            if best_paths is None or tdist < dist:
                best_paths = tmp_paths.copy()
                dist = tdist
                best_a, best_b = tmp_paths[path1][a], tmp_paths[path2][b]
    return best_paths, (best_a, best_b)


def find_best_insert(data, paths, stm, penalty_mult):
    paths = deepcopy(paths)
    best_paths = None
    dist = None
    best_point = None
    for path_i in range(len(paths)):
        for point_i in range(1, len(paths[path_i]) - 1):
            tmp_paths = deepcopy(paths)
            tmp_point = tmp_paths[path_i].pop(point_i)
            # print(tmp_paths)
            if tmp_point in stm:
                continue
            for path_j in range(len(tmp_paths)):
                for insert_j in range(1, len(tmp_paths[path_j])):
                    if path_j == path_i and point_i == insert_j:
                        continue
                    tmp_paths2 = deepcopy(tmp_paths)
                    tmp_paths2[path_j].insert(insert_j, tmp_point)
                    tdist = total_func(tmp_paths2, data, count_penalty(data, tmp_paths2), penalty_mult)
                    if best_paths is None or tdist < dist:
                        best_paths = deepcopy(tmp_paths2)
                        dist = tdist
                        best_point = tmp_point
    return best_paths, best_point


def count_weight(data, path):
    weight_counter = 0
    for i in path:
        weight_counter += data['customers'][i]['demand']
    return weight_counter


def tabu_search(data, stm_length=10):
    paths = greedy(data)
    stm = [[] for i in range(stm_length)]
    penalty_multiplier = 2
    best_paths = deepcopy(paths)
    best_dist = total_func(best_paths, data, 0, 0)
    print("best", best_dist, best_paths)
    tmp_paths = deepcopy(paths)
    while True:
        stm = stm[1:]
        stm.append([])
        tmp_paths, swap_attributes = find_best_swap(data, tmp_paths, stm, penalty_multiplier)
        stm[-1].extend(list(swap_attributes))
        tmp_penalty = count_penalty(data, tmp_paths)
        tmp_dist = total_func(tmp_paths, data, tmp_penalty, penalty_multiplier)
        draw_vrp(data, tmp_paths)
        if tmp_dist < best_dist and tmp_penalty == 0:
            best_paths = tmp_paths
            best_dist = tmp_dist
            print("best", best_dist, best_paths)
        elif tmp_penalty > 0:
            print(tmp_dist, 'pen', tmp_paths)
        else:
            print(tmp_dist, tmp_paths)
        if tmp_penalty > 0:
            penalty_multiplier = penalty_multiplier * 2
        else:
            penalty_multiplier = 2


def tabu_search_2(data, stm_length=20, const_pen_mult=0.25):
    paths = greedy(data)
    stm = [None for i in range(stm_length)]
    penalty_multiplier = const_pen_mult
    best_paths = deepcopy(paths)
    best_dist = total_func(best_paths, data, 0, 0)
    print("best", best_dist, best_paths)
    tmp_paths = deepcopy(paths)
    while True:
        stm = stm[1:]
        tmp_paths, best_point = find_best_insert(data, tmp_paths, stm, penalty_multiplier)
        stm.append(best_point)
        tmp_penalty = count_penalty(data, tmp_paths)
        tmp_dist = total_func(tmp_paths, data, tmp_penalty, penalty_multiplier)

        draw_vrp(data, tmp_paths)

        if tmp_dist < best_dist and tmp_penalty == 0:
            best_paths = tmp_paths
            best_dist = tmp_dist
            print("best", best_dist, best_paths)
        elif tmp_penalty > 0:
            print(tmp_dist, 'pen', tmp_paths)
        else:
            print(tmp_dist, tmp_paths)
        if tmp_penalty > 0:
            penalty_multiplier = penalty_multiplier * 2
        else:
            penalty_multiplier = const_pen_mult


def draw_vrp(data, tmp_paths):
    list_for_draw = []
    for path_i in tmp_paths:
        x1 = []
        y1 = []
        for path_j in path_i:
            x1.append(data['customers'][path_j]['x'])
            y1.append(data['customers'][path_j]['y'])
        list_for_draw.append(x1)
        list_for_draw.append(y1)
    for z in range(0, len(list_for_draw), 2):
        plt.plot(list_for_draw[z], list_for_draw[z + 1])
    plt.show()


data = parse_file('I1.txt')
# print(data['customers'][0]['due_time'])
# tabu_search(data)

tabu_search_2(data, const_pen_mult=1.1)
