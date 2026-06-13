'''Example program demonstrating how the API works
(I will write a frontend at some point, hopefully).'''
from src import DijkstraNetwork
import time
#The network class:
nw = DijkstraNetwork()
starttime = time.time()
nw.process_RLE('''#C xq4_153
x = 182, y = 50, rule = B3/S23-a5
99bo$99bobo$99b2o3$72bo18bo$70bobo16b2o16bo55bo$71b2o17b2o14bo56bobo6b
o$22bo83b3o54b2o5b2o$20b2o149b2o$21b2o130bo$151bobo$65bo86b2o$66bo109b
o$22bo41b3o108bo$22bobo120bobo18b2o7b3o$22b2o122b2o17bobo$7bo8bo129bo
19bo$8bo6bo$obo3b3o6b3o$b2o82b2o4b2o60b2o4b2o4b2o$bo82bobo4bobo59bobo
2bobo4bobo$69bobo12b2o6b2o51bo8bo3b2o6b2o$22b2o46b2o74bo$11bo10bobo45b
o73b3o$9bobo10bo84bo71b3o$10b2o94b2o71bo$84b2o6b2o12bobo49b2o6b2o3bo8b
o$32bo51bobo4bobo64bobo4bobo2bobo$31b2o52b2o4b2o66b2o4b2o4b2o$16b3o6b
3o3bobo$18bo6bo$17bo8bo132bo19bo$10b2o146bobo17b2o$9bobo136b3o7b2o18b
obo$11bo99b3o36bo$111bo37bo$112bo59b2o$172bobo$11b2o159bo$12b2o139b2o
$11bo57b3o82b2o5b2o$71bo14b2o17b2o46bo6bobo$70bo16b2o16bobo54bo$86bo18b
o3$77b2o$76bobo$78bo!
''')
print('Processed synthesis of xp25_8ca7y07ac8z8o8gy0g8o8zw13y031 in '+str(round(time.time() - starttime, 3))+' seconds.')
print(nw.getsynthRLE('xp25_8ca7y07ac8z8o8gy0g8o8zw13y031', 'xq4_153', 'b3s23-a5'))
print(nw.dump())
