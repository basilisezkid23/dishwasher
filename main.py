""""
Copyright (C) 2026 basilisezkid23   

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import pygame
from pathlib import Path
import sys
import math
import random

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

BASE_WIDTH, BASE_HEIGHT = 1280, 720
WIDTH, HEIGHT = 1280, 720
FPS = 60

#color palete
BG_COLOR = (20, 22, 24)        
PANEL_SHADOW = (10, 11, 12)
LED_ON = (255, 30, 30)
LED_GLOW = (200, 10, 10, 120)  
LED_OFF = (45, 12, 12)
TEXT_COLOR = (200, 200, 200)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Siemens SF64T353EU/01 Simulator")
clock = pygame.time.Clock()

font = pygame.font.SysFont("dejavusans", 24, bold=True)
button_font = pygame.font.SysFont("dejavusans", 20, bold=True)
title_font = pygame.font.SysFont("dejavusans", 36, bold=True)
status_font = pygame.font.SysFont("dejavusans", 18, bold=True)

#audio
class AudioEngine:
    def __init__(self):
        self.sounds = {}
        self.load_sounds()
        
        self.ch_fx = pygame.mixer.Channel(0)    
        self.ch_pump = pygame.mixer.Channel(1)  
        self.ch_wash = pygame.mixer.Channel(2)  
        
        self.ch_pump.set_volume(1.0)
        self.ch_wash.set_volume(1.0)

    def load_sounds(self):
        BASE_DIR = Path(__file__).resolve().parent
        ASSETS_DIR = BASE_DIR / "assets"
        # Finally figured it out
        sound_files: list[str] = [
            "relay1.wav",
            "relay2.wav",
            "start.wav",
            "stop.wav",
            "wash.wav",
            "MotorPump1.wav"
        ]
        for filename in sound_files:
            path = ASSETS_DIR / filename

            if not path.exists():
                raise FileNotFoundError(f"Missing audio asset: {path}")

            self.sounds[filename] = pygame.mixer.Sound(str(path))

    def play_fx(self, name):
        self.ch_fx(self.sounds[name])
        return self.sounds[name].get_length() * 1000

    def start_loops(self):
        self.ch_pump.play(self.sounds["MotorPump1.wav"], loops=-1)

    def trigger_spray(self):
        self.ch_wash.play(self.sounds["wash.wav"])

    def stop_loops(self):
        self.ch_pump.stop()
        self.ch_wash.stop()

audio = AudioEngine()

#cool display
class SevenSegment:
    DIGITS = {
        '0': (1, 1, 1, 1, 1, 1, 0),
        '1': (0, 1, 1, 0, 0, 0, 0),
        '2': (1, 1, 0, 1, 1, 0, 1),
        '3': (1, 1, 1, 1, 0, 0, 1),
        '4': (0, 1, 1, 0, 0, 1, 1),
        '5': (1, 0, 1, 1, 0, 1, 1),
        '6': (1, 0, 1, 1, 1, 1, 1),
        '7': (1, 1, 1, 0, 0, 0, 0),
        '8': (1, 1, 1, 1, 1, 1, 1),
        '9': (1, 1, 1, 1, 0, 1, 1),
        ' ': (0, 0, 0, 0, 0, 0, 0)
    }

    def __init__(self, center_x, center_y, scale=1.0):
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale
        
        self.seg_w = int(24 * scale)
        self.seg_h = int(22 * scale)
        self.t = int(5 * scale) 
        self.gap = int(2 * scale)

        self.glow_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        self.diffuser_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)

    def draw_polygon_with_glow(self, surface, points, is_on, brightness=1.0):
        if not is_on:
            color = LED_OFF
        else:
            r = int(LED_ON[0] * brightness)
            g = int(LED_ON[1] * brightness)
            b = int(LED_ON[2] * brightness)
            color = (r, g, b)

        pygame.draw.polygon(surface, color, points)
        if is_on and brightness > 0.1:
            glow_alpha = int(120 * brightness)
            r_g = int(LED_GLOW[0] * brightness)
            g_g = int(LED_GLOW[1] * brightness)
            b_g = int(LED_GLOW[2] * brightness)
            dynamic_glow = (r_g, g_g, b_g, glow_alpha)
            pygame.draw.polygon(self.glow_surface, dynamic_glow, points)

    def draw_digit(self, surface, digit, ox, oy, custom_states=None, brightness=1.0):
        states = custom_states if custom_states is not None else self.DIGITS.get(digit, self.DIGITS[' '])
        w = self.seg_w
        h = self.seg_h
        t = self.t

        segs = [
            [(ox+4, oy), (ox+w-4, oy), (ox+w, oy+4), (ox+w-4, oy+t), (ox+4, oy+t), (ox, oy+4)],
            [(ox+w, oy+4), (ox+w, oy+h-4), (ox+w-t, oy+h-t-2), (ox+w-t, oy+4+t)],
            [(ox+w, oy+h+4), (ox+w, oy+(h*2)-4), (ox+w-t, oy+(h*2)-4-t), (ox+w-t, oy+h+4+t)],
            [(ox+4, oy+(h*2)-t), (ox+w-4, oy+(h*2)-t), (ox+w, oy+(h*2)-4), (ox+w-4, oy+(h*2)), (ox+4, oy+(h*2)), (ox, oy+(h*2)-4)],
            [(ox, oy+h+4), (ox, oy+(h*2)-4), (ox+t, oy+(h*2)-4-t), (ox+t, oy+h+4+t)],
            [(ox, oy+4), (ox, oy+h-4), (ox+t, oy+h-t-2), (ox+t, oy+4+t)],
            [(ox+4, oy+h), (ox+w-4, oy+h), (ox+w, oy+h+t//2), (ox+w-4, oy+h+t), (ox+4, oy+h+t), (ox, oy+h+t//2)]
        ]

        for i, pts in enumerate(segs):
            self.draw_polygon_with_glow(surface, pts, states[i], brightness)

    def render(self, surface, time_str, custom_digit_states=None, colon_on=True, brightness=1.0, powered_on=True):
        self.glow_surface.fill((0, 0, 0, 0))

        bezel_rect = pygame.Rect(self.center_x - 170, self.center_y - 85, 340, 170)
        self.diffuser_surface.fill((0, 0, 0, 0))
        bezel_color = (15, 15, 18, 230) if powered_on else (8, 8, 10, 240)
        pygame.draw.rect(self.diffuser_surface, bezel_color, bezel_rect, border_radius=12)
        surface.blit(self.diffuser_surface, (0,0))

        if not powered_on:
            return

        digit_total_w = self.seg_w
        colon_w = int(16 * self.scale)
        total_width = (4 * digit_total_w) + colon_w + (6 * int(6 * self.scale))
        
        start_x = self.center_x - (total_width // 2)
        start_y = self.center_y - (self.seg_h)

        x_offset = start_x
        for idx, char in enumerate(time_str):
            if char == ':':
                cx = x_offset + colon_w // 2
                cy1 = start_y + self.seg_h - int(6 * self.scale)
                cy2 = start_y + self.seg_h + int(6 * self.scale)
                rad = int(3 * self.scale)
                
                c_on = colon_on and (brightness > 0.1)
                col_color = LED_ON if c_on else LED_OFF
                surface.set_at((cx, cy1), col_color)
                
                pygame.draw.circle(surface, col_color, (cx, cy1), rad)
                if c_on:
                    pygame.draw.circle(self.glow_surface, LED_GLOW, (cx, cy1), rad + 3)
                pygame.draw.circle(surface, col_color, (cx, cy2), rad)
                if c_on:
                    pygame.draw.circle(self.glow_surface, LED_GLOW, (cx, cy2), rad + 3)
                
                x_offset += colon_w + int(4 * self.scale)
            else:
                c_states = custom_digit_states[idx] if custom_digit_states and idx < len(custom_digit_states) else None
                self.draw_digit(surface, char, x_offset, start_y, custom_states=c_states, brightness=brightness)
                x_offset += self.seg_w + int(8 * self.scale)

        surface.blit(self.glow_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)


#the ui
class Button:
    def __init__(self, x, y, w, h, text, program_time, spray_interval):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.program_time = program_time
        self.spray_interval = spray_interval
        self.is_hovered = False
        self.is_pressed = False

    def draw(self, surface, enabled=True, forced_led_on=None):
        press_offset = 3 if (self.is_pressed and enabled) else 0
        
        if not enabled:
            base_color = (30, 31, 33)
            top_highlight = (40, 41, 43)
            bottom_shadow = (20, 21, 22)
            txt_col = (90, 90, 90)
            led_col = (30, 15, 15)
        else:
            base_color = (60, 62, 65) if self.is_hovered else (45, 47, 50)
            top_highlight = (20, 22, 24) if self.is_pressed else (90, 92, 95)
            bottom_shadow = (90, 92, 95) if self.is_pressed else (20, 22, 24)
            txt_col = TEXT_COLOR
            
            if forced_led_on is not None:
                led_col = LED_ON if forced_led_on else (70, 20, 20)
            else:
                led_col = LED_ON if self.is_pressed or self.is_hovered else (70, 20, 20)

        btn_draw_rect = self.rect.copy()
        btn_draw_rect.y += press_offset

        pygame.draw.rect(surface, base_color, btn_draw_rect, border_radius=8)
        pygame.draw.line(surface, top_highlight, btn_draw_rect.topleft, btn_draw_rect.topright, 2)
        pygame.draw.line(surface, top_highlight, btn_draw_rect.topleft, btn_draw_rect.bottomleft, 2)
        pygame.draw.line(surface, bottom_shadow, btn_draw_rect.bottomleft, btn_draw_rect.bottomright, 2)
        pygame.draw.line(surface, bottom_shadow, btn_draw_rect.topright, btn_draw_rect.bottomright, 2)

        pygame.draw.circle(surface, led_col, (btn_draw_rect.x + 15, btn_draw_rect.centery), 4)

        txt_surf = button_font.render(self.text, True, txt_col)
        txt_rect = txt_surf.get_rect(center=btn_draw_rect.center)
        surface.blit(txt_surf, txt_rect)


class PowerButton:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.is_hovered = False
        self.is_pressed = False

    def draw(self, surface, is_on):
        press_offset = 2 if self.is_pressed else 0
        base_color = (70, 30, 30) if is_on else (40, 42, 45)
        if self.is_hovered:
            base_color = (90, 40, 40) if is_on else (55, 57, 60)

        draw_rect = self.rect.copy()
        draw_rect.y += press_offset

        pygame.draw.rect(surface, base_color, draw_rect, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), draw_rect, width=2, border_radius=8)

        center = draw_rect.center
        pygame.draw.circle(surface, (220, 220, 220) if is_on else (120, 120, 120), center, 10, width=2)
        pygame.draw.line(surface, (220, 220, 220) if is_on else (120, 120, 120), (center[0], center[1] - 12), (center[0], center[1] - 3), 2)


class DoorButton:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.is_hovered = False
        self.is_pressed = False

    def draw(self, surface, is_open):
        press_offset = 2 if self.is_pressed else 0
        base_color = (70, 50, 30) if is_open else (40, 45, 50)
        if self.is_hovered:
            base_color = (90, 65, 40) if is_open else (55, 60, 65)

        draw_rect = self.rect.copy()
        draw_rect.y += press_offset

        pygame.draw.rect(surface, base_color, draw_rect, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), draw_rect, width=2, border_radius=8)

        txt = "DOOR: OPEN" if is_open else "DOOR: CLOSED"
        txt_surf = status_font.render(txt, True, (240, 200, 100) if is_open else (200, 200, 200))
        txt_rect = txt_surf.get_rect(center=draw_rect.center)
        surface.blit(txt_surf, txt_rect)


# if you break the logic its not my problem, future code editor
class DishwasherMachine:
    def __init__(self):
        self.powered_on = True
        self.door_open = False
        
        self.state = "BOOT"  
        self.seq_step = 0
        self.next_trigger_time = 0
        
        self.time_left = 0
        self.total_program_duration = 0
        self.last_tick = 0
        self.boot_timer = 0
        self.boot_sub_state = 0
        
        self.active_spray_interval = 5
        self.last_spray_time = 0
        self.last_relay_click_time = 0
        
        self.active_program_index = None
        self.busy_warning_timer = 0
        self.busy_warning_active = False
        self.door_warning_timer = 0
        self.door_warning_active = False
        
        self.display = SevenSegment(640, 260, scale=2.2)
        
        self.buttons = [
            Button(135, 460, 235, 80, "GLASSES", 25, spray_interval=2),
            Button(385, 460, 235, 80, "DISHES", 40, spray_interval=4),
            Button(635, 460, 235, 80, "MIXED", 50, spray_interval=3),
            Button(885, 460, 235, 80, "FULL WASH", 70, spray_interval=3)
        ]

        self.power_btn = PowerButton(1150, 50, 60, 60)
        self.door_btn = DoorButton(970, 50, 160, 60)

        self.trigger_boot_sequence()

    def trigger_boot_sequence(self):
        self.state = "BOOT"
        self.boot_timer = pygame.time.get_ticks()
        self.boot_sub_state = 0
        self.active_program_index = None
        self.busy_warning_active = False
        self.door_warning_active = False

    def format_time(self):
        if not self.powered_on:
            return "    "
        if self.door_open and self.state in ["READY", "FILLING", "WASHING", "HEATING"]:
            return "OPEN"
        if self.state == "BOOT":
            if self.boot_sub_state == 1:
                return "88:88"
            elif self.boot_sub_state == 2:
                return "    "
            elif self.boot_sub_state == 3:
                return "00:00"
            return "    "
        if self.time_left <= 0:
            return "00:00"
        m = self.time_left // 60
        s = self.time_left % 60
        return f"{m:02d}:{s:02d}"

    def get_custom_boot_display(self):
        if self.state != "BOOT":
            return None
        
        elapsed = pygame.time.get_ticks() - self.boot_timer
        if elapsed < 200:
            return None
        elif elapsed < 400:
            partial = (0, 0, 0, 0, 0, 0, 1)
            return [partial, partial, partial, partial]
        elif elapsed < 800:
            full_on = (1, 1, 1, 1, 1, 1, 1)
            return [full_on, full_on, full_on, full_on]
        elif elapsed < 1100:
            self.boot_sub_state = 1
            return None
        elif elapsed < 1300:
            self.boot_sub_state = 2
            return None
        elif elapsed < 1600:
            self.boot_sub_state = 3
            return None
        return None

    def start_program(self, index, time_seconds, spray_interval):
        if not self.powered_on:
            return
            
        if self.door_open:
            self.door_warning_active = True
            self.door_warning_timer = pygame.time.get_ticks()
            return
            
        if self.state in ["FILLING", "WASHING", "HEATING", "DRAINING", "STOPPING"]:
            self.busy_warning_active = True
            self.busy_warning_timer = pygame.time.get_ticks()
            return

        if self.state == "READY" or self.state == "FINISHED":
            self.active_program_index = index
            self.time_left = time_seconds
            self.total_program_duration = time_seconds
            self.active_spray_interval = spray_interval
            
            self.state = "FILLING"
            self.seq_step = 1
            
            duration = audio.play_fx("relay1.wav")
            self.next_trigger_time = pygame.time.get_ticks() + duration

    def handle_power_button_action(self):
        if self.powered_on:
            if self.state in ["FILLING", "WASHING", "HEATING", "DRAINING"]:
                audio.stop_loops()
                self.state = "DRAINING"
                self.seq_step = 100 
                dur = audio.play_fx("stop.wav")
                self.next_trigger_time = pygame.time.get_ticks() + dur
            else:
                self.powered_on = False
                self.state = "POWER OFF"
                self.time_left = 0
                self.active_program_index = None
                self.busy_warning_active = False
                self.door_warning_active = False
                audio.stop_loops()
        else:
            self.powered_on = True
            self.trigger_boot_sequence()

    def handle_door_button_action(self):
        self.door_open = not self.door_open
        if self.door_open and self.state in ["FILLING", "WASHING", "HEATING"]:
            audio.stop_loops()
            self.state = "READY"
            self.time_left = 0
            self.active_program_index = None

    def process_state_machine(self):
        now = pygame.time.get_ticks()

        if not self.powered_on:
            self.state = "POWER OFF"
            self.time_left = 0
            self.active_program_index = None
            audio.stop_loops()
            return

        if self.door_open and self.state in ["FILLING", "WASHING", "HEATING"]:
            audio.stop_loops()
            self.state = "READY"
            self.time_left = 0
            self.active_program_index = None

        if self.state == "BOOT":
            if now - self.boot_timer >= 1800:
                self.state = "READY"
                self.boot_sub_state = 4

        elif self.state == "FILLING":
            if now >= self.next_trigger_time:
                if self.seq_step == 1:
                    dur = audio.play_fx("start.wav")
                    self.next_trigger_time = now + dur
                    self.seq_step = 2
                elif self.seq_step == 2:
                    dur = audio.play_fx("relay2.wav")
                    self.next_trigger_time = now + dur
                    self.seq_step = 3
                elif self.seq_step == 3:
                    audio.start_loops()
                    self.state = "WASHING"
                    self.last_tick = now
                    self.last_spray_time = now
                    self.last_relay_click_time = now

        elif self.state == "WASHING":
            if now - self.last_relay_click_time >= random.randint(6000, 12000):
                relay_sound = "relay1.wav" if random.random() > 0.5 else "relay2.wav"
                audio.play_fx(relay_sound)
                self.last_relay_click_time = now

            elapsed_time = self.total_program_duration - self.time_left
            ratio = elapsed_time / max(1, self.total_program_duration)

            if self.active_program_index == 3:  
                if 0.35 <= ratio <= 0.38 and self.seq_step < 20:
                    audio.play_fx("relay1.wav")
                    self.seq_step = 20
                elif 0.4 <= ratio < 0.65:
                    self.state = "HEATING"
            elif self.active_program_index == 2:  
                if 0.5 <= ratio <= 0.52 and self.seq_step < 25:
                    audio.play_fx("relay2.wav")
                    self.seq_step = 25

            if (now - self.last_spray_time) >= (self.active_spray_interval * 1000):
                audio.trigger_spray()
                self.last_spray_time = now

            if now - self.last_tick >= 1000:
                self.time_left -= 1
                self.last_tick = now
                if self.time_left <= 0:
                    audio.stop_loops()
                    self.state = "DRAINING"
                    self.seq_step = 1
                    dur = audio.play_fx("stop.wav")
                    self.next_trigger_time = now + dur

        elif self.state == "HEATING":
            if (now - self.last_spray_time) >= (self.active_spray_interval * 1000):
                audio.trigger_spray()
                self.last_spray_time = now

            if now - self.last_tick >= 1000:
                self.time_left -= 1
                self.last_tick = now
                elapsed_time = self.total_program_duration - self.time_left
                ratio = elapsed_time / max(1, self.total_program_duration)
                if ratio >= 0.65:
                    self.state = "WASHING"

                if self.time_left <= 0:
                    audio.stop_loops()
                    self.state = "DRAINING"
                    self.seq_step = 1
                    dur = audio.play_fx("assets/stop.wav")
                    self.next_trigger_time = now + dur

        elif self.state == "DRAINING":
            if self.seq_step == 100:  
                self.powered_on = False
                self.state = "POWER OFF"
                self.time_left = 0
                self.active_program_index = None
                return

            if now >= self.next_trigger_time:
                if self.seq_step == 1:
                    dur = audio.play_fx("relay1.wav")
                    self.next_trigger_time = now + dur
                    self.seq_step = 2
                elif self.seq_step == 2:
                    dur = audio.play_fx("start.wav")
                    self.next_trigger_time = now + dur
                    self.seq_step = 3
                elif self.seq_step == 3:
                    dur = audio.play_fx("relay2.wav")
                    self.next_trigger_time = now + dur
                    self.seq_step = 4
                elif self.seq_step == 4:
                    self.state = "FINISHED"
                    self.time_left = 0

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        time_text = self.format_time()
        custom_states = self.get_custom_boot_display()
        
        now = pygame.time.get_ticks()
        colon_blink = (now // 500) % 2 == 0 if self.state in ["READY", "WASHING", "HEATING", "FINISHED"] else True
        pulse_brightness = 0.95 + 0.05 * math.sin(now / 200.0) if self.powered_on and self.state != "BOOT" else 1.0
        
        self.display.render(surface, time_text, custom_digit_states=custom_states, colon_on=colon_blink, brightness=pulse_brightness, powered_on=self.powered_on)
        
        title = title_font.render("SIEMENS", True, (150, 155, 160))
        surface.blit(title, (50, 50))
        model = font.render("SF64T353EU/01", True, (80, 85, 90))
        surface.blit(model, (50, 90))

        self.power_btn.draw(surface, self.powered_on)
        self.door_btn.draw(surface, self.door_open)

        status_str = self.state
        if not self.powered_on:
            status_str = "POWER OFF"
        elif self.door_open:
            status_str = "DOOR OPEN"
        elif self.door_warning_active:
            if (now // 200) % 2 == 0:
                status_str = "CLOSE DOOR FIRST"
        elif self.busy_warning_active:
            if (now // 200) % 2 == 0:
                status_str = "CYCLE IN PROGRESS"

        status_surf = status_font.render(f"STATUS: {status_str}", True, (220, 180, 60) if ("OPEN" in status_str or "FIRST" in status_str or "PROGRESS" in status_str) else (120, 180, 120))
        surface.blit(status_surf, (50, 140))

        busy_flash_state = False
        if self.busy_warning_active:
            elapsed_warning = now - self.busy_warning_timer
            if elapsed_warning >= 1500:
                self.busy_warning_active = False
            else:
                flash_step = (elapsed_warning // 250) % 2
                busy_flash_state = (flash_step == 0)

        if self.door_warning_active:
            if now - self.door_warning_timer >= 1500:
                self.door_warning_active = False

        for i, btn in enumerate(self.buttons):
            forced_led = None
            if self.busy_warning_active:
                forced_led = busy_flash_state
            elif self.active_program_index == i:
                if self.state in ["FILLING", "WASHING", "HEATING", "DRAINING"]:
                    forced_led = ((now // 500) % 2 == 0)
                elif self.state == "FINISHED":
                    forced_led = ((now // 250) % 2 == 0) and (now - self.last_tick < 5000)
            
            btn.draw(surface, enabled=self.powered_on, forced_led_on=forced_led)

    def handle_event(self, event, virtual_pos):
        if event.type == pygame.MOUSEMOTION:
            for btn in self.buttons:
                btn.is_hovered = btn.rect.collidepoint(virtual_pos)
            self.power_btn.is_hovered = self.power_btn.rect.collidepoint(virtual_pos)
            self.door_btn.is_hovered = self.door_btn.rect.collidepoint(virtual_pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.power_btn.rect.collidepoint(virtual_pos):
                    self.power_btn.is_pressed = True
                if self.door_btn.rect.collidepoint(virtual_pos):
                    self.door_btn.is_pressed = True
                if self.powered_on:
                    for btn in self.buttons:
                        if btn.rect.collidepoint(virtual_pos):
                            btn.is_pressed = True
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.power_btn.is_pressed:
                    if self.power_btn.rect.collidepoint(virtual_pos):
                        self.handle_power_button_action()
                    self.power_btn.is_pressed = False

                if self.door_btn.is_pressed:
                    if self.door_btn.rect.collidepoint(virtual_pos):
                        self.handle_door_button_action()
                    self.door_btn.is_pressed = False

                if self.powered_on:
                    for i, btn in enumerate(self.buttons):
                        if btn.is_pressed and btn.rect.collidepoint(virtual_pos):
                            self.start_program(i, btn.program_time, btn.spray_interval)
                        btn.is_pressed = False


# loop
def main():
    global screen
    machine = DishwasherMachine()
    fullscreen = False

    game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

    running = True
    while running:
        win_w, win_h = screen.get_size()
        
        scale_x = win_w / BASE_WIDTH
        scale_y = win_h / BASE_HEIGHT
        scale = min(scale_x, scale_y)
        
        scaled_w = int(BASE_WIDTH * scale)
        scaled_h = int(BASE_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        actual_mouse_pos = pygame.mouse.get_pos()
        virtual_mouse_x = int((actual_mouse_pos[0] - offset_x) / scale)
        virtual_mouse_y = int((actual_mouse_pos[1] - offset_y) / scale)
        virtual_mouse_pos = (virtual_mouse_x, virtual_mouse_y)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
                    else:
                        screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
                elif event.key == pygame.K_ESCAPE:
                    running = False

            machine.handle_event(event, virtual_mouse_pos)

        machine.process_state_machine()
        
        machine.draw(game_surface)

        screen.fill((0, 0, 0))

        scaled_surface = pygame.transform.smoothscale(game_surface, (scaled_w, scaled_h))
        screen.blit(scaled_surface, (offset_x, offset_y))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
