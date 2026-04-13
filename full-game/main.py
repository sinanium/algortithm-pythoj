import pygame
import math
import random

# fix sound delay issues
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 700, 500
TILE_SIZE = 50
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My game 101")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 60)

# colors
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
GOLD = (255, 215, 0)

# helper to load images without crashing if they are missing
def load_img(name, size):
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.scale(img, size)
    except Exception:
        print(f"Couldn't load '{name}' - using a magenta box instead")
        surf = pygame.Surface(size)
        surf.fill((200, 0, 200)) 
        return surf

player_img = load_img("player.png", (60, 35))
enemy_img  = load_img("enemy.png", (60, 35))

# load background music
try:
    pygame.mixer.music.load("music2.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except Exception:
    print("Music file missing, playing in silence")


# map layouts (1 = wall, 0 = floor, P = player spawn, G = goal)
LEVELS = [
    [
        "11111111111111",
        "1P000010000001",
        "10110001101101",
        "10000100000001",
        "10110111101101",
        "10000000001001",
        "111101111010G1",
        "11111111111111"
    ],
    [
        "11111111111111",
        "10000100000001",
        "1010P101111001",
        "10100000001001",
        "10111111101001",
        "10000000101001",
        "101111000000G1",
        "11111111111111"
    ]
]


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.lifetime = 20

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), 3)


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 35, 35)
        self.speed = 4

    def move(self, dx, dy, walls):
        # move x, then check collisions
        self.rect.x += dx * self.speed
        for w in walls:
            if self.rect.colliderect(w):
                if dx > 0: self.rect.right = w.left
                if dx < 0: self.rect.left = w.right
                
        # move y, then check collisions
        self.rect.y += dy * self.speed
        for w in walls:
            if self.rect.colliderect(w):
                if dy > 0: self.rect.bottom = w.top
                if dy < 0: self.rect.top = w.bottom

    def draw(self, surface):
        surface.blit(player_img, self.rect)


class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 35, 35)
        self.hp = 5
        self.max_hp = 5
        self.speed = 1.7

    def update(self, target_rect, walls):
        # find direction to player
        dx = target_rect.x - self.rect.x
        dy = target_rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        
        if dist != 0:
            dx, dy = dx/dist, dy/dist
            
            # move and slide against walls
            self.rect.x += dx * self.speed
            for w in walls:
                if self.rect.colliderect(w):
                    if dx > 0: self.rect.right = w.left
                    if dx < 0: self.rect.left = w.right
                    
            self.rect.y += dy * self.speed
            for w in walls:
                if self.rect.colliderect(w):
                    if dy > 0: self.rect.bottom = w.top
                    if dy < 0: self.rect.top = w.bottom

    def draw(self, surface):
        surface.blit(enemy_img, self.rect)
        # health bar
        pygame.draw.rect(surface, BLACK, (self.rect.x, self.rect.y - 8, self.rect.width, 4))
        health_width = self.rect.width * (self.hp / self.max_hp)
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 8, health_width, 4))


def setup_level(level_index):
    walls = []
    enemies = []
    start_pos = [60, 60]
    goal_rect = pygame.Rect(0, 0, 30, 30)
    
    layout = LEVELS[level_index]
    floor_tiles = []
    
    # parse the text grid
    for r, row in enumerate(layout):
        for c, char in enumerate(row):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            
            if char == "1":
                walls.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
            elif char == "P":
                start_pos = [x + 7, y + 7]
            elif char == "G":
                goal_rect = pygame.Rect(x + 10, y + 10, 30, 30)
            elif char == "0":
                floor_tiles.append((x, y))

    # spawn enemies randomly on floor tiles
    enemy_spawns = random.sample(floor_tiles, min(len(floor_tiles), 4))
    for sx, sy in enemy_spawns:
        enemies.append(Enemy(sx + 7, sy + 7))
        
    return Player(start_pos[0], start_pos[1]), enemies, walls, goal_rect


# global game state
current_level = 0
player, enemies, walls, prize = setup_level(current_level)
bullets = []
particles = []

game_won = False
player_dead = False
running = True

while running:
    screen.fill((220, 220, 220))
    
    # handle inputs and events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and not (game_won or player_dead):
            mx, my = pygame.mouse.get_pos()
            dx = mx - player.rect.centerx
            dy = my - player.rect.centery
            dist = math.hypot(dx, dy)
            
            if dist != 0:
                bullets.append({
                    "pos": [player.rect.centerx, player.rect.centery], 
                    "dir": [dx/dist, dy/dist]
                })
                
        # restart game
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            current_level = 0
            player, enemies, walls, prize = setup_level(current_level)
            game_won = False
            player_dead = False
            bullets.clear()
            particles.clear()
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)

    # game logic
    if not game_won and not player_dead:
        keys = pygame.key.get_pressed()
        move_x = keys[pygame.K_d] - keys[pygame.K_a]
        move_y = keys[pygame.K_s] - keys[pygame.K_w]
        player.move(move_x, move_y, walls)

        # update bullets
        for b in bullets[:]:
            b["pos"][0] += b["dir"][0] * 12
            b["pos"][1] += b["dir"][1] * 12
            bullet_rect = pygame.Rect(b["pos"][0]-3, b["pos"][1]-3, 6, 6)
            
            # hit wall
            hit_wall = any(bullet_rect.colliderect(w) for w in walls)
            if hit_wall:
                bullets.remove(b)
                continue
                
            # hit enemy
            for e in enemies[:]:
                if bullet_rect.colliderect(e.rect):
                    e.hp -= 1
                    if b in bullets:
                        bullets.remove(b)
                        
                    if e.hp <= 0:
                        for _ in range(12):
                            particles.append(Particle(e.rect.centerx, e.rect.centery))
                        enemies.remove(e)
                    break

        # update enemies
        for e in enemies:
            e.update(player.rect, walls)
            if e.rect.colliderect(player.rect): 
                player_dead = True
                pygame.mixer.music.stop()
        
        # level completion
        if player.rect.colliderect(prize):
            if current_level < len(LEVELS) - 1:
                current_level += 1
                player, enemies, walls, prize = setup_level(current_level)
                bullets.clear()
                particles.clear()
            else:
                game_won = True

    # rendering
    for w in walls:
        pygame.draw.rect(screen, (80, 80, 80), w)
        
    pygame.draw.rect(screen, GOLD, prize)
    
    for e in enemies:
        e.draw(screen)
        
    for b in bullets:
        pygame.draw.circle(screen, BLACK, (int(b["pos"][0]), int(b["pos"][1])), 4)
        
    for p in particles[:]: 
        p.update()
        p.draw(screen)
        if p.lifetime <= 0:
            particles.remove(p)
            
    player.draw(screen)

    # UI overlays
    if player_dead:
        screen.blit(big_font.render("YOU DIED!", True, RED), (WIDTH//2 - 110, HEIGHT//2 - 40))
        screen.blit(font.render("Press 'R' to Restart", True, BLACK), (WIDTH//2 - 95, HEIGHT//2 + 20))
    elif game_won:
        screen.blit(big_font.render("VICTORY!", True, GREEN), (WIDTH//2 - 100, HEIGHT//2 - 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()