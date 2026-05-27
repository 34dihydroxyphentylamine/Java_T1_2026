import os
import random
from datetime import datetime
import pygame
from PIL import Image as PILImage

# --- Globale Konstanten & Konfiguration ---
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 600
GRAVITY = 1.5  

SCORE_FILE = "highscore.txt"

def get_last_best_score():
    """Lädt den besten Score aus einer simplen Textdatei."""
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                line = f.readline().strip()
                if line:
                    parts = line.split(";")
                    if len(parts) == 3:
                        return f"Bester: {parts[0]} ({parts[1]}) am {parts[2]}"
        except Exception:
            pass
    return "Kein Highscore vorhanden"

def save_score(score, username="unknown"):
    """Speichert den Highscore als Textzeile ab, falls er besser als der alte ist."""
    current_best = 0
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                line = f.readline().strip()
                if line:
                    parts = line.split(";")
                    current_best = int(parts[0])
        except Exception:
            pass
            
    if score >= current_best:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(SCORE_FILE, "w") as f:
                f.write(f"{score};{username};{date_str}\n")
        except Exception as e:
            print(f"Fehler beim Schreiben der Textdatei: {e}")

def load_gif_frames(filename):
    """Lädt ein animiertes GIF und konvertiert die Frames für Pygame."""
    frames = []
    if os.path.exists(filename):
        try:
            pil_img = PILImage.open(filename)
            for frame_idx in range(getattr(pil_img, "n_frames", 1)):
                pil_img.seek(frame_idx)
                frame_rgba = pil_img.convert("RGBA")
                mode = frame_rgba.mode
                size = frame_rgba.size
                data = frame_rgba.tobytes()
                pygame_surface = pygame.image.fromstring(data, size, mode)
                frames.append(pygame_surface)
        except Exception as e:
            print(f"Fehler beim Laden des GIFs: {e}")
    return frames

# --- Pygame Initialisierung ---
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Geometry Dash")

# Assets laden
def safe_load_image(filename, fallback_color=(200, 0, 0), size=(70, 70)):
    if os.path.exists(filename):
        return pygame.image.load(filename).convert_alpha()
    surface = pygame.surface.Surface(size, pygame.SRCALPHA)
    surface.fill(fallback_color)
    return surface

sprite_img = safe_load_image("sprite.png", (0, 150, 255))
prize_img = safe_load_image("prize.png", (255, 215, 0), (40, 40))
shelf_img = safe_load_image("shelf.png", (139, 69, 19), (150, 20))

# Hintergründe laden
bg1_img = safe_load_image("bg1.jpeg", (240, 240, 240), (DEFAULT_WIDTH, DEFAULT_HEIGHT))
bg2_img = safe_load_image("bg2.jpg", (30, 30, 50), (DEFAULT_WIDTH, DEFAULT_HEIGHT))

# Audio laden
if os.path.exists("music.mp3"):
    pygame.mixer.music.load("music.mp3")

menu_sound = None
if os.path.exists("menu_audio.mp3"):
    menu_sound = pygame.mixer.Sound("menu_audio.mp3")

# --- Spieler-Klasse ---
class Player:
    def __init__(self):
        self.base_width = 70
        self.base_height = 70
        self.base_x = 100
        self.base_y = DEFAULT_HEIGHT - self.base_height
        
        self.vel_y = 0
        self.rotation = 0
        self.is_on_ground = True

    def jump(self):
        # Unendlicher Sprung: Setzt die Geschwindigkeit unabhängig vom Boden sofort nach oben
        self.vel_y = -22
        self.is_on_ground = False

    def update(self, platforms, current_height):
        self.vel_y += GRAVITY
        self.base_y += self.vel_y

        scale_y = current_height / DEFAULT_HEIGHT
        ground_level = DEFAULT_HEIGHT - self.base_height
        
        self.is_on_ground = False
        player_rect = self.get_rect(pygame.display.get_surface().get_size())
        
        if self.vel_y >= 0:
            for plat in platforms:
                if player_rect.colliderect(plat):
                    plat_base_top = plat.top / scale_y
                    if (player_rect.bottom - self.vel_y * scale_y) <= plat.top + 8:
                        self.base_y = plat_base_top - self.base_height
                        self.vel_y = 0
                        self.is_on_ground = True
                        self.rotation = 0
                        break

        if self.base_y >= ground_level:
            self.base_y = ground_level
            self.vel_y = 0
            self.is_on_ground = True
            self.rotation = 0
        else:
            if not self.is_on_ground:
                self.rotation -= 5

    def draw(self, screen_size):
        w, h = screen_size
        scale_x = w / DEFAULT_WIDTH
        scale_y = h / DEFAULT_HEIGHT

        current_w = max(10, int(self.base_width * scale_x))
        current_h = max(10, int(self.base_height * scale_y))
        current_x = int(self.base_x * scale_x)
        current_y = int(self.base_y * scale_y)

        scaled_sprite = pygame.transform.scale(sprite_img, (current_w, current_h))
        rotated = pygame.transform.rotate(scaled_sprite, self.rotation)
        rect = rotated.get_rect(center=(current_x + current_w // 2, current_y + current_h // 2))
        pygame.display.get_surface().blit(rotated, rect.topleft)

    def get_rect(self, screen_size):
        w, h = screen_size
        scale_x = w / DEFAULT_WIDTH
        scale_y = h / DEFAULT_HEIGHT
        return pygame.Rect(
            int(self.base_x * scale_x),
            int(self.base_y * scale_y),
            max(1, int(self.base_width * scale_x)),
            max(1, int(self.base_height * scale_y))
        )

# --- Spielelemente-Klassen ---
class Spike:
    def __init__(self, x_pos, spike_type):
        self.base_x = x_pos
        self.spike_type = spike_type
        self.base_width = 40 * spike_type
        self.base_height = 50
        self.base_y = DEFAULT_HEIGHT - self.base_height

    def update(self, speed):
        self.base_x -= speed

    def draw(self, screen_size):
        w, h = screen_size
        scale_x = w / DEFAULT_WIDTH
        scale_y = h / DEFAULT_HEIGHT

        curr_x = int(self.base_x * scale_x)
        curr_w = int(self.base_width * scale_x)
        curr_h = int(self.base_height * scale_y)
        curr_y = int(self.base_y * scale_y)

        if self.spike_type > 0:
            single_w = max(1, curr_w // self.spike_type)
            for i in range(self.spike_type):
                start_x = curr_x + (i * single_w)
                points = [
                    (start_x, curr_y + curr_h),
                    (start_x + single_w // 2, curr_y),
                    (start_x + single_w, curr_y + curr_h)
                ]
                pygame.draw.polygon(pygame.display.get_surface(), (220, 50, 50), points)

    def get_rect(self, screen_size):
        w, h = screen_size
        scale_x = w / DEFAULT_WIDTH
        scale_y = h / DEFAULT_HEIGHT
        return pygame.Rect(
            int(self.base_x * scale_x),
            int(self.base_y * scale_y),
            max(1, int(self.base_width * scale_x)),
            max(1, int(self.base_height * scale_y))
        )

class PlatformShelf:
    def __init__(self, x_pos, y_pos):
        self.base_x = x_pos
        self.base_y = y_pos
        self.base_width = 180
        self.base_height = 25
        self.has_prize = True

    def update(self, speed):
        self.base_x -= speed

    def draw(self, screen_size):
        w, h = screen_size
        scale_x = w / DEFAULT_WIDTH
        scale_y = h / DEFAULT_HEIGHT

        curr_x = int(self.base_x * scale_x)
        curr_y = int(self.base_y * scale_y)
        curr_w = max(5, int(self.base_width * scale_x))
        curr_h = max(2, int(self.base_height * scale_y))

        scaled_shelf = pygame.transform.scale(shelf_img, (curr_w, curr_h))
        pygame.display.get_surface().blit(scaled_shelf, (curr_x, curr_y))

        if self.has_prize:
            prize_w = max(2, int(40 * scale_x))
            prize_h = max(2, int(40 * scale_y))
            scaled_prize = pygame.transform.scale(prize_img, (prize_w, prize_h))
            prize_x = curr_x + (curr_w // 2) - (prize_w // 2)
            prize_y = curr_y - prize_h
            pygame.display.get_surface().blit(scaled_prize, (prize_x, prize_y))

    def get_rect(self, screen_size):
        w, h = screen_size
        scale_x = w / DEFAULT_WIDTH
        scale_y = h / DEFAULT_HEIGHT
        return pygame.Rect(
            int(self.base_x * scale_x),
            int(self.base_y * scale_y),
            max(1, int(self.base_width * scale_x)),
            max(1, int(self.base_height * scale_y))
        )

    def get_prize_rect(self, screen_size):
        if not self.has_prize:
            return pygame.Rect(0, 0, 0, 0)
        w, h = screen_size
        scale_x = w / DEFAULT_WIDTH
        scale_y = h / DEFAULT_HEIGHT
        
        curr_w = max(5, int(self.base_width * scale_x))
        prize_w = max(1, int(40 * scale_x))
        prize_h = max(1, int(40 * scale_y))
        
        curr_x = int(self.base_x * scale_x)
        curr_y = int(self.base_y * scale_y)
        
        return pygame.Rect(
            curr_x + (curr_w // 2) - (prize_w // 2),
            curr_y - prize_h,
            prize_w,
            prize_h
        )

# --- Zeichen-Hilfsfunktionen ---
def draw_text(text, size, color, x, y, align_center=True):
    font = pygame.font.SysFont("Arial", max(10, int(size)))
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align_center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    pygame.display.get_surface().blit(text_surface, text_rect)

def draw_pause_screen(screen_size):
    w, h = screen_size
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    pygame.display.get_surface().blit(overlay, (0, 0))
    draw_text("PAUSE", h // 8, (255, 255, 255), w // 2, h // 2)
    draw_text("Drücke 'S' zum Fortsetzen", h // 20, (200, 200, 200), w // 2, h // 2 + (h // 10))

# --- Pygame-internes Texteingabefeld ---
def pygame_username_input(score):
    username = ""
    input_active = True
    
    while input_active:
        clock.tick(60)
        w, h = screen.get_size()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_score(score, "unknown")
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False  
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    if len(username) < 20 and event.unicode.isprintable():
                        if event.unicode != ";":
                            username += event.unicode

        screen.fill((20, 20, 30))
        
        draw_text("GAME OVER", h // 10, (220, 50, 50), w // 2, h // 5)
        draw_text(f"Dein Score: {score}", h // 18, (255, 255, 255), w // 2, h // 3.2)
        draw_text("Gib Deinen Namen ein (max. 20 Zeichen):", h // 22, (200, 200, 200), w // 2, h // 2.2)
        
        box_w, box_h = int(400 * (w / DEFAULT_WIDTH)), int(50 * (h / DEFAULT_HEIGHT))
        box_rect = pygame.Rect(w // 2 - box_w // 2, h // 1.8 - box_h // 2, box_w, box_h)
        pygame.draw.rect(screen, (50, 50, 70), box_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 255, 150), box_rect, 2, border_radius=5)
        
        display_name = username + ("|" if (pygame.time.get_ticks() // 500) % 2 == 0 else "")
        draw_text(display_name, h // 20, (255, 255, 255), w // 2, h // 1.8)
        
        draw_text("Drücke [ENTER] zum Speichern", h // 25, (150, 150, 150), w // 2, h // 1.4)
        
        pygame.display.flip()
        
    return username if username.strip() else "Player"

# --- Haupt-Menü Funktion ---
def menu_pane():
    pygame.mixer.music.stop()

    # Kontinuierliches Menü-Audio starten
    menu_channel = None
    if menu_sound:
        menu_channel = menu_sound.play(loops=-1)

    gif_frames = load_gif_frames("animation.gif")
    gif_index = 0
    last_frame_time = pygame.time.get_ticks()

    menu_running = True
    selected_level = None

    while menu_running:
        clock.tick(60)
        w, h = screen.get_size()
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        # Dynamische Button-Größen berechnen
        btn_w, btn_h = int(220 * (w / DEFAULT_WIDTH)), int(60 * (h / DEFAULT_HEIGHT))
        btn1_rect = pygame.Rect(w // 2 - btn_w - int(20 * (w / DEFAULT_WIDTH)), h // 2.2, btn_w, btn_h)
        btn2_rect = pygame.Rect(w // 2 + int(20 * (w / DEFAULT_WIDTH)), h // 2.2, btn_w, btn_h)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if menu_channel:
                    menu_channel.stop()
                save_score(0, "unknown")
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_level = 1
                    menu_running = False
                elif event.key == pygame.K_2:
                    selected_level = 2
                    menu_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Linksklick auf Buttons
                    if btn1_rect.collidepoint(mouse_pos):
                        selected_level = 1
                        menu_running = False
                    elif btn2_rect.collidepoint(mouse_pos):
                        selected_level = 2
                        menu_running = False

        if gif_frames:
            if current_time - last_frame_time > 100:
                gif_index = (gif_index + 1) % len(gif_frames)
                last_frame_time = current_time
            scaled_bg = pygame.transform.scale(gif_frames[gif_index], (w, h))
            screen.blit(scaled_bg, (0, 0))
        else:
            screen.fill((40, 44, 52))

        draw_text("WILLKOMMEN BEI GEOMETRY DASH!", h // 12, (255, 255, 255), w // 2, h // 5)

        # Button 1 (Level 1)
        color_btn1 = (0, 200, 120) if btn1_rect.collidepoint(mouse_pos) else (0, 160, 90)
        pygame.draw.rect(screen, color_btn1, btn1_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), btn1_rect, 2, border_radius=8)
        draw_text("Level 1", h // 20, (255, 255, 255), btn1_rect.centerx, btn1_rect.centery)

        # Button 2 (Level 2)
        color_btn2 = (0, 200, 120) if btn2_rect.collidepoint(mouse_pos) else (0, 160, 90)
        pygame.draw.rect(screen, color_btn2, btn2_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), btn2_rect, 2, border_radius=8)
        draw_text("Level 2", h // 20, (255, 255, 255), btn2_rect.centerx, btn2_rect.centery)
        
        highscore_text = get_last_best_score()
        draw_text(highscore_text, h // 22, (255, 215, 0), w // 2, h - (h // 6))

        pygame.display.flip()

    if menu_channel:
        menu_channel.stop()
        
    return selected_level

# --- Gemeinsame Level-Logik-Funktion ---
def run_level(level_type):
    player = Player()
    spikes = []
    platforms = []
    
    score = 0
    game_paused = False
    level_running = True
    
    game_speed = 7
    spawn_timer = 0
    
    # Normalen Level-Soundtrack starten
    if os.path.exists("music.mp3"):
        pygame.mixer.music.play(-1)
    
    while level_running:
        clock.tick(60)
        w, h = screen.get_size()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_score(score, "unknown")
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    game_paused = not game_paused
                elif event.key == pygame.K_SPACE and not game_paused:
                    player.jump()

        if game_paused:
            draw_pause_screen((w, h))
            pygame.display.flip()
            continue

        spawn_timer -= 1
        if spawn_timer <= 0:
            choice = random.choice(["single", "double", "spaced", "platform"])
            
            if choice == "single" or level_type == 1:
                spike_type = random.randint(1, 3)
                spikes.append(Spike(DEFAULT_WIDTH, spike_type))
                spawn_timer = random.randint(90, 150)
            elif choice == "double" and level_type == 2:
                spikes.append(Spike(DEFAULT_WIDTH, 1))
                spikes.append(Spike(DEFAULT_WIDTH + 50, 1))
                spawn_timer = random.randint(110, 160)
            elif choice == "spaced" and level_type == 2:
                spikes.append(Spike(DEFAULT_WIDTH, 2))
                spawn_timer = random.randint(100, 140)
            elif choice == "platform" and level_type == 2:
                plat_y = random.randint(320, 420)
                platforms.append(PlatformShelf(DEFAULT_WIDTH, plat_y))
                if random.random() > 0.5:
                    spikes.append(Spike(DEFAULT_WIDTH + 60, 1))
                spawn_timer = random.randint(120, 180)

        # Zuweisung der JPEG-Hintergründe je nach gewähltem Level
        if level_type == 1:
            scaled_bg1 = pygame.transform.scale(bg1_img, (w, h))
            screen.blit(scaled_bg1, (0, 0))
        elif level_type == 2:
            scaled_bg2 = pygame.transform.scale(bg2_img, (w, h))
            screen.blit(scaled_bg2, (0, 0))

        # Bodenlinie zur Orientierung zeichnen
        pygame.draw.line(screen, (100, 100, 100), (0, h - 5), (w, h - 5), 5)

        # Plattformen verarbeiten
        active_platform_rects = []
        for plat in platforms:
            plat.update(game_speed)
            plat.draw((w, h))
            active_platform_rects.append(plat.get_rect((w, h)))
            
            if plat.has_prize:
                prize_rect = plat.get_prize_rect((w, h))
                if player.get_rect((w, h)).colliderect(prize_rect):
                    plat.has_prize = False
                    score += 5

        # Spieler updaten und zeichnen
        player.update(active_platform_rects, h)
        player.draw((w, h))

        # Spikes verarbeiten und Kollisionen prüfen
        for spike in spikes:
            spike.update(game_speed)
            spike.draw((w, h))
            
            if player.get_rect((w, h)).colliderect(spike.get_rect((w, h))):
                level_running = False

        spikes = [s for s in spikes if s.base_x > -150]
        platforms = [p for p in platforms if p.base_x > -200]

        score += 1
        if score % 500 == 0:
            game_speed += 0.5

        draw_text(f"Score: {score}", h // 22, (0, 0, 0) if level_type == 1 else (255, 255, 255), w // 20, h // 20, align_center=False)

        pygame.display.flip()

    chosen_name = pygame_username_input(score)
    save_score(score, chosen_name)

# --- Hauptprogramm ---
def main():
    while True:
        level_choice = menu_pane()
        if level_choice in [1, 2]:
            run_level(level_choice)

if __name__ == "__main__":
    main()
