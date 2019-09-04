"""
Inspired by the website below. Graph class, covert_image_to_graph created by Eric
https://www.redblobgames.com/pathfinding/a-star/introduction.html
"""
import Queue
from PIL import Image


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GREY = (50, 50, 50)


graph = []

class Graph():
    def __init__(self, graph, graph_cost):
        self.graph = graph
        self.graph_cost = graph_cost

    def neighbors(self, current):
        start = (current[0] - 1, current[1] - 1)
        end = (current[0] + 1, current[1] + 1)
        neighbor_list = []
        for h in range(3):
            for v in range(3):
                if (self.graph[start[0] + h])[start[1] + v] == 0:
                    neighbor_list.append((start[0] + h, start[1] + v))
        try:
            neighbor_list.remove((current[0],current[1]))
        except ValueError:
			pass
        
        return neighbor_list

    def cost(self, current, cell):
        return self.graph_cost[cell[0]][cell[1]]
        
def import_image():
	return Image.open('data/image/map.png')

def convert_image_to_graph ():
	#convert background map into graph
	global graph
	image = import_image()
	imgGraph = []
	imgGraph_Cost = []
	step = 20  # step variable so that the graph generalizes background map instead of finding the value for every pixel
	for x in range(image.size[0]/step):
		imgGraph.append([])
		imgGraph_Cost.append([])
		for y in range(image.size[1]/step):
			RGB = image.getpixel((x*step,y*step))
			if RGB == (0, 0, 0, 255):
				imgGraph[x].append(1)
			else:
				imgGraph[x].append(0)
			imgGraph_Cost[x].append(1)
	graph = Graph(imgGraph, imgGraph_Cost)
	return graph


def heuristic(a, b):
    # Manhattan distance on a square grid
	return abs(a[1] - b[1]) + abs(a[0] - b[0])

def return_path(start, goal, graph):
	# this portion is borrowed and altered
	start = tuple([x/20 for x in start])# steps
	goal = tuple([x/20 for x in goal])
	frontier = Queue.PriorityQueue()
	frontier.put(start, 0)
	came_from = {}
	cost_so_far = {}
	came_from[start] = None
	cost_so_far[start] = 0

	while not frontier.empty():
		current = frontier.get()

		if current == goal:
			break

		for cell in graph.neighbors(current):
			new_cost = cost_so_far[current] + graph.cost(current, cell)
			if cell not in cost_so_far or new_cost < cost_so_far[cell]:
				cost_so_far[cell] = new_cost
				priority = new_cost + heuristic(goal, cell)
				frontier.put(cell, priority)
				came_from[cell] = current
				
	current = goal
	path = []
	
	while current != start:
		path.append(current)
		try:
			current = came_from[current]
		except KeyError:
			pass
	came_from = {}
	path.append(start)
	path.reverse()
	return path
	
"""
path = return_path((200, 200), (300, 380), graph)

###Visualizing astar###
import pygame  # optional, for visualizing astar
pygame.init()

# sets size of the screen
screenx = 1024
screeny = 768

# Initialize and set screen
pygame.init()
screen = pygame.display.set_mode((screenx, screeny), 0, 32)

# Controling speed of game
clock = pygame.time.Clock()
fps = 30


def draw(path):
    for row in range(len(graph.graph)):
        for col in range(len(graph.graph[0])):
            cell = (col, row)
            cell_rect = pygame.Rect(cell[0] * 20, cell[1] * 20, 20, 20)
            if (graph.graph[row])[col] == 1:
                pygame.draw.rect(screen, BLUE, cell_rect)
            else:
                pygame.draw.rect(screen, WHITE, cell_rect)

    for cell in path:
        cell_rect = pygame.Rect(cell[0] * 20, cell[1] * 20, 20, 20)
        pygame.draw.rect(screen, BLACK, cell_rect)
        path.remove(cell)
        break
        

rungame = True
while rungame:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rungame = False

    screen.fill(WHITE)
    mouse_pos = pygame.mouse.get_pos()
    draw(path)
    pygame.display.update()
    clock.tick(fps)

"""
