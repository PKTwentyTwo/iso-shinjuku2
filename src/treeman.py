'''Handler for Lifetrees, managing their creation and deletion.'''
import time
import lifelib
import psutil
#Get avaliable RAM in MB:
ram = psutil.virtual_memory()[1]//1000000
#Maximum number of lifetrees. Feel free to change.
MAXLT = 8
#Dictionary storing lifetrees:
lifetrees = {}
#Generation time of each lifetree:
gentime = {}
#Memory allocated to each lifetree, with a max total of half of free RAM.
mem = ram // (2 * MAXLT)
def getlifetree(rule):
    '''Returns a Lifetree for the given rule.'''
    clearmem()
    rule = lifelib.genera.sanirule(rule)
    genus = lifelib.genera.obtain_genus(rule)
    if genus not in ['isotropic', 'lifelike', 'b3s23life']:
        raise ValueError('Error: Rule {rule} is not a supported rule.')
    if rule not in lifetrees:
        lt = lifelib.load_rules(rule).lifetree(n_layers = 1, memory = mem)
        lifetrees[rule] = lt
    gentime[rule] = time.time()
    return lifetrees[rule]
def clearmem():
    '''Deletes the least recently used Lifetree if at full capacity.'''
    if len(lifetrees) < MAXLT:
        return None
    mintime = time.time() + 100
    minrule = 'b3s23'
    for x in gentime:
        if gentime[x] < mintime:
            mintime = gentime[x]
            minrule = x
    del lifetrees[minrule]
    del gentime[minrule]
    return None
