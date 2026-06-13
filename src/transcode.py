'''Main functions for committing syntheses.'''
import sys
from lifelib.genera import obtain_genus, sanirule
try:
    from ship import extract, Spaceship, getlifetree
except ImportError:
    from .ship import extract, Spaceship, getlifetree

def oscar(pt):
    '''Gets the period of a pattern (0 if aperiodic).'''
    try:
        period = pt.period
    except KeyError:
        period = 0
    return period
def removeships(pt, shipset):
    '''Removes all spaceships from a pattern.'''
    pt2 = pt.owner.pattern() + pt
    for x in shipset:
        pt2 -= x.pt()
    return pt2
def split_mosaic(mosaic, ship, radius=17, assume_rows=False, maxtime=1024):
    env = mosaic.owner.pattern() + mosaic
    for x in range(2, 16, 2):
        env += mosaic[x]
    for i in range(16, 64, 4):
        env += mosaic[i]
    for i in range(64, maxtime, 8):
        env += mosaic[i]
    if assume_rows:
        comps = env.components(halo='125o$125o$125o$125o$125o!')
        comps = [(c & mosaic) for c in comps]
        synthparts = [split_mosaic(c, ship, radius=radius) for c in comps]
        return [x for y in synthparts for x in y]
    diameter = radius * 2 + 1
    halo = mosaic.owner.pattern(f'{diameter}o$' * diameter).centre()
    comps = env.components(halo=halo)
    comps = [c & mosaic for c in comps]
    comps = [c for c in comps if c.population > 5]
    return comps
def rewind(pt, ship, gens):
    '''Rewinds a synthesis a given number of generations.
Assumes that the pattern is periodic.'''
    ships = extract(pt, ship)
    basept = removeships(pt, ships)
    rewound = pt.owner.pattern()
    for x in ships:
        rewound += x.pt()[-gens]
    basept = basept[-gens]
    return basept + rewound
def advancesynth(pt, ship, period):
    '''Advances a synthesis using a binary search.'''
    gen = 1
    shipcount = len(extract(pt, ship))
    dobreak = False
    while not dobreak:
        gen *= 2
        dobreak = len(extract(pt[gen], ship)) != shipcount
        if gen >= 10000:
            return pt.owner.pattern()
    diff = gen
    dobreak = True
    while diff > 1:
        diff = diff//2
        if dobreak:
            gen -= diff
        else:
            gen += diff
        dobreak = len(extract(pt[gen], ship)) != shipcount
    if dobreak:
        gen -= 1
    gen -= 2
    if gen < 0:
        gen = 0
    gen = period * (gen // period)
    return pt[gen]
def canonisesynth(pt, ship):
    '''Canonises a synthesis.'''
    initpt = removeships(pt, extract(pt, ship))
    pt2 = initpt
    period = initpt.period
    targetpt = pt.owner.pattern(pt2.apgcode)
    loops = 0
    while pt2.octodigest() != targetpt.octodigest():
        pt2 = pt2[1]
        loops += 1
        if loops > period+1:
            sys.stderr.write('Phase matching loops exceeded!\n')
            return pt.owner.pattern()
    gens = loops - period
    orientations = ['identity', 'rot90', 'rot180', 'rot270', 'flip_x', 'flip_y', 'swap_xy', 'swap_xy_flip', 'transpose']
    loops = 0
    pt3 = pt2
    orientation = 'identity'
    while pt2.digest() != targetpt.digest():
        orientation = orientations[loops]
        pt2 = pt3(orientation)
        loops += 1
        if loops > 8:
            sys.stderr.write('Orientation matching loops exceeded!\n'+pt2.apgcode+'\n')
            break
    transpt = initpt[gens](orientation)
    delta = (targetpt.firstcell[0] - transpt.firstcell[0], targetpt.firstcell[1] - transpt.firstcell[1])
    canonpt = rewind(pt, ship, period - gens)(orientation)(delta[0], delta[1])
    return advancesynth(canonpt, ship, period)
def process_synth(pt, ship, nw):
    '''Processes a synthesis component, returning a status code.
0 = Success
1 = Malformed synthesis
2 = Aperiodic
3 = Non-rewindable'''
    rule = pt.owner.session.rules[0]
    if isinstance(ship, str):
        ship = pt.owner.pattern(ship)
    #Get the copies of the ship:
    ships = extract(pt, ship)
    if len(ships) == 0:
        #sys.stderr.write('Error: no copies of the ship are present.\n')
        return 1
    #Check that the eventual pattern is periodic:
    evpt = pt[4096]
    period = oscar(evpt)
    if not period:
        #sys.stderr.write('Error: resulting pattern is aperiodic.\n')
        return 2
    try:
        pt.period
        return 1
    except KeyError:
        pass
    #Check that the initial pattern is periodic:
    initpt = removeships(pt, ships)
    if not oscar(initpt[4096]):
        #sys.stderr.write('Error: initial pattern is aperiodic.\n')
        return 2
    #Check rewindability:
    try:
        if rewind(pt, ship, 4096)[4096] != pt:
            return 3
    #The base pattern can of course be aperiodic, so we need to check for that:
    except KeyError:
        return 2
    canonpt = canonisesynth(pt, ship)
    #canonpt = rewind(canonpt, ship, max(4, period))
    initapgcode = initpt.apgcode
    evapgcode = evpt.apgcode
    cost = len(ships)
    shiplist = [x.gettuple()[1:-1] for x in extract(canonpt, ship)]
    if len(shiplist) == 0:
        return 1
    nw.addcon((initapgcode, evapgcode, cost), rule, ship.apgcode)
    nw.addsynth(initapgcode, evapgcode, cost, ship.apgcode, shiplist, rule)
    return 0
def process_RLE(rle, nw):
    '''Processes an RLE submitted via an HTML text box.
Returns a tuple in form (binary message, HTTP code).'''
    #Check that it fits constraints:
    if len(rle) > 400000:
        return (b'Error: Submitted RLEs must be <100 KB.', 400)
    splitrle = rle.split('\n')
    if len(splitrle) < 3:
        return (b'Malformed RLE: Less than three distinct lines were detected.', 400)
    comment, header, rle = splitrle[0], splitrle[1], ''.join([(lambda x : (x).replace(' ', ''))(x) for x in splitrle[2:]])
    #More validity checks:
    if not comment.startswith('#C '):
        return (b'Malformed RLE: You must provide a comment specifying the ship, e.g \"#C xq4_153\"', 400)
    header = header.replace(' ', '')
    if 'rule=' not in header:
        return (b'Malformed RLE: A header is required on the second line, e.g \"x = 0, y = 0, rule = B3/S23\n"', 400)
    rule = header[header.find('rule=')+5:]
    rule = sanirule(rule)
    if obtain_genus(rule) not in ['lifelike', 'b3s23life', 'isotropic']:
        return (b'Malformed RLE: Rule '+rule.encode('utf-8')+b' is not of a supported genus.', 400)
    #Checking the spaceship apgcode:
    lt = getlifetree(rule)
    apgcode = comment.split(' ')[1]
    if not apgcode.startswith('xq'):
        return (b'Malformed RLE: apgcode is not a spaceship.', 400)
    try:
        shippt = lt.pattern(apgcode)
    except ValueError:
        return (b'Malformed RLE: spaceship apgcode is not valid in the specified rule.', 400)
    pt = lt.pattern(rle)
    if pt.population > 100000:
        return (b'Error: Syntheses cannot exceed 100000 live cells.', 400)
    if pt.empty():
        return (b'Error: Synthesis is empty.')
    if max(pt.bounding_box[2:]) > 9999:
        return (b'Error: Syntheses cannot exceed a 9999x9999 bounding box.', 400)
    for x in split_mosaic(lt.pattern(rle), shippt, radius=20):
        process_synth(x, lt.pattern(apgcode), nw)
    return (b'RLE successfully submitted for processing.', 200)
def compilesynth(nw, apgcode, ship, rule):
    '''Compiles a synthesis as a pattern.
Returns a tuple (pattern, cost)'''
    lt = getlifetree(rule)
    traversal = nw.traverse('xs0_0', apgcode, ship, rule)
    print(traversal)
    if not traversal[0]:
        return lt.pattern()
    pt = lt.pattern()
    for n in range(len(traversal[0])-1):
        src = traversal[0][n]
        dst = traversal[0][n+1]
        shiplist = nw.data[rule][ship][src + ',' + dst]
        newcomp = lt.pattern(src)
        for x in shiplist:
            newcomp += Spaceship(ship, *(x), rule).pt()
        bbox2 = newcomp.bounding_box
        if pt.nonempty():
            bbox1 = pt.bounding_box
            dx = bbox1[0] + bbox1[2] + 21 - bbox2[0]
        else:
            dx = 0
        
        dy = -round(bbox2[1] + bbox2[3] / 2)
        pt += newcomp(dx, dy)
    return (pt, traversal[1])
