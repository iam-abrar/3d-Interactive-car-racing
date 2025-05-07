from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
import sys

# Game states
STATE_MENU, STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER = 0, 1, 2, 3
game_state = STATE_MENU

# Game settings
window_w, window_h = 1000, 800
all_menu = ['Easy', 'Medium', 'Hard']
menu_index = 0
top_scores = [0, 0, 0]

# Player variables
player_pos = [0, 0, 0]
player_color = [0, 0.5, 1]  # Default blue color
score = 0
distance = 0  # Distance meter
fuel = 100  # Fuel system (0-100)
base_speed = 5
speed = base_speed
base_spawn_interval = 3.0
spawn_interval = base_spawn_interval
last_spawn_time = time.time()
last_frame_time = time.time()
track_z_offset = 0
obstacles = []
nitro_active = False
nitro_available = False
nitro_amount = 0
nitro_max = 100
shield_active = False
shield_end_time = 0
camera_mode = 0
object_rotation = 0
acceleration = 0
max_speed = 15

# Progressive difficulty
difficulty_increase_interval = 350  # Points needed to increase difficulty
next_difficulty_increase = difficulty_increase_interval
difficulty_level = 1
max_difficulty_level = 10
difficulties = {
    'Easy': {'speed': 2.0, 'spawn': 2.0, 'fuel_drain': 0.5, 'enemy_move_chance': 0.1},
    'Medium': {'speed': 3.0, 'spawn': 1.5, 'fuel_drain': 1.0, 'enemy_move_chance': 0.15},
    'Hard': {'speed': 4.0, 'spawn': 1.0, 'fuel_drain': 1.5, 'enemy_move_chance': 0.2},
}
enemy_move_timers = {}
enemy_lane_change_speeds = {}
SCORE_VALUES = {
    'distance': 10,  # per meter
    'blue_car': 100,
    'perks': 50
}


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def car_body_shape(color):
    glPushMatrix()
    # Main body
    glColor3f(*color)
    glPushMatrix()
    glScalef(60, 25, 30)  # length, height, width
    glutSolidCube(1)
    glPopMatrix()

    # Roof
    glColor3f(color[0] * 0.5, color[1] * 0.5, color[2] * 0.5)
    glPushMatrix()
    glTranslatef(0, 20, 0)
    glScalef(40, 10, 25)
    glutSolidCube(1)
    glPopMatrix()

    # Front bumper
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(35, 5, 0)
    glScalef(10, 10, 30)
    glutSolidCube(1)
    glPopMatrix()

    # Rear bumper
    glPushMatrix()
    glTranslatef(-35, 5, 0)
    glScalef(10, 10, 30)
    glutSolidCube(1)
    glPopMatrix()

    # Headlights
    glColor3f(1, 1, 0.8)
    glPushMatrix()
    glTranslatef(40, 10, 15)
    glutSolidSphere(3, 10, 10)
    glTranslatef(0, 0, -30)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()

    # Tail lights
    glColor3f(1, 0, 0)
    glPushMatrix()
    glTranslatef(-40, 10, 15)
    glutSolidSphere(3, 10, 10)
    glTranslatef(0, 0, -30)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()

    # Windows
    glColor4f(0.1, 0.1, 0.2, 0.5)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPushMatrix()
    glTranslatef(0, 25, 0)
    glScalef(35, 8, 25)
    glutSolidCube(1)
    glPopMatrix()
    glDisable(GL_BLEND)

    # Wheels
    wheel_positions = [(-30, -10, 20), (30, -10, 20), (-30, -10, -20), (30, -10, -20)]
    glColor3f(0.1, 0.1, 0.1)
    for (x, y, z) in wheel_positions:
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(90, 0, 1, 0)
        glutSolidTorus(4, 7, 10, 10)
        glPopMatrix()

    glPopMatrix()


def draw_player():
    glPushMatrix()
    try:
        # position the car
        glTranslatef(player_pos[0], 30, player_pos[2])

        if nitro_active:
            glColor3f(0, 0, 1)
        elif shield_active:
            glColor3f(1, 1, 0)
        else:
            glColor3fv(player_color)

        car_body_shape(player_color)

        if shield_active:
            glColor4f(1, 1, 0, 0.3)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glutWireSphere(50, 16, 16)
            glDisable(GL_BLEND)
    finally:
        glPopMatrix()


def road_track():
    glPushMatrix()
    try:
        for i in range(20):
            z = (i * -200 + track_z_offset) % 4000 - 2000

            # Road
            glColor3f(0.13, 0.23, 0.3)
            glPushMatrix()
            glTranslatef(0, -30, z)
            glScalef(500, 1, 200)
            glutSolidCube(1)
            glPopMatrix()

            # Road lines
            glColor3f(1, 1, 1)
            glPushMatrix()
            glTranslatef(0, -29.5, z)
            glScalef(10, 0.5, 20)
            for lane in range(-2, 3):
                glPushMatrix()
                glTranslatef(lane * 100, 0, 0)
                glutSolidCube(1)
                glPopMatrix()
            glPopMatrix()

            # Center line (dashed)
            glColor3f(1, 1, 0)
            glPushMatrix()
            glTranslatef(0, -29, z)
            for dash in range(-5, 5):
                glPushMatrix()
                glTranslatef(0, 0, dash * 40)
                glScalef(5, 0.5, 20)
                glutSolidCube(1)
                glPopMatrix()
            glPopMatrix()

            # Roadside grass
            glColor3f(0, 0.5, 0)
            glPushMatrix()
            glTranslatef(300, -30, z)
            glScalef(200, 1, 200)
            glutSolidCube(1)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(-300, -30, z)
            glScalef(200, 1, 200)
            glutSolidCube(1)
            glPopMatrix()

            if i % 2 == 0:
                for side in [-1, 1]:
                    glPushMatrix()
                    glTranslatef(side * 250, 0, z)

                    # Pole
                    glColor3f(0.2, 0.2, 0.2)
                    glPushMatrix()
                    glRotatef(90, 1, 0, 0)
                    glutSolidCylinder(3, 120, 10, 10)
                    glPopMatrix()

                    # Lamp arm
                    glPushMatrix()
                    glTranslatef(side * 20, 120, 0)
                    glRotatef(90, 0, 1, 0)
                    glutSolidCylinder(2, 30, 10, 10)
                    glPopMatrix()

                    # Lamp head
                    glColor3f(0.9, 0.9, 0.7)
                    glPushMatrix()
                    glTranslatef(side * 50, 120, 0)
                    glRotatef(90, 0, 1, 0)
                    glutSolidCylinder(8, 15, 10, 10)
                    glPopMatrix()

                    # Light glow
                    glColor4f(1, 1, 0.8, 0.3)
                    glEnable(GL_BLEND)
                    glPushMatrix()
                    glTranslatef(side * 65, 120, 0)
                    glScalef(40, 40, 40)
                    glutSolidSphere(1, 10, 10)
                    glPopMatrix()
                    glDisable(GL_BLEND)

                    glPopMatrix()

            # Bushes and plants (completely stable)
            if i % 5 == 0:
                for side in [-1, 1]:
                    glPushMatrix()
                    plant_z = z + (random.random() - 0.5) * 100
                    glTranslatef(side * (350 + random.random() * 50),
                                 -20 + random.random() * 10,
                                 plant_z)

                    # Bush base
                    glColor3f(0, 0.4 + random.random() * 0.3, 0)
                    glutSolidSphere(15 + random.random() * 10, 10, 10)

                    # Flowers (less frequent)
                    if random.random() > 0.7:
                        glColor3f(1, random.random(), 0)
                        glPushMatrix()
                        glTranslatef(0, 15, 0)
                        glutSolidSphere(5, 10, 10)
                        glPopMatrix()

                    glPopMatrix()
    finally:
        glPopMatrix()


def nitro_shape(x, y, z):
    glPushMatrix()
    try:
        glTranslatef(x, y, z)
        glRotatef(object_rotation, 0, 1, 0)

        # Bottle
        glColor3f(0.2, 0.2, 1)
        glPushMatrix()
        glTranslatef(0, 20, 0)
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(10, 30, 16, 16)
        glPopMatrix()

        # Bottle top
        glColor3f(0.8, 0.8, 0.8)
        glPushMatrix()
        glTranslatef(0, 50, 0)
        glutSolidSphere(8, 16, 16)
        glPopMatrix()

        # Liquid
        glColor4f(0, 0.5, 1, 0.7)
        glEnable(GL_BLEND)
        glPushMatrix()
        glTranslatef(0, 30, 0)
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(8, 20, 16, 16)
        glDisable(GL_BLEND)
        glPopMatrix()

        # Name label
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_w, 0, window_h)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        screen_pos = gluProject(x, y + 60, z)
        if screen_pos[2] < 1:
            draw_text(screen_pos[0] - 20, window_h - screen_pos[1], "NITRO")

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    finally:
        glPopMatrix()


def draw_shield(x, y, z):
    glPushMatrix()
    try:
        glTranslatef(x, y + 30, z)
        glRotatef(object_rotation, 0, 1, 0)

        glColor3f(1, 1, 0)
        glPushMatrix()
        glScalef(1.5, 2, 0.2)
        glutSolidSphere(15, 16, 16)
        glPopMatrix()

        glColor3f(0.5, 0.5, 0)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex3f(-15, 0, 0.1)
        glVertex3f(15, 0, 0.1)
        glVertex3f(0, -20, 0.1)
        glVertex3f(0, 20, 0.1)
        glEnd()

        # Name label
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_w, 0, window_h)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        screen_pos = gluProject(x, y + 60, z)
        if screen_pos[2] < 1:
            draw_text(screen_pos[0] - 25, window_h - screen_pos[1], "SHIELD")

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    finally:
        glPopMatrix()


def fuel_can_shape(x, y, z):
    glPushMatrix()
    try:
        glTranslatef(x, y, z)
        glRotatef(object_rotation, 0, 1, 0)

        # Can body
        glColor3f(0.8, 0.5, 0)
        glPushMatrix()
        glTranslatef(0, 20, 0)
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(15, 30, 16, 16)
        glPopMatrix()

        # Can top
        glColor3f(0.5, 0.5, 0.5)
        glPushMatrix()
        glTranslatef(0, 50, 0)
        glutSolidSphere(10, 16, 16)
        glPopMatrix()

        # Label
        glColor3f(1, 0, 0)
        glBegin(GL_LINES)
        glVertex3f(-15, 30, 15.1)
        glVertex3f(15, 30, 15.1)
        glVertex3f(0, 20, 15.1)
        glVertex3f(0, 40, 15.1)
        glEnd()

        # Name label
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_w, 0, window_h)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        screen_pos = gluProject(x, y + 60, z)
        if screen_pos[2] < 1:
            draw_text(screen_pos[0] - 20, window_h - screen_pos[1], "FUEL")

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    finally:
        glPopMatrix()


def obstacles_design():
    for o in obstacles:
        if o['type'] == 'red':
            # Red enemy car
            glPushMatrix()
            glTranslatef(o['x'], 30, o['z'])
            car_body_shape([1, 0, 0])  # Red color

            # Name label
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluOrtho2D(0, window_w, 0, window_h)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()

            screen_pos = gluProject(o['x'], 90, o['z'])
            if screen_pos[2] < 1:
                draw_text(screen_pos[0] - 25, window_h - screen_pos[1], "DANGER")

            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)

            glPopMatrix()
        elif o['type'] == 'blue':
            # Blue point car
            glPushMatrix()
            glTranslatef(o['x'], 30, o['z'])
            car_body_shape([0, 0, 1])  # Blue color

            # Name label
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluOrtho2D(0, window_w, 0, window_h)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()

            screen_pos = gluProject(o['x'], 90, o['z'])
            if screen_pos[2] < 1:
                draw_text(screen_pos[0] - 15, window_h - screen_pos[1], "+10")

            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)

            glPopMatrix()
        elif o['type'] == 'nitro':
            nitro_shape(o['x'], 30, o['z'])
        elif o['type'] == 'shield':
            draw_shield(o['x'], 30, o['z'])
        elif o['type'] == 'fuel':
            fuel_can_shape(o['x'], 30, o['z'])


def hud_info():
    # Score
    draw_text(10, 770, f"Score: {score}")

    # Distance
    dist_text = f"{distance:.0f}m" if distance < 1000 else f"{distance / 1000:.1f}km"
    draw_text(10, 740, f"Distance: {dist_text}")

    # Speed
    draw_text(10, 710, f"Speed: {round(speed, 1)}")

    # Fuel gauge
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(10, 680)
    glVertex2f(110, 680)
    glVertex2f(110, 670)
    glVertex2f(10, 670)
    glEnd()

    glColor3f(0, 1, 0) if fuel > 20 else glColor3f(1, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(10, 680)
    glVertex2f(10 + fuel, 680)
    glVertex2f(10 + fuel, 670)
    glVertex2f(10, 670)
    glEnd()

    glColor3f(1, 1, 1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(10, 680)
    glVertex2f(110, 680)
    glVertex2f(110, 670)
    glVertex2f(10, 670)
    glEnd()

    draw_text(115, 670, f"{fuel:.0f}%")

    # Nitro gauge
    glColor3f(0.2, 0.2, 0.4)
    glBegin(GL_QUADS)
    glVertex2f(10, 650)
    glVertex2f(110, 650)
    glVertex2f(110, 640)
    glVertex2f(10, 640)
    glEnd()

    glColor3f(0, 0, 1) if nitro_amount > 20 else glColor3f(0.5, 0.5, 1)
    glBegin(GL_QUADS)
    glVertex2f(10, 650)
    glVertex2f(10 + nitro_amount, 650)
    glVertex2f(10 + nitro_amount, 640)
    glVertex2f(10, 640)
    glEnd()

    glColor3f(1, 1, 1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(10, 650)
    glVertex2f(110, 650)
    glVertex2f(110, 640)
    glVertex2f(10, 640)
    glEnd()

    draw_text(115, 640, f"NITRO: {nitro_amount:.0f}%")

    # Active power-ups
    if shield_active:
        remaining = max(0, shield_end_time - time.time())
        draw_text(10, 620, f"Shield: {remaining:.1f}s")

    # Difficulty level
    draw_text(10, 590, f"Level: {difficulty_level}/{max_difficulty_level}")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90, window_w / window_h, 1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == 0:
        gluLookAt(player_pos[0], 150, player_pos[2] + 300,
                  player_pos[0], 0, player_pos[2],
                  0, 1, 0)
    else:
        gluLookAt(player_pos[0], 50, player_pos[2] + 30,
                  player_pos[0], 50, player_pos[2] - 300,
                  0, 1, 0)


def update_obstacles(dt):
    global obstacles, enemy_move_timers, enemy_lane_change_speeds

    new_obstacles = []
    for o in obstacles:
        o['z'] += speed * 200 * dt

        if o['type'] in ['red', 'blue']:
            if id(o) not in enemy_move_timers:
                enemy_move_timers[id(o)] = time.time() + random.uniform(0.5, 1.5)
                enemy_lane_change_speeds[id(o)] = random.uniform(1.0, 3.0)

            if time.time() > enemy_move_timers[id(o)]:
                base_chance = difficulties[all_menu[menu_index]]['enemy_move_chance']
                level_bonus = (difficulty_level / max_difficulty_level) * 0.05
                total_chance = min(base_chance + level_bonus, 0.25)  # Higher cap for red cars

                if random.random() < total_chance:
                    possible_lanes = [-100, 0, 100]
                    if o['x'] in possible_lanes:
                        possible_lanes.remove(o['x'])

                    # Red cars aggressively move toward player
                    if o['type'] == 'red':
                        # Find lane closest to player with higher probability
                        if random.random() < 0.7:  # 70% chance to move toward player
                            target_x = min(possible_lanes, key=lambda x: abs(x - player_pos[0]))
                        else:
                            target_x = random.choice(possible_lanes)
                    else:  # blue car moves away
                        if random.random() < 0.7:  # 70% chance to move away
                            target_x = max(possible_lanes, key=lambda x: abs(x - player_pos[0]))
                        else:
                            target_x = random.choice(possible_lanes)

                    o['target_x'] = target_x
                    o['original_x'] = o['x']
                    o['lane_change_start'] = time.time()
                    o['lane_change_duration'] = random.uniform(0.5, 1.5) / enemy_lane_change_speeds[id(o)]

                enemy_move_timers[id(o)] = time.time() + random.uniform(0.5, 1.5)

            if 'target_x' in o and o['target_x'] is not None:
                elapsed = time.time() - o['lane_change_start']
                progress = min(elapsed / o['lane_change_duration'], 1.0)
                progress = progress * progress * (3 - 2 * progress)
                o['x'] = o['original_x'] + (o['target_x'] - o['original_x']) * progress
                if progress >= 1.0:
                    o['x'] = o['target_x']
                    o['target_x'] = None

        if o['z'] < 300:
            new_obstacles.append(o)
        else:
            if id(o) in enemy_move_timers:
                del enemy_move_timers[id(o)]
            if id(o) in enemy_lane_change_speeds:
                del enemy_lane_change_speeds[id(o)]

    obstacles[:] = new_obstacles


def spawn_obstacle():
    global last_spawn_time

    if time.time() - last_spawn_time >= spawn_interval:
        # Spawn cars and perks - adjusted weights
        kind = random.choices(
            ['red', 'blue', 'nitro', 'shield', 'fuel'],
            weights=[0.4, 0.3, 0.1, 0.1, 0.1]
        )[0]

        lane = random.choice([-100, 0, 100])
        obstacles.append({
            'x': lane,
            'z': player_pos[2] - 1000,
            'type': kind,
            'original_x': lane,
            'target_x': None
        })
        last_spawn_time = time.time()


def check_collisions():
    global obstacles, score, nitro_active, nitro_available, nitro_amount
    global shield_active, shield_end_time, speed, game_state, fuel
    global acceleration

    new_obs = []
    for o in obstacles:
        if abs(o['x'] - player_pos[0]) < 60 and abs(o['z'] - player_pos[2]) < 60:
            if o['type'] == 'red':
                if not shield_active:
                    end_game()
                    return
            elif o['type'] == 'blue':
                score += SCORE_VALUES['blue_car']
            elif o['type'] == 'nitro':
                nitro_available = True
                nitro_amount = min(nitro_max, nitro_amount + 50)
                score += SCORE_VALUES['perks']
            elif o['type'] == 'shield':
                shield_active = True
                shield_end_time = time.time() + 7
                score += SCORE_VALUES['perks']
            elif o['type'] == 'fuel':
                fuel = min(100, fuel + 30)
                score += SCORE_VALUES['perks']
            continue
        new_obs.append(o)
    obstacles[:] = new_obs


def update():
    global track_z_offset, last_frame_time, score, speed, distance, fuel
    global nitro_active, nitro_amount, shield_active, object_rotation, spawn_interval
    global next_difficulty_increase, difficulty_level, acceleration, max_speed

    now = time.time()
    dt = now - last_frame_time
    last_frame_time = now

    object_rotation = (object_rotation + 60 * dt) % 360

    if game_state == STATE_PLAYING:
        # Fuel-based acceleration
        if fuel > 0:
            acceleration = 0.1 * (fuel / 100)  # More fuel = faster acceleration
            speed = min(max_speed, speed + acceleration * dt)
        else:
            speed = max(0, speed - 2 * dt)  # Slow down when out of fuel

        distance += speed * dt * 10
        score += int(SCORE_VALUES['distance'] * speed * dt * 5)

        # Fuel consumption based on speed
        fuel_consumption = difficulties[all_menu[menu_index]]['fuel_drain'] * (1 + speed / max_speed)
        fuel -= fuel_consumption * dt

        if fuel <= 0:
            end_game()
            return

        # Progressive difficulty
        if score >= next_difficulty_increase and difficulty_level < max_difficulty_level:
            difficulty_level += 1
            max_speed += 1  # Increase max speed
            spawn_interval = max(0.5, spawn_interval - 0.1)
            next_difficulty_increase += difficulty_increase_interval

        track_z_offset += speed * 100 * dt

        # Handle nitro
        if nitro_active and nitro_amount > 0:
            nitro_amount -= 40 * dt  # Faster nitro consumption
            speed = min(max_speed * 1.5, speed + 1 * dt)  # Bigger boost
            if nitro_amount <= 0:
                nitro_amount = 0
                nitro_active = False
        elif not nitro_active and nitro_amount < nitro_max and nitro_available:
            nitro_amount = min(nitro_max, nitro_amount + 15 * dt)  # Faster recharge

        if shield_active and time.time() > shield_end_time:
            shield_active = False

        update_obstacles(dt)
        spawn_obstacle()
        check_collisions()

    glutPostRedisplay()
    glutTimerFunc(16, lambda x: update(), 0)


def end_game():
    global game_state, top_scores, score
    game_state = STATE_GAME_OVER
    top_scores.append(score)
    top_scores = list(set(top_scores))
    top_scores.sort(reverse=True)
    top_scores[:] = top_scores[:3]


def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, window_w, window_h)
    setup_camera()

    if game_state == STATE_MENU:
        # Menu screen
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_w, 0, window_h)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        draw_text(400, 700, "Select Difficulty with ↑ ↓, Press Enter", GLUT_BITMAP_TIMES_ROMAN_24)
        for i, opt in enumerate(all_menu):
            prefix = "▶ " if i == menu_index else "   "
            draw_text(400, 650 - i * 40, f"{prefix}{opt}", GLUT_BITMAP_HELVETICA_18)

        draw_text(400, 480, "Top Scores:", GLUT_BITMAP_TIMES_ROMAN_24)
        for i, s in enumerate(top_scores):
            draw_text(400, 440 - i * 30, f"{i + 1}. {s}", GLUT_BITMAP_HELVETICA_18)

        draw_text(400, 300, "Controls:", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(400, 270, "A/D - Move Left/Right", GLUT_BITMAP_HELVETICA_18)
        draw_text(400, 240, "W/S - Nitro/Brake", GLUT_BITMAP_HELVETICA_18)
        draw_text(400, 210, "C - Change Camera", GLUT_BITMAP_HELVETICA_18)
        draw_text(400, 180, "P - Pause Game", GLUT_BITMAP_HELVETICA_18)

        # draw_text(40, 30, ":", GLUT_BITMAP_TIMES_ROMAN_24)
        # draw_text(40, 20, " - Move Left/Right", GLUT_BITMAP_HELVETICA_18)
        # draw_text(40, 20,  - Nitro/Brake", GLUT_BITMAP_HELVETICA_18)
        # draw_text(40, 20,- Change Camera", GLUT_BITMAP_HELVETICA_18)
        # draw_text(40, 10,  - Pause Game", GLUT_BITMAP_HELVETICA_18)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    elif game_state in [STATE_PLAYING, STATE_PAUSED]:
        # Game screen
        road_track()
        draw_player()
        obstacles_design()
        hud_info()

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_w, 0, window_h)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        if game_state == STATE_PLAYING:
            draw_text(900, 30, "Pause: P")
        else:
            draw_text(900, 30, "Play: P")

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        if game_state == STATE_PAUSED:
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluOrtho2D(0, window_w, 0, window_h)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()

            glColor4f(0, 0, 0, 0.7)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBegin(GL_QUADS)
            glVertex2f(0, 0)
            glVertex2f(window_w, 0)
            glVertex2f(window_w, window_h)
            glVertex2f(0, window_h)
            glEnd()
            glDisable(GL_BLEND)

            draw_text(450, 500, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
            draw_text(400, 450, f"Score: {score}")
            draw_text(400, 420, f"Distance: {distance:.0f}m")
            draw_text(400, 390, "Press P to continue")

            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)

    elif game_state == STATE_GAME_OVER:
        # Game over screen
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_w, 0, window_h)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # # Dark overlay
        # glColor4f(0, 0, 0, 0.8)
        # glEnable(GL_BLEND)
        # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glBegin(GL_QUADS)
        # glVertex2f(0, 0)
        # glVertex2f(window_w, 0)
        # glVertex2f(window_w, window_h)
        # glVertex2f(0, window_h)
        # glEnd()
        # glDisable(GL_BLEND)

        # Game over text
        draw_text(420, 600, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(400, 550, f"Your Score: {score}", GLUT_BITMAP_HELVETICA_18)

        draw_text(400, 500, "Top Scores:", GLUT_BITMAP_TIMES_ROMAN_24)
        for i, s in enumerate(top_scores):
            draw_text(400, 470 - i * 30, f"{i + 1}. {s}", GLUT_BITMAP_HELVETICA_18)

        draw_text(400, 400, "Press R to Restart", GLUT_BITMAP_HELVETICA_18)
        draw_text(400, 370, "Press M for Menu", GLUT_BITMAP_HELVETICA_18)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    glutSwapBuffers()


def keyboard(key, x, y):
    global player_pos, camera_mode, game_state, fuel, menu_index
    global nitro_active, nitro_available, speed, acceleration

    key = key.decode('utf-8').lower()

    if game_state == STATE_MENU:
        if key in ['\r', '\n']:  # Enter key
            start_game_with(all_menu[menu_index])
    elif game_state == STATE_PLAYING:
        if key == 'a':
            player_pos[0] = max(-200, player_pos[0] - 100)
        elif key == 'd':
            player_pos[0] = min(200, player_pos[0] + 100)
        elif key == 'c':
            camera_mode = 1 - camera_mode
        elif key == 'p':
            game_state = STATE_PAUSED
        elif key == 'w':
            # Activate nitro only if available and not already active
            if nitro_amount > 0 and not nitro_active and nitro_available:
                nitro_active = True
        elif key == 's':
            # Brake (slow down)
            speed = max(base_speed, speed * 0.7)
    elif game_state == STATE_PAUSED:
        if key == 'p':
            game_state = STATE_PLAYING
    elif game_state == STATE_GAME_OVER:
        if key == 'r':
            reset_game()
        elif key == 'm':
            reset_to_menu()


def keyboard_up(key, x, y):
    global nitro_active

    key = key.decode('utf-8').lower()

    if key == 'w' and nitro_active:
        nitro_active = False


def special_keys(key, x, y):
    global menu_index
    if game_state == STATE_MENU:
        if key == GLUT_KEY_UP:
            menu_index = (menu_index - 1) % len(all_menu)
        elif key == GLUT_KEY_DOWN:
            menu_index = (menu_index + 1) % len(all_menu)
        glutPostRedisplay()


def start_game_with(difficulty_name):
    global base_speed, speed, base_spawn_interval, spawn_interval, game_state
    global player_pos, score, obstacles, nitro_active, shield_active
    global track_z_offset, camera_mode, player_color, distance, fuel
    global next_difficulty_increase, enemy_move_timers, difficulty_level
    global nitro_available, nitro_amount, max_speed, acceleration

    settings = difficulties[difficulty_name]
    base_speed = settings['speed']
    speed = base_speed
    max_speed = base_speed * 2
    base_spawn_interval = settings['spawn']
    spawn_interval = base_spawn_interval
    player_pos = [0, 0, 0]
    player_color = [0, 0.5, 1]
    score = 0
    distance = 0
    fuel = 100
    obstacles.clear()
    nitro_active = False
    nitro_available = False
    nitro_amount = 0
    shield_active = False
    track_z_offset = 0
    camera_mode = 0
    next_difficulty_increase = difficulty_increase_interval
    difficulty_level = 1
    enemy_move_timers = {}
    acceleration = 0
    game_state = STATE_PLAYING


def reset_game():
    global game_state, player_pos, score, distance, fuel, obstacles
    global nitro_active, shield_active, track_z_offset, difficulty_level
    global next_difficulty_increase, enemy_move_timers, enemy_lane_change_speeds
    global nitro_available, nitro_amount, max_speed, acceleration

    if game_state in [STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER]:
        player_pos = [0, 0, 0]
        score = 0
        distance = 0
        fuel = 100
        obstacles = []
        nitro_active = False
        nitro_available = False
        nitro_amount = 0
        shield_active = False
        track_z_offset = 0
        difficulty_level = 1
        next_difficulty_increase = difficulty_increase_interval
        enemy_move_timers = {}
        enemy_lane_change_speeds = {}
        acceleration = 0
        game_state = STATE_PLAYING


def reset_to_menu():
    global game_state, menu_index
    game_state = STATE_MENU
    menu_index = 0


def init():
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.1, 0.1, 0.1, 1)


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_w, window_h)
    glutCreateWindow(b"Enhanced 3D Racing Game")
    init()
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_keys)
    glutTimerFunc(0, lambda x: update(), 0)
    glutMainLoop()


if __name__ == "__main__":
    main()