'''Classes used to implement Dijkstra's algorithm.
Also includes the main class that stores the database.'''
#See below for details:
#https://en.wikipedia.org/wiki/Dijkstra's_algorithm
#It can find the shortest path between two nodes on a directed network
#in O(n^2) time, so it's perfect for a database of components.
import json
import gzip
import os
from collections import defaultdict
try:
    from transcode import process_RLE, process_synth, compilesynth
except ImportError:
    from .transcode import process_RLE, process_synth, compilesynth   
def bignum():
    '''Used by defaultdict.'''
    return 99999999
ISOSJKDIR = os.path.dirname(__file__)
class DijkstraNode:
    '''A node used for Dijkstra's algorithm.'''
    def __init__(self, apgcode):
        self.apgcode = apgcode
        #self.sources stores the nodes with connections feeding in:
        self.sources = {}
        #self.sinks stores the nodes with connections going out from the node:
        self.sinks = {}
        #Used when Dijkstra's algorithm is run.
        self.distance = 0
        self.path = []
    def __hash__(self):
        return hash(self.apgcode)
    def __eq__(self, other):
        if isinstance(other, DijkstraNode):
            return hash(self) == hash(other)
        return False
    def __repr__(self):
        return 'DijkstraNode(apgcode=\"'+self.apgcode+'\", hash=' + str(hash(self))+ ')'
    def connect(self, other, distance):
        '''Adds a connection from the node to another node.'''
        if self == other:
            #For obvious reasons, connecting a node to itself is pointless:
            return None
        if other in self.sinks:
            self.sinks[other] = min(distance, self.sinks[other])
        else:
            self.sinks[other] = distance
        if self in other.sources:
            other.sources[self] = min(distance, other.sources[self])
        else:
            other.sources[self] = distance
        return None
class DijkstraNetwork:
    '''A class representing a directed network on which to run Dijkstra's algorithm.'''
    def __init__(self, file=None):
        #Dictionary storing nodes.
        self.nodes = defaultdict(dict)
        #Giant messed up dictionary that stores enough data to reconstruct the network from JSON:
        self.data = {}
        if file:
            self.load_network(file)
    def addnode(self, other, key):
        '''Adds a node to the network.'''
        self.nodes[key][other.apgcode] = other
    def addsynth(self, src, dst, cost, ship, ships, rule):
        '''Adds a synthesis to the network.'''
        if rule not in self.data:
            self.data[rule] = {}
        if ship not in self.data[rule]:
            self.data[rule][ship] = {}
        #datalist = [ships, cost]
        #Check that the cost is <= the best current cost:
        key = src + ',' + dst
        bestcost = 9999999999999999
        if key in self.data[rule][ship]:
            bestcost = min(len(self.data[rule][ship][key]), bestcost)
        if cost < bestcost:
            self.data[rule][ship][key] = ships
    def addcon(self, connection, rule, ship):
        '''Adds nodes to the network based on a tuple (src_apgcode, dst_apgcode, cost).'''
        src = connection[0]
        key = rule + ',' + ship
        if key not in self.nodes:
            self.nodes[key] = {}
        if src not in self.nodes[key]:
            node = DijkstraNode(src)
            self.addnode(node, key)
        dst = connection[1]
        if dst not in self.nodes[key]:
            node = DijkstraNode(dst)
            self.addnode(node, key)
        self.nodes[key][src].connect(self.nodes[key][dst], connection[2])
    def _minunvisited(self, distances, visited):
        '''Finds the closest unvisited node to the source node.'''
        minnode = None
        mindistance = 999999999
        for x in distances:
            if x not in visited:
                if distances[x] < mindistance:
                    mindistance = distances[x]
                    minnode = x
        return minnode
    def _applydistances(self, node, distances):
        '''Updates the distances given a node.'''
        for x in node.sinks:
            distance = node.sinks[x] + distances[node]
            if distance < distances[x]:
                distances[x] = distance
                x.path = node.path + [x.apgcode]
        return distances
    def traverse(self, src, dst, ship, rule):
        '''Attempts to find a path between the source node and destination node.'''
        #This is what actually implements Dijkstra's algorithm.
        key = rule + ',' + ship
        if isinstance(src, str):
            src = self.nodes[key][src]
        if isinstance(dst, str):
            dst = self.nodes[key][dst]
        #We only want to be using necessary nodes here:
        usednodes = [dst]
        length = 0
        while length != len(usednodes):
            length = len(usednodes)
            for x in usednodes:
                for y in x.sources:
                    if y not in usednodes:
                        usednodes.append(y)
        #If no path is detected, quit:
        if src not in usednodes:
            return ([], -1)
        #Find a path from the source node to the destination node:
        distances = defaultdict(bignum)
        for x in usednodes:
            distances[x] = 99999999
        distances[src] = 0
        visited = []
        src.path = [src.apgcode]
        while len(visited) < len(usednodes):
            node = self._minunvisited(distances, visited)
            visited.append(node)
            distances = self._applydistances(node, distances)
        #Return the apgcode path and the cost:
        return (dst.path, distances[dst])
    def dump(self, file=ISOSJKDIR + '/network.json.gz'):
        '''Dumps the network data as gzipped JSON.'''
        data = json.dumps(self.data)
        data = data.replace(' ', '')
        zipdata = gzip.compress(data.encode('utf-8'))
        with open(file, 'wb') as f:
            return f.write(zipdata)
    def load_network(self, file=ISOSJKDIR + '/network.json.gz'):
        '''Extracts data from a file and reconstructs a network.'''
        with open(file, 'rb') as f:
            data = f.read()
        #Decompress file if it is gzipped:
        if data[0:2] == b'\x1f\x8b':
            data = gzip.decompress(data)
        networkdata = json.loads(data)
        self.data = networkdata
        self.nodes = defaultdict(dict)
        for rule in networkdata:
            for ship in networkdata[rule]:
                for key in networkdata[rule][ship]:
                    src, dst = key.split(',')
                    connection = (src, dst, len(networkdata[rule][ship][key]))
                    self.addcon(connection, rule, ship)
    def process_synth(self, pt, ship):
        '''Processes a synthesis component, returning a status code.
0 = Success
1 = Malformed synthesis
2 = Aperiodic
3 = Non-rewindable'''
        return process_synth(pt, ship, self)
    def process_RLE(self, rle):
        '''Processes an RLE submitted via an HTML text box.
    Returns a tuple in form (binary message, HTTP code).'''
        return process_RLE(rle, self)
    def assemblesynth(self, apgcode, ship, rule):
        '''Compiles the given synthesis as a pattern.
Returns a tuple (pattern, cost).
Will throw an error if no path is found.'''
        return compilesynth(self, apgcode, ship, rule)
    def getsynthRLE(self, apgcode, ship, rule):
        '''Returns the RLE for a synthesis.'''
        pt, cost = self.assemblesynth(apgcode, ship, rule)
        rle = pt.rle_string()
        rle = rle[rle.find('\n') + 1:]
        header = '''#C [[ GRID MAXGRIDSIZE 14 THEME Catagolue ]]
#CSYNTH '''
        header += apgcode + ' costs ' + str(cost) + ' copies of ' + ship + '\n'
        return header + rle
        
