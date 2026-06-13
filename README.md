# iso-shinjuku2
An improved database for arbitrary syntheses in INT rules.
## Introduction
Back in December 2025, I created [iso-shinjuku](https://github.com/PKTwentyTwo/iso-shinjuku) as an attempt to store syntheses in rules other than standard Life, since Jeremy Tan's [Shinjuku](https://gitlab.com/parclytaxel/Shinjuku) is specialised for Life only. However, it was disorganised, inefficient, and only worked for the glider, not for the plethora of unique spaceships across the INT rulespace. This rewrite attempts to address these issues - the code is cleaner, much of it being directly adapted from Shinjuku, and it can handle any spaceship.
## Method
The way in which syntheses are managed and stored is as follows:

 - A class, ```DijkstraNetwork```, is used as the processing and storage frontend. It stores syntheses using a giant dictionary, with the following structure:
 ```{rule:{spaceship_apgcode:{src_apgcode,dst_apgcode:[[orientation, phase, translation]*]}}}```
 This allows the storage of data for all rules in a single JSON file (which is compressed with gzip to save space), which reduces the storage overhead from using lots of files on a filesystem.
 - As the name suggests, a ```DijkstraNetwork``` assembles syntheses using [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra's_algorithm), which has O(n<sup>2</sup>) time complexity and always finds the shortest path from the null apgcode ```xs0_0``` to the target apgcode, provided one exists.
 - Arbitrary spaceships are represented by a class ```Spaceship```, which stores apgcode, orientation, phase, translation, and rule. When stored in JSON, only the orientation, phase, and translation are stored, since the apgcode and rule are already used as keys higher up.
 - Networks have a range of functions for handling synthesis components:
1. ```nw.process_synth(pt, ship)``` processes the component passed as a lifelib pattern.
 2. ```nw.traverse(src, dst, ship, rule)``` returns the shortest path from src to dst in the form ```[[src, apgcode1, apgcode2..., dst], cost]```.
 3. ```nw.assemblesynth(apgcode, ship, rule)``` assembles a synthesis for the specified apgcode based on the shortest path.
 4. ```nw.getsynthRLE(apgcode, ship, rule)``` returns an RLE with additional information, ideal for displaying in LifeViewer.
	5. ```nw.process_RLE(rle)``` processes a synthesis RLE, which must have a comment specifying the ship and a header to show the rule. Example:
```
#C xq4_27
x = 50, y = 38, rule = B3/S23-a5
30bobo$31bo$31bo5$24bobo$25bo$25bo19$o$b2o$o5$48bo$48b2o$48bo!
```
  - To store a network, use ```nw.dump()```, and to load a network, ```nw.load_network```. Bear in mind that networks are overwritten by default.

## Frontend
I have yet to develop a frontend for the project to allow it to be effectively used locally, or perhaps on a server. Ideas include a basic CLI, or a local HTTP server (which would allow for pages to use LifeViewer - it could just insert LifeViewers into Catagolue pages).

## Dependencies
The project dependencies are:
- [lifelib](https://gitlab.com/apgoucher/lifelib) by Adam P. Goucher, either cloned in the same directory or installed as a Python package.
- The Python module ```psutil``` - Install with either ```sudo apt install python3-psutil``` or ```pip install psutil```.
Note that some features of lifelib do not work as well on Windows, so I recommend using the project on POSIX systems or using WSL.

## License
The project is avaliable under the permissive MIT license. Some code is copied or adapted from Shinjuku, which is also avaliable under an MIT license.
