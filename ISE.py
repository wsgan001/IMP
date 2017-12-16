import numpy as np
import os
import time
import argparse

graph = None


def read_seed_info(path):
    if os.path.exists(path):
        try:
            f = open(path, 'r')
            txt = f.readlines()
            seeds = list()
            for line in txt:
                seeds.append(int(line))
            return seeds
        except IOError:
            print
            'IOError'
    else:
        print
        'file can not found'


# read and analyse the data in the file to obtain a graph object
def read_graph_info(path):
    if os.path.exists(path):
        parents = {}
        children = {}
        edges = {}
        nodes = set()

        try:
            f = open(path, 'r')
            txt = f.readlines()
            header = str.split(txt[0])
            node_num = int(header[0])
            edge_num = int(header[1])

            for line in txt[1:]:
                row = str.split(line)

                src = int(row[0])
                des = int(row[1])
                nodes.add(src)
                nodes.add(des)

                if children.get(src) is None:
                    children[src] = []
                if parents.get(des) is None:
                    parents[des] = []

                weight = float(row[2])
                edges[(src, des)] = weight
                children[src].append(des)
                parents[des].append(src)

            return list(nodes), edges, children, parents, node_num, edge_num
        except IOError:
            print 'IOError'
    else:
        print 'file can not found'


def happen_with_prop(rate):
    rand = np.random.ranf()
    if rand <= rate:
        return True
    else:
        return False


class Graph:
    nodes = None
    edges = None
    children = None
    parents = None
    node_num = None
    edge_num = None

    def __init__(self, (nodes, edges, children, parents, node_num, edge_num)):
        self.nodes = nodes
        self.edges = edges
        self.children = children
        self.parents = parents
        self.node_num = node_num
        self.edge_num = edge_num

    def get_children(self, node):
        ch = self.children.get(node)
        if ch is None:
            self.children[node] = []
        return self.children[node]

    def get_parents(self, node):
        pa = self.parents.get(node)
        if pa is None:
            self.parents[node] = []
        return self.parents[node]

    def get_weight(self, src, dest):
        weight = self.edges.get((src, dest))
        if weight is None:
            return 0
        else:
            return weight

    # return true if node1 is parent of node 2 , else return false
    def is_parent_of(self, node1, node2):
        if self.get_weight(node1, node2) != 0:
            return True
        else:
            return False

    # return true if node1 is child of node 2 , else return false
    def is_child_of(self, node1, node2):
        return self.is_parent_of(node2, node1)

    def get_out_degree(self, node):
        return len(self.get_children(node))

    def get_in_degree(self, node):
        return len(self.get_parents(node))

# graph : Graph
# seed : list
# sample_num : int
def influence_spread_computation_IC(graph, seeds, sample_num=10000):
    influence = 0
    for i in range(sample_num):
        activated = seeds
        new_activated = activated
        while len(new_activated) != 0:
            activated = new_activated
            new_activated = []
            for node in activated:
                node_children = graph.get_children(node)
                for j in range(graph.get_out_degree(node)):
                    if happen_with_prop(graph.get_weight(node, node_children[j])):
                        new_activated.append(node_children[j])
                        influence = influence + 1
    return int(influence / sample_num) + len(seeds)



def forward(Q, D, spd, pp, r, W, U, spdW_u):
    x = Q[-1]
    if U is None:
        U = []
    children = graph.get_children(x)
    count = 0
    while True:
        # any suitable chid is ok

        for child in range(count, len(children)):
            # if is_in_sub_node_set(children[child],W) and (not is_in_sub_node_set(children[child],q)) and (children[child] not in D[x]):
            if (children[child] in W) and (children[child] not in Q) and (children[child] not in D[x]):
                y = children[child]
                break
            count = count + 1

        # no such child:
        if count == len(children):
            return Q, D, spd, pp

        if pp * graph.get_weight(x, y) < r:
            D[x].append(y)
        else:
            Q.append(y)
            pp = pp * graph.get_weight(x, y)
            spd = spd + pp
            D[x].append(y)
            x = Q[-1]
            for v in U:
                if v not in Q:
                    spdW_u[v] = spdW_u[v] + pp
            children = graph.get_children(x)
            count = 0


def backtrack(u, r, W, U, spdW_):
    Q = [u]
    spd = 1
    pp = 1
    D = init_D()

    while len(Q) != 0:
        Q, D, spd, pp = forward(Q, D, spd, pp, r, W, U, spdW_)
        u = Q.pop()
        D[u] = []
        if len(Q) != 0:
            v = Q[-1]
            pp = pp / graph.get_weight(v, u)
    return spd


def simpath_spread(S, r, U, spdW_=None):
    spread = 0
    # W: V-S
    W = set(graph.nodes).difference(S)
    if U is None or spdW_ is None:
        spdW_ = np.zeros(graph.node_num + 1)
        # print 'U None'
    for u in S:
        W.add(u)
        # print spdW_[u]
        spread = spread + backtrack(u, r, W, U, spdW_[u])
        # print spdW_[u]
        W.remove(u)
    return spread


def influence_spread_computation_LT(seeds, r=0.01):
    return simpath_spread(seeds, r, None)


def init_D():
    D = list()
    for i in range(graph.node_num + 1):
        D.append([])
    return D


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', help='CARP instance file', dest='graph_path')
    parser.add_argument('-s', help='seed set', dest='seed_path')
    parser.add_argument('-m', help='diffusion model', dest='model')
    parser.add_argument('-b',
                        help='specifies the termination manner and the value can only be 0 or 1. If it is set to 0, '
                             'the termination condition is as the same defined in your algorithm. Otherwise, '
                             'the maximal time budget specifies the termination condition of your algorithm.',
                        dest='type')
    parser.add_argument('-t', type=int, help='termination', dest='timeout')
    parser.add_argument('-r', type=int, help='random seed', dest='random_seed')

    args = parser.parse_args()
    graph_path = args.graph_path
    seed_path = args.seed_path
    model = args.model
    type = args.type
    timeout = args.timeout
    random_seed = args.random_seed

    np.random.seed(random_seed)

    graph = Graph(read_graph_info(graph_path))
    seeds = read_seed_info(seed_path)

    if model == 'IC':
        print influence_spread_computation_IC(graph=graph, seeds=seeds, sample_num=10000)
    elif model == 'LT':
        print influence_spread_computation_LT(seeds=seeds)
    else:
        print('Type err')
