# ----- [FULL CORRECTED CODE] -----
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
import math
import sys

# Game states
STATE_MENU, STATE_PLAYING, STATE_GAME_OVER = 0, 1, 2
game_state = STATE_MENU

# Game settings
window_width, window_height = 1000, 800
menu_options = ['Easy', 'Medium', 'Hard']
menu_index = 0
top_scores = [0, 0, 0]

# Player variables
player_pos = [0, 0, 0]
player_color = [0, 0.5, 1]  # Default blue color
score = 0
distance = 0  # Distance meter
fuel = 100  # Fuel system (0-100)
base_speed = 2
speed = base_speed
base_spawn_interval = 2.0
spawn_interval = base_spawn_interval
last_spawn_time = time.time()
last_frame_time = time.time()
track_z_offset = 0
obstacles = []
nitro_active = False
shield_active = False
nitro_end_time = 0
shield_end_time = 0
camera_mode = 0
object_rotation = 0

# Progressive difficulty
difficulty_increase_interval = 1000
next_difficulty_increase = difficulty_increase_interval

# Enemy AI settings
enemy_move_timers = {}

difficulties = {
    'Easy': {'speed': 2.0, 'spawn': 2.5, 'fuel_drain': 0.2, 'enemy_move_chance': 0.01},
    'Medium': {'speed': 3.0, 'spawn': 1.8, 'fuel_drain': 0.3, 'enemy_move_chance': 0.03},
    'Hard': {'speed': 4.0, 'spawn': 1.2, 'fuel_drain': 0.4, 'enemy_move_chance': 0.05}
}


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
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


def draw_player():
    glPushMatrix()
    try:
        glTranslatef(player_pos[0], 30, player_pos[2])

        if nitro_active:
            glColor3f(0, 0, 1)
        elif shield_active:
            glColor3f(1, 1, 0)
        else:
            glColor3fv(player_color)

        glutSolidCube(60)

        if shield_active:
            glColor4f(1, 1, 0, 0.3)  # Corrected to 4 components
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glutWireSphere(40, 16, 16)
            glDisable(GL_BLEND)
    finally:
        glPopMatrix()


def draw_track():
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    try:
        for i in range(10):
            z = (i * -200 + track_z_offset) % 2000 - 1000
            glPushMatrix()
            glTranslatef(0, -30, z)
            glScalef(300, 1, 200)
            glutSolidCube(1)
            glPopMatrix()
    finally:
        glPopMatrix()


def draw_nitro(x, y, z):
    glPushMatrix()
    try:
        glTranslatef(x, y, z)
        glRotatef(object_rotation, 0, 1, 0)

        glColor3f(0, 0.5, 1)
        glPushMatrix()
        glTranslatef(0, 30, 0)
        glScalef(1, 2, 1)
        glutSolidSphere(20, 16, 16)
        glPopMatrix()

        glColor3f(0.7, 0.7, 1)
        glPushMatrix()
        glTranslatef(0, 50, 0)
        glScalef(0.7, 0.5, 0.7)
        glutSolidSphere(10, 16, 16)
        glPopMatrix()
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
    finally:
        glPopMatrix()


def draw_fuel_can(x, y, z):
    glPushMatrix()
    try:
        glTranslatef(x, y, z)
        glRotatef(object_rotation, 0, 1, 0)

        glColor3f(0.8, 0.5, 0)
        glPushMatrix()
        glTranslatef(0, 20, 0)
        glScalef(1, 1.5, 0.5)
        glutSolidCube(30)
        glPopMatrix()

        glColor3f(1, 1, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex3f(-10, 25, 15.1)
        glVertex3f(10, 25, 15.1)
        glVertex3f(0, 15, 15.1)
        glVertex3f(0, 35, 15.1)
        glEnd()
    finally:
        glPopMatrix()


def draw_obstacles():
    for o in obstacles:
        if o['type'] == 'green':
            glPushMatrix()
            glTranslatef(o['x'], 30, o['z'])
            glColor3f(0, 1, 0)
            glutSolidCube(60)
            glPopMatrix()
        elif o['type'] == 'red':
            glPushMatrix()
            glTranslatef(o['x'], 30, o['z'])
            glColor3f(1, 0, 0)
            glutSolidCube(60)
            glPopMatrix()
        elif o['type'] == 'nitro':
            draw_nitro(o['x'], 30, o['z'])
        elif o['type'] == 'shield':
            draw_shield(o['x'], 30, o['z'])
        elif o['type'] == 'fuel':
            draw_fuel_can(o['x'], 30, o['z'])


def draw_hud():
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
    gluOrtho2D(0, window_width, 0, window_height)
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

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90, window_width / window_height, 1, 2000)
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


def update():
    global track_z_offset, last_frame_time, score, speed, distance, fuel
    global nitro_active, shield_active, object_rotation, spawn_interval
    global next_difficulty_increase

    now = time.time()
    dt = now - last_frame_time
    last_frame_time = now

    object_rotation = (object_rotation + 60 * dt) % 360

    if game_state == STATE_PLAYING:
        distance += speed * dt * 10
        fuel -= difficulties[menu_options[menu_index]]['fuel_drain'] * dt

        if fuel <= 0:
            end_game()
            return

        if score >= next_difficulty_increase:
            spawn_interval = max(0.5, spawn_interval - 0.1)
            next_difficulty_increase += difficulty_increase_interval

        track_z_offset += speed * 100 * dt
        score += int(speed * dt * 10)

        if nitro_active and time.time() > nitro_end_time:
            nitro_active = False
            speed /= 1.5
        if shield_active and time.time() > shield_end_time:
            shield_active = False

        update_obstacles(dt)
        spawn_obstacle()
        check_collisions()

    glutPostRedisplay()
    glutTimerFunc(16, lambda x: update(), 0)


def update_obstacles(dt):
    global obstacles, enemy_move_timers

    new_obstacles = []
    for o in obstacles:
        o['z'] += speed * 100 * dt

        if o['type'] == 'red':
            if id(o) not in enemy_move_timers:
                enemy_move_timers[id(o)] = time.time() + random.uniform(1, 3)

            if time.time() > enemy_move_timers[id(o)]:
                if random.random() < difficulties[menu_options[menu_index]]['enemy_move_chance']:
                    target_x = random.choice([-100, 0, 100])
                    o['x'] += (target_x - o['x']) * 0.1 * dt * 60
                enemy_move_timers[id(o)] = time.time() + random.uniform(1, 3)

        if o['z'] < 300:
            new_obstacles.append(o)
        else:
            if id(o) in enemy_move_timers:
                del enemy_move_timers[id(o)]

    obstacles[:] = new_obstacles


def spawn_obstacle():
    global last_spawn_time

    if time.time() - last_spawn_time >= spawn_interval:
        kind = random.choices(
            ['green', 'red', 'nitro', 'shield', 'fuel'],
            weights=[0.35, 0.35, 0.1, 0.1, 0.1]
        )[0]

        lane = random.choice([-100, 0, 100])
        obstacles.append({
            'x': lane,
            'z': player_pos[2] - 1000,
            'type': kind,
            'original_x': lane
        })
        last_spawn_time = time.time()


def check_collisions():
    global obstacles, score, nitro_active, nitro_end_time
    global shield_active, shield_end_time, speed, game_state, fuel

    new_obs = []
    for o in obstacles:
        if abs(o['x'] - player_pos[0]) < 60 and abs(o['z'] - player_pos[2]) < 60:
            if o['type'] == 'green':
                score += 50
            elif o['type'] == 'red':
                if not shield_active:
                    end_game()
                    return
            elif o['type'] == 'nitro':
                nitro_active = True
                nitro_end_time = time.time() + 5
                speed *= 1.5
            elif o['type'] == 'shield':
                shield_active = True
                shield_end_time = time.time() + 5
            elif o['type'] == 'fuel':
                fuel = min(100, fuel + 25)
            continue
        new_obs.append(o)
    obstacles[:] = new_obs


def end_game():
    global game_state, top_scores, score
    top_scores.append(score)
    top_scores.sort(reverse=True)
    top_scores = top_scores[:3]
    game_state = STATE_GAME_OVER


def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, window_width, window_height)
    setup_camera()

    if game_state == STATE_MENU:
        draw_text(400, 700, "Select Difficulty with ↑ ↓, Press Enter")
        for i, opt in enumerate(menu_options):
            prefix = "▶ " if i == menu_index else "   "
            draw_text(400, 650 - i * 40, f"{prefix}{opt}")
        draw_text(400, 500, "Top Scores:")
        for i, s in enumerate(top_scores):
            draw_text(400, 470 - i * 30, f"{i + 1}. {s}")

    elif game_state == STATE_PLAYING:
        draw_track()
        draw_player()
        draw_obstacles()
        draw_hud()

    elif game_state == STATE_GAME_OVER:
        draw_text(420, 400, "GAME OVER")
        draw_text(380, 360, f"Your Score: {score}")
        draw_text(350, 320, "Press 'R' to Restart")

    glutSwapBuffers()


def keyboard(key, x, y):
    global player_pos, camera_mode, game_state, fuel
    global track_z_offset, menu_index

    key = key.decode('utf-8').lower()

    if game_state == STATE_MENU:
        if key in ['\r', '\n']:
            start_game_with(menu_options[menu_index])
    elif game_state == STATE_PLAYING:
        if key == 'a':
            player_pos[0] = max(-100, player_pos[0] - 100)
        elif key == 'd':
            player_pos[0] = min(100, player_pos[0] + 100)
        elif key == 'c':
            camera_mode = 1 - camera_mode
    elif game_state == STATE_GAME_OVER:
        if key == 'r':
            reset_to_menu()


def special_keys(key, x, y):
    global menu_index
    if game_state == STATE_MENU:
        if key == GLUT_KEY_UP:
            menu_index = (menu_index - 1) % len(menu_options)
        elif key == GLUT_KEY_DOWN:
            menu_index = (menu_index + 1) % len(menu_options)
        glutPostRedisplay()


def start_game_with(difficulty_name):
    global base_speed, speed, base_spawn_interval, spawn_interval, game_state
    global player_pos, score, obstacles, nitro_active, shield_active
    global track_z_offset, camera_mode, player_color, distance, fuel
    global next_difficulty_increase, enemy_move_timers

    settings = difficulties[difficulty_name]
    base_speed = settings['speed']
    speed = base_speed
    base_spawn_interval = settings['spawn']
    spawn_interval = base_spawn_interval
    player_pos = [0, 0, 0]
    player_color = [0, 0.5, 1]
    score = 0
    distance = 0
    fuel = 100
    obstacles.clear()
    nitro_active = False
    shield_active = False
    track_z_offset = 0
    camera_mode = 0
    next_difficulty_increase = difficulty_increase_interval
    enemy_move_timers = {}

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
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"3D Racing Game")
    init()
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutTimerFunc(0, lambda x: update(), 0)
    glutMainLoop()


if __name__ == "__main__":
    main()