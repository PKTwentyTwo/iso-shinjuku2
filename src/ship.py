'''Functions which handle extraction of arbitrary spaceships.'''
try:
    from treeman import getlifetree
except ImportError:
    from .treeman import getlifetree
def permute(pt):
    '''Returns a dictionary containing all orientations and phases of a pattern.'''
    orientations = ('identity','rot90','rot180','rot270','flip_x','flip_y','swap_xy','swap_xy_flip')
    period = pt.period
    output = {}
    digests = set()
    for x in orientations:
        for y in range(period):
            pt2 = pt[y](x)
            digest = pt2.digest()
            if digest not in digests:
                digests.add(digest)
                output[(x, y)] = pt2
    return output
def getperiod(apgcode):
    '''Returns the period based on an apgcode.'''
    if not apgcode.startswith('xq'):
        raise ValueError('Error: apgcode {apgcode} does not represent a spaceship.')
    try:
        period = int(apgcode[2:apgcode.find('_')])
        assert period > 0
    except:
        raise ValueError('Incorrectly formed apgcode: {apgcode}')
    return period
class Spaceship:
    '''Class representing a singular spaceship.'''
    def __init__(self, apgcode, orientation, phase, translation, rule):
        self.apgcode = apgcode
        self.orientation = orientation
        self.translation = translation
        self.phase = phase
        self.rule = rule
        #self.period = getperiod(apgcode)
    def gettuple(self):
        '''Return a tuple representing the object.'''
        objtuple = (self.apgcode, self.orientation, self.phase, self.translation, self.rule)
        return objtuple
    def __repr__(self):
        string = 'Spaceship'+str(self.gettuple()).replace('(', '<').replace(')', '>')
        return string
    def pt(self):
        '''Return a lifelib Pattern representing the object.'''
        lifetree = getlifetree(self.rule)
        pattern = lifetree.pattern(self.apgcode)
        pattern = pattern[self.phase](self.orientation)
        pattern = pattern(self.translation[0], self.translation[1])
        return pattern
def miniextract(pt, ship, permutations):
    '''Extracts a list of class Spaceship from a salvo.'''
    ships = []
    for x in permutations:
        shipor = permutations[x]
        #Needed to ensure the ship is disconnected
        #(found while doing testing with Travelling Ts):
        deadcells = shipor.convolve(pt.owner.pattern('3o$3o$3o')(-1, -1)) - shipor
        cells = pt.match(shipor, dead=deadcells).coords().tolist()
        for c in cells:
            shipclass = Spaceship(ship.apgcode, x[0], x[1], tuple(c), pt.getrule())
            ships.append(shipclass)
    return ships
def extract(pt, ship):
    '''Extracts a list of class Spaceship from a pattern.'''
    res = []
    outlist = []
    ships = permute(ship)
    shiplist = [ships[x] for x in ships]
    for block in zip(*[iter(shiplist)]):
        salvo = sum((pt.match(g, halo='3o$3o$3o').convolve(g) for g in block),start=pt.owner.pattern())
        #Below part is apparently necessary. Don't touch it.
        mask = pt.owner.pattern()
        res.append(salvo - mask)
    for x in res:
        outlist += miniextract(x, ship, ships)
    return outlist
