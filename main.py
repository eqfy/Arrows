"""
Arrow.IO
Created by Eric Yan, Jeffery Wang, Johnathan Sun-Payeur
This is a game inspired by a mobile game called arrow.io.
"""
import pygame
import math
import random
import time
from astar import convert_image_to_graph, return_path

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
cRED = (200, 0, 20)
RED = (255, 0, 0)
cBLUE = (0, 235, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GREY = (50, 50, 50)

# sets size of the screen
screenx = 1124
screeny = 768

# Initialize and set screen
pygame.init()
screen = pygame.display.set_mode((screenx, screeny), 0, 32)
pygame.display.set_caption("RealArrow.IO")
pygame.display.set_icon(pygame.image.load("data/image/arrow.jpg"))

# Import fonts
fontTiny = pygame.font.Font(None, 17)
fontSmall = pygame.font.Font(None, 24)
font = pygame.font.Font(None, 32)
fontMed = pygame.font.Font(None, 50)
fontBig = pygame.font.Font(None, 64)
fontHuge = pygame.font.Font(None, 128)

# Global game variables
gameover = False
score = 0

# Controling speed of game
clock = pygame.time.Clock()
fps = 30

# Sound
pygame.mixer.pre_init(44100, -16, 2, 2048)

# Projectile
projectile_id = 0
# projectile damage = base*multiplier
projectile_damage_multiplier = {"arrow": 1, "freeze_arrow": 1.3, "poison_arrow": 1.5, "fireball": 2, "smart_arrow": 3}
# corresponding projectile type for each level
projectile_level = {1: "arrow", 3: "freeze_arrow", 5: "poison_arrow", 10: "fireball", 15: "smart_arrow"}
level_list = [1, 3, 5, 10, 15]


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # Variables for sprite class
        self.ori_image = pygame.image.load("data/image/standing_still_0.png").convert_alpha()
        self.image = self.ori_image
        self.map_collision_image = pygame.image.load("data/image/standing_still_0.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = (450, 330)
        self.mask = pygame.mask.from_surface(self.image)
        # Direction
        self.direction = 0
        self.direction_radians = 0
        # Game variables
        self.hp = 100
        self.max_hp = 100
        self.exp = 0
        self.level = 1
        self.kills = 0
        self.deaths = 0
        self.speed = 5
        self.cooldown = 100
        self.state = "standing_still"
        self.past_state = "standing_still"
        self.previous_mouse = 0
        self.skin = "default"  # Other skins: default, black, tiger, army, desert, ghost
        self.coins = 0
        self.Looted = False
        # Projectile
        self.projectile_type = projectile_level[self.level]
        self.projectile_damage = projectile_damage_multiplier[self.projectile_type] * int(self.level * 5)
        self.available_projectile = ["arrow"]
        self.cool_counter = 0
        self.cooled = True
        self.counter = -1
        # Images
        self.standing_still_image = []
        self.fired_shot_image = []
        self.aiming_image = []
        self.import_image()

    def move(self):
        # Controls movement of player
        # Changes player's state according to the player's movement and the player's progress in firing a projectile
        if mouse_pressed[0] == 1 and self.cooled and self.state != "dead":
            self.state = "aiming"
            self.past_state = "walking"
            self.previous_mouse = 1
        elif mouse_pressed[0] == 0 and self.previous_mouse == 1 or mouse_pressed[0] == 0 and self.cooled is False and self.state != "dead":
            self.state = "fired_shot"
            self.past_state = "aiming"
            self.previous_mouse = 0
        elif self.cooled and self.state != "dead":
            self.state = "standing_still"
            self.past_state = "standing_still"
        ori_rect = self.rect.copy()
        begin_moving = False
        if key_pressed[pygame.K_LEFT] or key_pressed[pygame.K_a]:
            self.rect.left -= self.speed
            begin_moving = True
        if key_pressed[pygame.K_RIGHT] or key_pressed[pygame.K_d]:
            self.rect.left += self.speed
            begin_moving = True
        if key_pressed[pygame.K_UP] or key_pressed[pygame.K_w]:
            self.rect.top -= self.speed
            begin_moving = True
        if key_pressed[pygame.K_DOWN] or key_pressed[pygame.K_s]:
            self.rect.top += self.speed
            begin_moving = True

        if begin_moving and self.state == "standing_still":
            self.past_state = "standing_still"
            self.state = "walking"

        if self.map_collision():
            self.rect = ori_rect  # places player in orginal position if movement hits a map wall

    def hit(self):
        # Runs when player is hit by enemy projectile or when player is dead
        if self.projectile_collision():
            self.state = "hit"
            self.hp -= enemy[0].damage
        if self.hp <= 0 and self.state != "dead":   # when the player just died
            self.past_state = "hit"
            self.state = "dead"
            self.dead()
        elif self.state == "dead":  # when the player have died for some time
            self.past_state = "dead"
            self.dead()

    def dead(self):
        # Runs when player is dead and checks to see if player can respawn
        screen.fill(cRED)
        screen.blit(fontHuge.render('YOU DIED', False, RED), (400, 310))
        screen.blit(font.render('click to respawn', False, RED), (465, 385))
        self.rect.topleft = (-100, 0)
        if self.past_state != "dead":  # plays just died sound effect
            pygame.mixer.stop()  # Clear all channels to ensure dead sound can play
            sound.dead_sound.play()
            duration = sound.dead_sound.get_length()
            time.sleep(duration)  # enable the entire sound effect to be played
        self.past_state = "dead"
        pygame.mixer.stop()  # stops all sound

    def respawn(self):
        # Respawning the player after dying
        self.level = 1
        self.exp = 0
        self.max_hp = 100
        self.hp = self.max_hp
        self.deaths += 1
        self.rect.topleft = (450, 330)
        self.speed = 10
        self.state = "standing_still"
        self.past_state = "standing_still"
        self.available_projectile = ["arrow"]
        self.projectile_type = "arrow"
        for i in enemy:
            i.levelup()
            i.respawn()
        channel0.play(sound.BG, loops=-1)
        info.lvlup = 30 * self.level

    def import_image(self):
        # new import
        self.standing_still_image = []
        self.fired_shot_image = []
        self.aiming_image = []
        for i in range(3):
            self.standing_still_image.append(pygame.image.load(
                "data/image/skins/" + str(self.skin) + "/standing_still_" + str(i) + ".png").convert_alpha())
            self.fired_shot_image.append(pygame.image.load(
                "data/image/skins/" + str(self.skin) + "/fired_shot_" + str(i) + ".png").convert_alpha())
            self.aiming_image.append(
                pygame.image.load("data/image/skins/" + str(self.skin) + "/aiming_" + str(i) + ".png").convert_alpha())

    def animation(self):
        # Chooses correct image and plays animation according to state of player
        self.counter += 1
        self.frame = (self.counter / 5) % 3
        if self.state == "walking":
            self.ori_image = self.standing_still_image[self.frame]
        elif self.state == "fired_shot":
            self.ori_image = self.fired_shot_image[self.frame]
        elif self.state == "aiming":
            self.ori_image = self.aiming_image[self.frame]
        elif self.state == "standing_still":
            self.ori_image = self.standing_still_image[0]

    def map_collision(self):
        # Detect collision with map walls
        if self.state != "walking":  # to prevent player from getting stuck in the wall because the shooting image is smaller than the walking image
            current_image = self.image
            self.image = self.map_collision_image
            self.mask = pygame.mask.from_surface(self.map_collision_image)
            hit_list = pygame.sprite.spritecollide(self, map_group, False, pygame.sprite.collide_mask)
            self.image = current_image
            self.mask = pygame.mask.from_surface(current_image)
        else:
            hit_list = pygame.sprite.spritecollide(self, map_group, False, pygame.sprite.collide_mask)
        for i in hit_list:
            return True

    def projectile_collision(self):
        # Detect collision with enemy projectiles
        hit_list = pygame.sprite.spritecollide(self, enemy_projectile_group, True, pygame.sprite.collide_mask)
        for i in hit_list:
            return True

    def rotate(self):
        # rotates player image according to mouse position
        old_direction = self.direction  # stores old direction to be reverted back to
        try:  # finds direction of player image to the mouse position
            self.direction_radians = math.atan2(float(mouse_pos[0] - self.rect.center[0]),
                                                float(mouse_pos[1] - self.rect.center[1]))
            self.direction = math.degrees(self.direction_radians)
        except ZeroDivisionError:
            pass

        orig_rect = self.ori_image.get_rect()
        self.image = pygame.transform.rotate(self.ori_image, self.direction)
        rot_rect = orig_rect.copy()
        rot_rect.center = self.image.get_rect().center
        self.image = self.image.subsurface(rot_rect).copy()
        self.mask = pygame.mask.from_surface(self.image)

        if self.map_collision():  # makes sure player does not rotate if rotating causes it to enter the walls
            self.direction = old_direction
            self.direction_radians = math.radians(self.direction)
            orig_rect = self.ori_image.get_rect()
            self.image = pygame.transform.rotate(self.ori_image, self.direction)
            rot_rect = orig_rect.copy()
            rot_rect.center = self.image.get_rect().center
            self.image = self.image.subsurface(rot_rect).copy()
            self.mask = pygame.mask.from_surface(self.image)
            if self.state == "walking":
                self.map_collision_image = self.image

    def fire_shot(self):
        # Attempts to shoot projectile
        if self.state == "fired_shot" and self.cooled:  # Runs to check if conditions are met for firing projectile
            global projectile_id
            # Passes the values for shooting correctly (projectile type, position direction)
            arrow[projectile_id].active = True
            arrow[projectile_id].name = self.projectile_type
            arrow[projectile_id].x = self.rect.center[0]
            arrow[projectile_id].y = self.rect.center[1]
            arrow[projectile_id].direction = self.direction
            arrow[projectile_id].direction_radians = math.radians(self.direction)
            arrow[projectile_id].update()
            all_object_group.add(arrow[projectile_id])
            projectile_group.add(arrow[projectile_id])
            projectile_id += 1
            # Resets cool-down variables
            self.cooled = False
            self.state = "standing_still"
            self.past_state = "fired_shot"

    def cool_down(self):
        # cool down counter for firing projectiles
        if ((self.counter - self.cool_counter) / 50) % 2 == 1:
            self.cool_counter = self.counter
            self.cooled = True

    def levelup(self):
        # Levels up player
        if self.exp >= info.lvlup:
            # Player's hp and damage is increased
            orig_max_hp = player.max_hp
            self.max_hp = int((self.level * 100) ** (1 + self.level / 50.0))
            self.hp = int(self.hp * (float(self.max_hp) / float(orig_max_hp) + 0.03))
            if self.hp > self.max_hp:
                self.hp = self.max_hp
            self.projectile_damage = projectile_damage_multiplier[self.projectile_type] * int(self.level * 5)
            try:  # attempts to unlock new projectile type
                self.projectile_type = projectile_level[self.level]
                self.available_projectile.append(self.projectile_type)
                self.projectile_damage = projectile_damage_multiplier[self.projectile_type] * int(self.level * 5)
            except KeyError:
                pass
            # Player level and exp for next level are increased
            self.level += 1
            info.lvlup = 30 * self.level
            self.exp = 1
            for i in enemy:  # makes sure enemy levels up with player
                i.levelup()

    def change_projectile(self):
        # changes projectile type is the projectile is unlocked and the corresponding number key is pressed
        if key_pressed[pygame.K_1]:
            self.projectile_type = "arrow"
        elif key_pressed[pygame.K_2] and "freeze_arrow" in player.available_projectile:
            self.projectile_type = "freeze_arrow"
        elif key_pressed[pygame.K_3] and "poison_arrow" in player.available_projectile:
            self.projectile_type = "poison_arrow"
        elif key_pressed[pygame.K_4] and "fireball" in player.available_projectile:
            self.projectile_type = "fireball"
        elif key_pressed[pygame.K_5] and "smart_arrow" in player.available_projectile:
            self.projectile_type = "smart_arrow"

    def update(self):
        self.levelup()
        self.rotate()
        self.move()
        self.animation()
        self.change_projectile()
        self.fire_shot()
        self.cool_down()
        self.hit()
        sound.play_sound(self.past_state, self.state)
        if self.state == "dead":
            if mouse_pressed[0] == 1:
                self.respawn()


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # Varaibles needed for sprite class
        self.ori_image = pygame.image.load("data/image/enemy_standing_still_0.png").convert_alpha()
        self.image = self.ori_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (-30, -30)
        self.mask = pygame.mask.from_surface(self.image)
        self.direction = 0
        self.direction_radians = 0
        # Game variables for the enemy
        self.hp = 20
        self.max_hp = 20
        self.damage = 3
        self.speed = 5
        self.exp = 20
        self.levelup()
        # states of the enemy
        self.state = "walking"
        self.past_state = "walking"
        self.is_hit = False
        # stores images for different enemy states
        self.standing_still_image = []
        self.fired_shot_image = []
        self.aiming_image = []
        self.import_image()
        # variables for firing projectile
        self.projectile_type = "enemy_arrow"
        self.counter_step = 50
        self.counter = random.randint(0, self.counter_step)
        self.cool_counter = 0
        self.cooled = True
        # astar related variables
        self.execute_astar = False
        self.astar_counter = 0
        self.astar_counter_other = 0
        self.path = []
        self.at_point = False
        # True when enemy has just respawned
        self.init = True

    def import_image(self):
        # Lods images
        for i in range(3):
            self.standing_still_image.append(
                pygame.image.load("data/image/enemy_standing_still_" + str(i) + ".png").convert_alpha())
            self.fired_shot_image.append(
                pygame.image.load("data/image/enemy_fired_shot_" + str(i) + ".png").convert_alpha())
            self.aiming_image.append(pygame.image.load("data/image/enemy_aiming_" + str(i) + ".png").convert_alpha())

    def animation(self):
        # Animations for enemy character
        self.counter += 1
        self.frame = (self.counter / 5) % 3
        if self.state == "walking":
            self.ori_image = self.standing_still_image[self.frame]
        elif self.state == "fired_shot":
            self.ori_image = self.fired_shot_image[self.frame]
        elif self.state == "aiming":
            self.ori_image = self.aiming_image[self.frame]

    def rotate(self):
        # Rotates enemy's direction
        orig_rect = self.ori_image.get_rect()
        self.image = pygame.transform.rotate(self.ori_image, self.direction)
        rot_rect = orig_rect.copy()
        rot_rect.center = self.image.get_rect().center
        self.image = self.image.subsurface(rot_rect).copy()
        self.mask = pygame.mask.from_surface(self.image)

    def random_placement(self):
        # Randomly places enemy when respawned
        valid_location = False
        while valid_location is False:
            self.rect.center = (random.randint(20, screenx - 200), random.randint(20, screeny))
            if self.map_collision() == None and self.player_collision() == None and self.enemy_collision() == None:
                self.init = False
                break

    def map_collision(self):
        # Detect collision with the map walls
        hit_list = pygame.sprite.spritecollide(self, map_group, False, pygame.sprite.collide_mask)
        for i in hit_list:
            return True

    def projectile_collision(self):
        # Detect collision with projectile
        hit_list = pygame.sprite.spritecollide(self, projectile_group, True, pygame.sprite.collide_mask)
        for i in hit_list:
            return True

    def player_collision(self):
        # Detect collision with player
        hit_list = pygame.sprite.spritecollide(self, player_group, False, pygame.sprite.collide_mask)
        for i in hit_list:
            return True

    def enemy_collision(self):
        # Detect collision with other enemies
        enemy_group.remove(self)
        hit_list = pygame.sprite.spritecollide(self, enemy_group, False, pygame.sprite.collide_mask)
        enemy_group.add(self)
        for i in hit_list:
            return True

    def move(self):
        # Controls enemy movement
        self.astar_decision()
        if len(self.path) > 1:  # only moves when the path to the player is greater than one
            self.move_to_next_point(self.path[0])
            if self.at_point:  # if enemy is at the first point in the path, this point is removed
                if len(self.path) > 3:
                    self.path.pop(0)
                    self.at_point = False
                elif 1 < len(
                        self.path) <= 3 and self.enemy_collision():  # to prevent the enemys from stacking on top of each other after reaching the goal
                    self.find_nearby_point(1)
                    self.at_point = True

    def astar_decision(self):
        # Calls corresponding astar counters according to enemy's state, uses astar to return path to player if conditions are met
        if player.state == "walking":
            self.astar_cooldown()
        else:
            self.astar_cooldown_other()

        if self.execute_astar:
            self.path = return_path(self.rect.center, player.rect.center, map_bg.graph)
            self.execute_astar = False

    def move_to_next_point(self, point):
        # Moves the enemy to the first point in its path
        # If enemy is at that point, then moves on to next point
        dx = point[0] * map_bg.graph.step - self.rect.center[0]
        dy = point[1] * 20 - self.rect.center[1]

        centerx, centery = self.rect.center
        at_x = False
        at_y = False

        if abs(dx) <= self.speed:
            centerx = point[0] * 20
            at_x = True
        if abs(dy) <= self.speed:
            centery = point[1] * 20
            at_y = True

        if dx > 0 and not at_x:
            centerx += self.speed
        elif dx < 0 and not at_x:
            centerx -= self.speed

        if dy > 0 and not at_y:
            centery += self.speed
        elif dy < 0 and not at_y:
            centery -= self.speed

        self.rect.center = (centerx, centery)

        if at_x and at_y:
            self.at_point = True

    def find_nearby_point(self, step):
        # Finds nearby points that enemys can move to in order to prevent enemies stacking on top of each other
        new_point = (0, 0)
        while map_bg.graph.graph[new_point[0]][new_point[1]] == 1:
            new_point = (self.path[0][0] + random.randint(-step, step), self.path[0][1] + random.randint(-step, step))
        self.path[0] = new_point

    def astar_cooldown(self):
        # astar counter for when enemy is in walking state
        self.astar_counter -= 1
        if self.astar_counter <= 0:
            self.astar_counter = random.randint(50, 200)
            self.execute_astar = True

    def astar_cooldown_other(self):
        # astar counter for when enemy is in states other than walking
        self.astar_counter_other -= 1
        if self.astar_counter_other <= 0:
            self.astar_counter_other = random.randint(100, 300)
            self.execute_astar = True

    def fire_shot(self):
        # Attempts to shoot projectile
        if self.state == "fired_shot" and self.cooled:  # Runs to check if conditions are met for firing projectile
            global projectile_id
            # Passes the values for shooting correctly (projectile type, position direction)
            arrow[projectile_id].active = True
            arrow[projectile_id].name = self.projectile_type
            arrow[projectile_id].x = self.rect.center[0]
            arrow[projectile_id].y = self.rect.center[1]
            arrow[projectile_id].direction = self.direction
            arrow[projectile_id].direction_radians = math.radians(self.direction)
            arrow[projectile_id].update()
            all_object_group.add(arrow[projectile_id])
            enemy_projectile_group.add(arrow[projectile_id])
            projectile_id += 1
            # Resets cool-down variables
            self.cooled = False
            self.past_state = self.state
            self.state = "walking"

    def aim_direction(self):
        # Calculates angle when enemy faces player
        try:
            self.direction = math.degrees(math.atan2(float(player.rect.center[0] - self.rect.center[0]),
                                                     float(player.rect.center[1] - self.rect.center[1])))
            self.direction_radians = math.radians(self.direction)
        except ZeroDivisionError:
            pass

    def cool_down(self):
        # For cooling down the enemy's firing of projectile
        if ((self.counter - self.cool_counter) / self.counter_step) % 2 == 1:
            self.cool_counter = self.counter
            self.cooled = True
            if self.state == "standing_still" or self.state == "walking":
                self.past_state = self.state
                self.state = "aiming"
            elif self.state == "aiming":
                self.past_state = self.state
                self.state = "fired_shot"

    def respawn(self):
        # Runs when enemy respawns (enemy is randomly placed. path cleared, have stats rest and added to sprite groups)
        self.random_placement()
        self.path = []
        self.hp = self.max_hp
        all_object_group.add(self)
        enemy_group.add(self)

    def hit(self):
        # Runs when enemy is hit by player
        if self.projectile_collision():
            self.is_hit = True
            self.hp -= player.projectile_damage
            self.past_state = self.state
            self.state = "hit"

            if self.hp <= 0:
                all_object_group.remove(self)
                enemy_group.remove(self)
                player.exp += enemy[0].exp
                player.coins += 1
                self.respawn()

    def levelup(self):
        # enemy levels up with the player. They get relatively stonger at higher levels
        self.max_hp = int(player.level * 20 / (player.level * 1.5))
        self.damage = int((player.level * 10) ** (1 + player.level / 50.0))
        self.exp = int(player.level * 25 ** (0.98))

    def update(self):
        if player.state != "dead":  # Enemy only active when player is alive
            if self.init:
                self.random_placement()
            self.animation()
            self.aim_direction()
            self.fire_shot()
            self.cool_down()
            self.rotate()
            self.move()
            self.hit()
            sound.play_sound(self.past_state, self.state)
            if self.is_hit:
                self.state = self.past_state
                self.is_hit = False


class Map(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # Variables for sprite class
        self.image = pygame.image.load("data/image/map.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        # Converts the background map into a 2D graph for astar path finding
        self.graph = convert_image_to_graph()


class Projectile(pygame.sprite.Sprite):
    def __init__(self, name):
        pygame.sprite.Sprite.__init__(self)
        # Variables for sprite class
        self.ori_image = pygame.image.load("data/image/arrow.png").convert_alpha()
        self.image = self.ori_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.top = -100  # moves the arrow outside of screen
        # Movment of projectile
        self.speed = 15.0
        self.x = 0
        self.y = 0
        # Type of projectile
        self.name = name
        # Direction in degrees and radians
        self.direction = 0
        self.direction_radians = 0
        # Animation variables
        self.counter = 0
        self.frame = 0
        # Variable for the first shot
        self.active = False
        self.released = False
        self.reposition = True
        self.dist_from_base_center = 30
        # Store image in lists
        self.arrow_image = []
        self.enemy_arrow_image = []
        self.fireball_image = []
        self.poison_arrow_image = []
        self.freeze_arrow_image = []
        self.smart_arrow_image = []
        self.import_image()

    def import_image(self):
        # Loads images
        for i in range(2):
            self.fireball_image.append(pygame.image.load("data/image/fireball_" + str(i) + ".png").convert_alpha())
            self.poison_arrow_image.append(
                pygame.image.load("data/image/poison_arrow_" + str(i) + ".png").convert_alpha())
        self.arrow_image.append(pygame.image.load("data/image/arrow.png").convert_alpha())
        self.enemy_arrow_image.append(pygame.image.load("data/image/enemy_arrow.png").convert_alpha())
        self.freeze_arrow_image.append(pygame.image.load("data/image/freeze_arrow.png").convert_alpha())
        self.smart_arrow_image.append(pygame.image.load("data/image/smart_arrow.png").convert_alpha())

    def animation(self):
        # Selects correct image according to the arrow name of the shooter
        # Plays animation if the projectile type has an animation
        self.counter += 1
        self.frame = (self.counter / 5) % 2
        if self.name == "arrow":
            self.ori_image = self.arrow_image[0]
        elif self.name == "fireball":
            self.ori_image = self.fireball_image[self.frame]
        elif self.name == "freeze_arrow":
            self.ori_image = self.freeze_arrow_image[0]
        elif self.name == "poison_arrow":
            self.ori_image = self.poison_arrow_image[self.frame]
        elif self.name == "smart_arrow":
            self.ori_image = self.smart_arrow_image[0]
        elif self.name == "enemy_arrow":
            self.ori_image = self.enemy_arrow_image[0]

    def placement(self):
        # Places projectile around character
        dx = math.sin(self.direction_radians) * self.dist_from_base_center
        dy = math.cos(self.direction_radians) * self.dist_from_base_center
        self.rect.center = (self.rect.center[0] + dx, self.rect.center[1] + dy)
        self.reposition = False

    def rotate(self):
        # Rotates the projectile image according to the shooter's direction when shot
        if self.released is False:  # When projectile is just released
            self.animation()
            self.released = True

        orig_rect = self.ori_image.get_rect()
        self.image = pygame.transform.rotate(self.ori_image, self.direction)
        rot_rect = orig_rect.copy()
        rot_rect.center = orig_rect.center
        self.image = self.image.subsurface(rot_rect).copy()
        self.mask = pygame.mask.from_surface(self.image)

    def move(self):
        # Moves the arrow according to the rotated angle
        self.speedx = math.sin(self.direction_radians) * self.speed
        self.speedy = math.cos(self.direction_radians) * self.speed
        self.x += self.speedx
        self.y += self.speedy
        self.rect.center = (self.x, self.y)

    def map_collision(self):
        # Checks for collision with the map
        # If True, removes projectile from all sprite groups and return True
        hit_list = pygame.sprite.spritecollide(self, map_group, False, pygame.sprite.collide_mask)
        for i in hit_list:
            all_object_group.remove(self)
            projectile_group.remove(self)
            enemy_projectile_group.remove(self)
            return True

    def respawn(self):
        # Reset variables for respawning projectile
        self.active = False
        self.released = False
        self.reposition = True

    def update(self):
        if self.active:
            self.animation()
            self.rotate()
            if self.reposition:
                self.placement()
            self.move()

        if self.map_collision():  # Calls respawn if projectile hits map walls
            self.respawn()


class Info():  # The area on the right that contains the player stats, arrow menu and shop
    def __init__(self):
        self.kd = 1.0
        self.lvlup = 3 * player.level
        self.XPbar = 84 * player.exp / self.lvlup
        self.HPbar = 84 * player.hp / 100

        # import images
        self.lock = pygame.image.load('data/image/lock.png')
        self.arrow = pygame.image.load('data/image/arrow.png')
        self.freeze_arrow = pygame.image.load('data/image/freeze_arrow.png')
        self.poison_arrow = pygame.image.load('data/image/poison_arrow_0.png')
        self.fireball = pygame.image.load('data/image/fireball_0.png')
        self.smart_arrow = pygame.image.load('data/image/smart_arrow.png')

        self.Clicker1 = False  #
        self.Clicker2 = False  #

        self.ClickProfile = True
        self.ClickShop = False

        ###
        self.DisabledProfile = 0
        self.DisabledShop = 0
        self.BlackUnlock = False
        self.DesertUnlock = False
        self.ArmyUnlock = False
        self.TigerUnlock = False
        self.GhostUnlock = False

    def ratio(self):
        # Calculates the kill/death ratio of the player
        if player.deaths == 0 and player.kills < 2:
            self.kd = str(1.0)
        elif player.deaths == 0 and player.kills >= 2:
            self.kd = str(player.kills) + ".0"
        else:
            self.kd = str(player.kills / player.deaths + 0.0)

    def FPS_display(self):
        FPS = clock.get_fps()
        screen.blit(font.render('FPS: ' + str(int(FPS)), False, (0, 0, 0)), (906, 30))

    def LVL(self):
        if player.exp >= self.lvlup:
            player.level += 1
            self.lvlup = 30 * player.level
            player.exp = 1
        screen.blit(font.render('Level: ' + str(player.level), True, (0, 0, 0)), (1026, 5))
        self.XPbar = 84 * player.exp / self.lvlup
        pygame.draw.rect(screen, cBLUE, (1029, 28, self.XPbar, 14), 0)
        pygame.draw.rect(screen, BLACK, (1028, 29, 85, 12), 3)
        screen.blit(fontTiny.render('XP: ' + str(player.exp), True, BLACK), (1030, 30))  # 1028, 45

    def PROFILE(self):
        # pygame.draw.rect(screen, BLACK, (1028, 45, 85, 60), 1 )
        pygame.draw.rect(screen, GREEN, (1028, 45, 42, 42), 0)  # Button
        screen.blit(fontTiny.render('Profile', False, (0, 0, 0)), (1031, 60))  # Button
        if self.ClickProfile == True:
            screen.blit(fontSmall.render('Kills: ' + str(player.kills), True, (0, 0, 0)), (1029, 465))
            screen.blit(fontSmall.render('Deaths: ' + str(player.deaths), True, (0, 0, 0)), (1029, 490))
            screen.blit(fontSmall.render('K/D: ' + str(self.kd), True, (0, 0, 0)), (1029, 515))
            pygame.draw.rect(screen, GREY, (1027, 450, 85, 100), 3)  # Popup
            screen.blit(font.render('Profile', False, GREY), (1029, 430))  # Popup

    def SHOP_display(self):
        if player.coins >= 99:
            player.coins = 99
        pygame.draw.rect(screen, BLUE, (1070, 45, 42, 42), 0)  # SHOP
        screen.blit(fontTiny.render('SHOP', False, (0, 0, 0)), (1074, 60))  # SHOP
        pygame.draw.rect(screen, BLUE, (1028, 129, 86, 35), 0)  # Bill
        screen.blit(pygame.image.load('data/image/coins.png'), (1030, 127))
        screen.blit(fontMed.render(str(player.coins), True, (0, 0, 0)), (1072, 130))
        if self.ClickShop == True:
            pygame.draw.rect(screen, GREY, (1027, 450, 85, 0), 3)  # Popup
            screen.blit(font.render('Shop', False, GREY), (1029, 430))  # Popup

            screen.blit(pygame.font.Font(None, 15).render('Free', False, BLUE), (1036, 469))
            pygame.draw.rect(screen, BLACK, (1027, 480, 45, 67), 3)
            screen.blit(pygame.image.load('data/image/skins/default/aiming_0.png'), (1015, 480))

            screen.blit(pygame.font.Font(None, 15).render('1 C$', False, BLUE), (1079, 469))
            pygame.draw.rect(screen, BLACK, (1071, 480, 45, 67), 3)
            screen.blit(pygame.image.load('data/image/skins/black/aiming_0.png'), (1060, 480))
            if self.BlackUnlock == False:
                screen.blit(pygame.image.load('data/image/lock.png'), (1071, 480))

            screen.blit(pygame.font.Font(None, 15).render('5 C$', False, BLUE), (1036, 549))
            pygame.draw.rect(screen, BLACK, (1027, 560, 45, 67), 3)
            screen.blit(pygame.image.load('data/image/skins/desert/aiming_0.png'), (1015, 558))
            if self.DesertUnlock == False:
                screen.blit(pygame.image.load('data/image/lock.png'), (1027, 560))

            screen.blit(pygame.font.Font(None, 15).render('10 C$', False, BLUE), (1079, 549))
            pygame.draw.rect(screen, BLACK, (1071, 560, 45, 67), 3)
            screen.blit(pygame.image.load('data/image/skins/army/aiming_0.png'), (1060, 558))
            if self.ArmyUnlock == False:
                screen.blit(pygame.image.load('data/image/lock.png'), (1071, 560))

            screen.blit(pygame.font.Font(None, 15).render('25 C$', False, BLUE), (1036, 629))
            pygame.draw.rect(screen, BLACK, (1029, 640, 45, 67), 3)
            screen.blit(pygame.image.load('data/image/skins/tiger/aiming_0.png'), (1015, 636))
            if self.TigerUnlock == False:
                screen.blit(pygame.image.load('data/image/lock.png'), (1029, 640))

            screen.blit(pygame.font.Font(None, 15).render('50 C$', False, BLUE), (1079, 629))
            pygame.draw.rect(screen, BLACK, (1071, 640, 45, 67), 3)
            screen.blit(pygame.image.load('data/image/skins/ghost/aiming_0.png'), (1060, 636))
            if self.GhostUnlock == False:
                screen.blit(pygame.image.load('data/image/lock.png'), (1071, 640))

    def purchase(self):
        mx, my = pygame.mouse.get_pos()
        # Checks if mouse position is above the default skin icon, being clicked, and if it has been purchased yet
        if (1070 - mx) in range(0, 41) and (482 - my) in range(-63, 0) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.ClickShop == True:
            player.skin = "default"  # default, black, tiger, army, desert, ghost
            player.import_image()
        if (1113 - mx) in range(0, 41) and (482 - my) in range(-63, 0) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.ClickShop == True:
            if self.BlackUnlock == False and player.coins >= 1:
                self.BlackUnlock = True
                player.coins -= 1
            if self.BlackUnlock:
                player.skin = "black"
                player.import_image()
        if (1070 - mx) in range(0, 41) and (625 - my) in range(0, 63) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.ClickShop == True:
            if self.DesertUnlock == False and player.coins >= 5:
                self.DesertUnlock = True
                player.coins -= 5
            if self.DesertUnlock == True:
                player.skin = "desert"
                player.import_image()
        if (1113 - mx) in range(0, 41) and (625 - my) in range(0, 63) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.ClickShop == True:
            if self.ArmyUnlock == False and player.coins >= 10:
                self.ArmyUnlock = True
                player.coins -= 10
            if self.ArmyUnlock == True:
                player.skin = "army"
                player.import_image()
        if (1070 - mx) in range(0, 41) and (706 - my) in range(0, 63) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.ClickShop == True:
            if self.TigerUnlock == False and player.coins >= 25:
                self.TigerUnlock = True
                player.coins -= 25
            if self.TigerUnlock == True:
                player.skin = "tiger"
                player.import_image()
        if (1113 - mx) in range(0, 41) and (706 - my) in range(0, 63) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.ClickShop == True:
            if self.GhostUnlock == False and player.coins >= 50:
                self.GhostUnlock = True
                player.coins -= 50
            if self.GhostUnlock == True:
                player.skin = "ghost"
                player.import_image()

    def HP_display(self):
        screen.blit(font.render('HP: ' + str(player.hp), True, (255, 0, 0)), (1027, 89))
        self.HPbar = 84 * player.hp / player.max_hp
        pygame.draw.rect(screen, RED, (1029, 111, self.HPbar, 14), 0)
        pygame.draw.rect(screen, BLACK, (1028, 112, 85, 12), 3)

    def projectile(self):
        if player.projectile_type == "arrow":
            pygame.draw.rect(screen, GREEN, (1030, 180, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1030, 180, 37, 67), 3)
        if player.projectile_type == "freeze_arrow":
            pygame.draw.rect(screen, GREEN, (1074, 180, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1074, 180, 37, 67), 3)
        if player.projectile_type == "poison_arrow":
            pygame.draw.rect(screen, GREEN, (1030, 260, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1030, 260, 37, 67), 3)
        if player.projectile_type == "fireball":
            pygame.draw.rect(screen, GREEN, (1074, 260, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1074, 260, 37, 67), 3)
        if player.projectile_type == "smart_arrow":
            pygame.draw.rect(screen, GREEN, (1029, 340, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1029, 340, 37, 67), 3)
        screen.blit(fontTiny.render('LVL 1', False, (0, 0, 0)), (1032, 168))
        pygame.draw.rect(screen, BLACK, (1030, 180, 37, 67), 3)
        screen.blit(pygame.image.load('data/image/arrow.png'), (1012, 180))

        screen.blit(fontTiny.render('LVL 3', False, (0, 0, 0)), (1074, 168))
        pygame.draw.rect(screen, BLACK, (1074, 180, 37, 67), 3)
        screen.blit(pygame.image.load('data/image/freeze_arrow.png'), (1057, 180))
        if player.level < 3:
            screen.blit(pygame.image.load('data/image/lock.png'), (1074, 180))

        screen.blit(fontTiny.render('LVL 5', False, (0, 0, 0)), (1032, 248))
        pygame.draw.rect(screen, BLACK, (1030, 260, 37, 67), 3)
        screen.blit(pygame.image.load('data/image/poison_arrow_0.png'), (1012, 258))
        if player.level < 5:
            screen.blit(pygame.image.load('data/image/lock.png'), (1030, 260))

        screen.blit(fontTiny.render('LVL 10', False, (0, 0, 0)), (1074, 248))
        pygame.draw.rect(screen, BLACK, (1074, 260, 37, 67), 3)
        screen.blit(pygame.image.load('data/image/fireball_0.png'), (1057, 258))
        if player.level < 10:
            screen.blit(pygame.image.load('data/image/lock.png'), (1074, 260))

        screen.blit(fontTiny.render('LVL 15', False, (0, 0, 0)), (1032, 328))
        pygame.draw.rect(screen, BLACK, (1029, 340, 37, 67), 3)
        screen.blit(pygame.image.load('data/image/smart_arrow.png'), (1012, 336))
        if player.level < 15:
            screen.blit(pygame.image.load('data/image/lock.png'), (1029, 340))

    def icon_clicks(self):
        mx, my = pygame.mouse.get_pos()
        # print 45-my
        # Check if mouse position is above the Profile icon, being clicked, and not visible
        if (1028 - mx) in range(-41, 0) and (45 - my) in range(-42, 0) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.DisabledProfile == False:
            print "Profile Click"
            if self.ClickProfile == False:
                self.ClickShop = False
                self.DisabledShop = False
                self.ClickProfile = True
            else:
                self.DisabledProfile = True
        # Check if mouse position is above the Shop icon, being clicked, and not visible
        if (1070 - mx) in range(-41, 0) and (45 - my) in range(-42, 0) and pygame.mouse.get_pressed() == (
        1, 0, 0) and self.DisabledShop == False:
            print "Shop Click"
            if self.ClickShop == False:
                self.ClickProfile = False
                self.DisabledProfile = False
                self.ClickShop = True
            else:
                self.DisabledShop = True

    def projectile_select(self):
        # Adds a green border to the projectile type selected
        if player.projectile_type == "arrow":
            pygame.draw.rect(screen, GREEN, (1030, 180, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1030, 180, 37, 67), 3)
        if player.projectile_type == "freeze_arrow":
            pygame.draw.rect(screen, GREEN, (1074, 180, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1074, 180, 37, 67), 3)
        if player.projectile_type == "poison_arrow":
            pygame.draw.rect(screen, GREEN, (1030, 260, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1030, 260, 37, 67), 3)
        if player.projectile_type == "fireball":
            pygame.draw.rect(screen, GREEN, (1074, 260, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1074, 260, 37, 67), 3)
        if player.projectile_type == "smart_arrow":
            pygame.draw.rect(screen, GREEN, (1029, 340, 37, 67), 3)
        else:
            pygame.draw.rect(screen, BLACK, (1029, 340, 37, 67), 3)
    """
    def update(self):
        self.display_text()
        self.projectile_select()
        self.ratio()
        self.profile()
    """

    def update(self):
        self.FPS_display()
        self.HP_display()
        self.SHOP_display()
        self.PROFILE()
        self.projectile()
        self.ratio()
        self.LVL()
        self.icon_clicks()
        self.purchase()

class Sound():
    def __init__(self):
        self.is_enemy = False
        self.is_player = False
        self.no_sound = pygame.mixer.Sound("data/sound/blank.wav")
        self.walking_sound = pygame.mixer.Sound("data/sound/walking.wav")
        self.dead_sound = pygame.mixer.Sound("data/sound/dead.wav")
        self.firing_sound = pygame.mixer.Sound("data/sound/firing.wav")
        self.hit_sound = pygame.mixer.Sound("data/sound/hit.wav")
        self.aiming_sound = pygame.mixer.Sound("data/sound/aiming.wav")
        self.BG = pygame.mixer.Sound("data/sound/BG.ogg")
        # the corresponding sound of a state
        self.sound_dict = {"standing_still": self.no_sound, "walking": self.walking_sound, "dead": self.dead_sound,
                           "fired_shot": self.firing_sound, "hit": self.hit_sound, "aiming": self.aiming_sound}
        # the possible previous states of the player character
        self.state_dict = {"standing_still": ["walking", "fired_shot", "aiming", "hit"],
                           "walking": ["standing_still", "fired_shot", "aiming", "hit"],
                           "aiming": ["standing_still", "walking"], "fired_shot": ["aiming"],
                           "hit": ["standing_still", "walking", "fire_shot", "aiming", "hit"], "dead": ["hit"]}

    def play_sound(self, past_state, state):
        # Plays a sound file according to the state of the enemy/player
        if past_state in self.state_dict[state]:
            try:
                self.sound_dict[state].play()
            except KeyError:
                pass


class Display():
    def startmenu_display(self, x, y):
        # Display startmenu and allows related actions
        # Takes in mouse x and y coordinates for button click
        screen.blit(Starting_Screen, (0, 0))

        global startmenu, helpmenu, pausegame
        if x in range(112, 219) and y in range(621, 649) and pygame.mouse.get_pressed() == (1, 0, 0):
            startmenu = False
            pausegame = False
        if x in range(113, 326) and y in range(658, 684) and pygame.mouse.get_pressed() == (1, 0, 0):
            helpmenu = True
            startmenu = False

    def helpmenu_display(self, x, y):
        # Display helpmenu and allows related actions
        # Takes in mouse x and y coordinates for button click
        screen.blit(how_to_play, (0, 0))
        global startmenu, helpmenu, pausegame
        if x in range(13, 88) and y in range(18, 89) and mouse_pressed == (1, 0, 0):
            helpmenu = False
            startmenu = True

    def pausegame_display(self, x, y):
        # Pauses the game
        # Takes in mouse x and y coordinates for button click
        global pausegame
        if x in range(1061, 1083) and y in range(694, 717) and mouse_pressed == (1, 0, 0):
            pausegame = not pausegame


""" Create objects, sprite groups and add class objects to related sprite groups"""
all_object_group = pygame.sprite.Group()
# Player
player_group = pygame.sprite.Group()
player = Player()
all_object_group.add(player)
player_group.add(player)
# Enemy
enemy_group = pygame.sprite.Group()
enemy = []
for i in range(4):
    enemy.append(Enemy())
    enemy_group.add(enemy[i])
    all_object_group.add(enemy[i])
# Background Map
map_group = pygame.sprite.Group()
map_bg = Map()
map_group.add(map_bg)
all_object_group.add(map_bg)
# Projectile
projectile_group = pygame.sprite.Group()
enemy_projectile_group = pygame.sprite.Group()
arrow = []
for i in range(50):  # Max 50 projectiles on screen
    arrow.append(Projectile("arrow"))
# Sound
sound = Sound()
channel0 = pygame.mixer.Channel(0)  # play background music indefinitely in a reserved channel
channel0.play(sound.BG, loops=-1)
# Info
info = Info()
# Display
display = Display()


"""Game States"""
# Preload images for different states of the game e.g. start_screen, how to play etc.
Starting_Screen = pygame.image.load("data/image/Intro_screen.png").convert()
how_to_play = pygame.image.load("data/image/how_to_play.png").convert()
pause_button = pygame.image.load("data/image/pause.png").convert_alpha()
rungame = True
startmenu = True
helpmenu = False
pausegame = True


def all_update():  # All the necessary updates when the game is running
    screen.fill(WHITE)
    screen.blit(pause_button, (0, 0))
    screen.blit(pause_button, (1052, 685))
    player.update()  # Update player class object
    for i in enemy:  # Update enemy class object
        i.update()
    global projectile_id  # Ensures that there is a maximum of only 49 projectiles class objects
    if projectile_id >= 49:
        all_object_group.remove(arrow[projectile_id])
        projectile_group.remove(arrow[projectile_id])
        projectile_id = 0
    for i in arrow:  # Update projectile class objects
        i.update()
    info.update()  # Update info class object
    all_object_group.draw(screen)

while rungame:  # Main game loop
    """All user inputs"""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rungame = False
    key_pressed = pygame.key.get_pressed()
    mouse_pressed = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    mx, my = pygame.mouse.get_pos()

    if startmenu:
        display.startmenu_display(mx, my)
    elif helpmenu:
        display.helpmenu_display(mx, my)
    else:
        display.pausegame_display(mx, my)
    if not pausegame:
        all_update()

    pygame.display.update()
    clock.tick(fps)

