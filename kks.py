import pygame
import sys
import random
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

# Инициализация Pygame
pygame.init()
pygame.font.init()

# Константы
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# Шрифты
font_small = pygame.font.SysFont('Courier New', 18, bold=True)
font_medium = pygame.font.SysFont('Courier New', 22, bold=True)
font_large = pygame.font.SysFont('Courier New', 32, bold=True)

# Паттерн Стратегия для выбора атаки врагом
class AttackStrategy(ABC):
    @abstractmethod
    def choose_attack(self) -> str:
        pass

class FastAttackStrategy(AttackStrategy):
    def choose_attack(self) -> str:
        return random.choices(
            ["tentacle", "laser", "missile"],
            weights=[0.5, 0.3, 0.2]
        )[0]

class HeavyAttackStrategy(AttackStrategy):
    def choose_attack(self) -> str:
        return random.choices(
            ["tentacle", "laser", "missile"],
            weights=[0.3, 0.4, 0.3]
        )[0]

# Базовый класс корабля
class Spaceship:
    def __init__(self, name: str, max_hp: int):
        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.attack = None
        self.turn = False
        self.action_text = ""
        self.action_time = 0
        self.speech_text = ""
        self.speech_time = 0
    
    def take_damage(self, damage: int):
        self.current_hp = max(0, self.current_hp - damage)
        return self.current_hp <= 0

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def reset(self):
        self.current_hp = self.max_hp
        self.turn = False
        self.attack = None
        self.action_text = ""
        self.action_time = 0
        self.speech_text = ""
        self.speech_time = 0

# Класс игрока
class Player(Spaceship):
    def __init__(self, nickname: str):
        super().__init__(nickname, 150)
        self.wins = 0
        self.weapons = {
            "laser": {"damage": 35, "color": RED, "chance": 0.85},
            "ion": {"damage": 25, "color": CYAN, "chance": 0.9},
            "shield": {"damage": 15, "color": BLUE, "chance": 0.75}
        }
        self.actions = {
            "dodge": {"text": "УВОРОТ", "chance": 0.7},
            "attack": {"text": "ПРЯМОЙ УДАР", "chance": 0.85},
            "ignore": {"text": "ИГНОРИРОВАТЬ"}
        }

# Класс врага
class Enemy(Spaceship):
    def __init__(self, name: str, max_hp: int, strategy: AttackStrategy, image_path: str):
        super().__init__(name, max_hp)
        self.strategy = strategy
        self.original_image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.original_image, (250, 250))
        self.speech_bubble = pygame.Surface((300, 100), pygame.SRCALPHA)
        self.attack_names = {
            "tentacle": "ЩУПАЛЬЦЕ",
            "laser": "ЛАЗЕР",
            "missile": "РАКЕТА"
        }
        self.dialogues = {
            "win": ["ХА! ТЕБЕ НЕ ПОБЕДИТЬ!", "МОЯ ОЧЕРЕДЬ ТЕБЯ УНИЧТОЖИТЬ!"],
            "lose": ["АРГХ! КРИТИЧЕСКИЕ ПОВРЕЖДЕНИЯ!", "СИСТЕМЫ ОТКАЗЫВАЮТ!"],
            "draw": ["НИЧЬЯ? НЕВЕРОЯТНО!", "ТВОЯ ЗАЩИТА НЕПЛОХА..."],
            "dodge": ["ТЫ ДЕРЕШЬСЯ ИЛИ В ИГРЫ ИГРАЕМ?", "БЕГСТВО - ТВОЕ ЕДИНСТВЕННОЕ СПАСЕНИЕ!"],
            "attack": ["ПРИНИМАЙ УДАР!", "ЭТО БУДЕТ БОЛЬНО!"],
            "ignore": ["ТЫ СЛИШКОМ УВЕРЕН В СЕБЕ!", "ПОСМОТРИМ, КАК ТЫ ВЫКРУТИШЬСЯ!"],
            "tentacle": ["ЩУПАЛЬЦА ОПЛЕТАЮТ ТВОЙ КОРАБЛЬ!", "ПОПРОБУЙ УКЛОНИТЬСЯ ОТ ЭТОГО!"],
            "laser": ["ЛАЗЕРНЫЙ ЗАРЯД ЗАПУЩЕН!", "ОЧЕНЬ БОЛЬНО, ДА?"],
            "missile": ["РАКЕТЫ В ПУТИ!", "ПОДАРОК ДЛЯ ТЕБЯ!"]
        }
    
    def choose_attack(self) -> str:
        return self.strategy.choose_attack()
    
    def get_dialogue(self, result: str) -> str:
        return random.choice(self.dialogues[result])
    
    def update_speech_bubble(self, text: str):
        self.speech_bubble.fill((0, 0, 0, 0))
        pygame.draw.rect(self.speech_bubble, (50, 50, 100, 200), (0, 0, 300, 100), border_radius=10)
        pygame.draw.rect(self.speech_bubble, CYAN, (0, 0, 300, 100), 2, border_radius=10)
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if font_small.size(test_line)[0] < 280:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines[:2]):
            text_surface = font_small.render(line, True, WHITE)
            self.speech_bubble.blit(text_surface, (10, 10 + i * 25))
    
    def perform_enemy_turn(self, player):
        if not self.turn:
            return False
            
        current_time = time.time()
        
        # Фаза 1: Показ сообщения о ходе противника (первые 1.5 секунды)
        if current_time - self.action_time < 1.5:
            if not hasattr(self, 'attack_chosen'):
                self.attack = self.choose_attack()
                attack_name = self.attack_names.get(self.attack, self.attack.upper())
                self.action_text = f"{self.name} ИСПОЛЬЗУЕТ {attack_name}!"
                self.speech_text = self.get_dialogue(self.attack)
                self.update_speech_bubble(self.speech_text)
                self.attack_chosen = True
            return True
        
        # Фаза 2: Нанесение урона (между 1.5 и 2.5 секундами)
        elif current_time - self.action_time < 2.5:
            if not hasattr(self, 'damage_dealt'):
                damage = random.randint(15, 25)
                player.take_damage(damage)
                self.damage_dealt = True
                attack_name = self.attack_names.get(self.attack, self.attack.upper())
                self.action_text = f"{attack_name} НАНЕС {damage} УРОНА!"
            return True
        
        # Фаза 3: Завершение хода (после 2.5 секунд)
        else:
            self.turn = False
            player.turn = True
            if hasattr(self, 'attack_chosen'):
                del self.attack_chosen
            if hasattr(self, 'damage_dealt'):
                del self.damage_dealt
            return False

# Система боя
class BattleSystem:
    @staticmethod
    def player_action(player, enemy, action: str, weapon: str):
        if action == "dodge":
            if random.random() < player.actions["dodge"]["chance"]:
                enemy.speech_text = enemy.get_dialogue("dodge")
                enemy.update_speech_bubble(enemy.speech_text)
                enemy.speech_time = time.time()
                return "dodge_success", 0
            else:
                damage = random.randint(10, 20)
                player.take_damage(damage)
                enemy.speech_text = "ПОПАДАНИЕ! ПРИНИМАЙ УДАР!"
                enemy.update_speech_bubble(enemy.speech_text)
                enemy.speech_time = time.time()
                return "dodge_fail", damage
                
        elif action == "attack":
            if random.random() < player.weapons[weapon]["chance"]:
                damage = player.weapons[weapon]["damage"]
                enemy.take_damage(damage)
                enemy.speech_text = enemy.get_dialogue("attack")
                enemy.update_speech_bubble(enemy.speech_text)
                enemy.speech_time = time.time()
                return "attack_success", damage
            else:
                enemy.speech_text = "ПРОМАХ! ПОПРОБУЙ ЕЩЕ РАЗ!"
                enemy.update_speech_bubble(enemy.speech_text)
                enemy.speech_time = time.time()
                return "attack_fail", 0
                
        elif action == "ignore":
            damage = random.randint(20, 30)
            player.take_damage(damage)
            enemy.speech_text = enemy.get_dialogue("ignore")
            enemy.update_speech_bubble(enemy.speech_text)
            enemy.speech_time = time.time()
            return "ignore", damage
            
        return "none", 0

# Класс игры
class SpaceWarGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("КОСМИЧЕСКАЯ ВОЙНА v1.3")
        self.clock = pygame.time.Clock()
        self.state = "loading"
        self.loading_progress = 0
        self.loading_start_time = time.time()
        
        # Создаем игрока и врагов
        self.player = None
        self.enemies = [
            Enemy("КОРВЕТ 'МОЛНИЯ'", 120, FastAttackStrategy(), "enemy1.png"),
            Enemy("ЛИНКОР 'ТИТАН'", 200, HeavyAttackStrategy(), "enemy2.png")
        ]
        self.current_enemy = None
        self.selected_weapon = "laser"
        
        # Для ввода никнейма
        self.nickname = ""
        self.input_active = True
        self.nickname_rect = pygame.Rect(300, 300, 200, 40)
        
        # Статистика
        self.leaderboard = []
        self.load_leaderboard()
        
        # Создаем ретро-стиль
        self.create_retro_assets()
        
        # Инициализация UI
        self.init_ui()
    
    def create_retro_assets(self):
        # Ретро-фон для диалогового окна
        self.dialog_bg = pygame.Surface((700, 120))
        self.dialog_bg.fill((0, 0, 60))
        for i in range(0, 700, 4):
            pygame.draw.line(self.dialog_bg, (0, 120, 200), (i, 0), (i, 120), 1)
        
        # Ретро-кнопки
        self.button_normal = pygame.Surface((180, 50))
        self.button_normal.fill((0, 0, 60))
        pygame.draw.rect(self.button_normal, (0, 200, 200), (0, 0, 180, 50), 2)
        
        self.button_hover = pygame.Surface((180, 50))
        self.button_hover.fill((0, 40, 80))
        pygame.draw.rect(self.button_hover, (0, 200, 200), (0, 0, 180, 50), 2)
        
        # Ретро-панель здоровья
        self.health_bar_bg = pygame.Surface((202, 22))
        self.health_bar_bg.fill((0, 0, 60))
        pygame.draw.rect(self.health_bar_bg, (0, 200, 200), (0, 0, 202, 22), 2)
    
    def load_leaderboard(self):
        try:
            with open("leaderboard.json", "r") as f:
                data = json.load(f)
                if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                    self.leaderboard = data
                else:
                    self.leaderboard = []
        except (FileNotFoundError, json.JSONDecodeError):
            self.leaderboard = []
    
    def save_leaderboard(self):
        with open("leaderboard.json", "w") as f:
            json.dump(self.leaderboard, f)
    
    def add_to_leaderboard(self, nickname: str, wins: int):
        existing = next((item for item in self.leaderboard if item["nickname"] == nickname), None)
        if existing:
            if wins > existing["wins"]:
                existing["wins"] = wins
        else:
            self.leaderboard.append({"nickname": nickname, "wins": wins})
        
        self.leaderboard.sort(key=lambda x: x["wins"], reverse=True)
        self.leaderboard = self.leaderboard[:10]
        self.save_leaderboard()
    
    def init_ui(self):
        # Кнопки действий игрока
        self.action_buttons = [
            {"rect": pygame.Rect(100, 500, 180, 50), "action": "dodge", "text": "УВОРОТ"},
            {"rect": pygame.Rect(310, 500, 180, 50), "action": "attack", "text": "ПРЯМОЙ УДАР"},
            {"rect": pygame.Rect(520, 500, 180, 50), "action": "ignore", "text": "ИГНОРИРОВАТЬ"}
        ]
        
        # Кнопки выбора оружия
        self.weapon_buttons = [
            {"rect": pygame.Rect(650, 150, 120, 40), "weapon": "laser", "text": "ЛАЗЕР (35)"},
            {"rect": pygame.Rect(650, 200, 120, 40), "weapon": "ion", "text": "ИОН (25)"},
            {"rect": pygame.Rect(650, 250, 120, 40), "weapon": "shield", "text": "ЩИТ (15)"}
        ]
        
        # Кнопка выбора противника
        self.enemy_buttons = [
            {"rect": pygame.Rect(200, 300, 180, 50), "enemy": self.enemies[0], "text": "КОРВЕТ 'МОЛНИЯ'"},
            {"rect": pygame.Rect(450, 300, 180, 50), "enemy": self.enemies[1], "text": "ЛИНКОР 'ТИТАН'"}
        ]
        
        # Кнопка для статистики
        self.stats_button = {"rect": pygame.Rect(650, 20, 120, 30), "text": "СТАТИСТИКА"}
        
        # Кнопка возврата в меню
        self.back_button = {"rect": pygame.Rect(50, 20, 120, 30), "text": "В МЕНЮ"}
        
        # Кнопка в game_over
        self.menu_button = {"rect": pygame.Rect(300, 350, 200, 50), "text": "В ГЛАВНОЕ МЕНЮ"}
    
    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN and self.state == "nickname":
                    if event.key == pygame.K_RETURN and self.nickname:
                        self.player = Player(self.nickname)
                        self.state = "menu"
                    elif event.key == pygame.K_BACKSPACE:
                        self.nickname = self.nickname[:-1]
                    elif len(self.nickname) < 15 and event.unicode.isprintable():
                        self.nickname += event.unicode
            
            # Обновление состояния игры
            self.update()
            
            # Отрисовка
            self.draw()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def handle_click(self, pos):
        if self.state == "menu":
            for button in self.enemy_buttons:
                if button["rect"].collidepoint(pos):
                    self.current_enemy = button["enemy"]
                    self.current_enemy.reset()
                    if self.player is None:
                        self.player = Player("ИГРОК")
                    self.player.reset()
                    self.player.turn = True
                    self.selected_weapon = "laser"
                    self.state = "battle"
                    return
            
            if self.stats_button["rect"].collidepoint(pos):
                self.state = "stats"
        
        elif self.state == "battle":
            # Обработка выбора оружия
            for button in self.weapon_buttons:
                if button["rect"].collidepoint(pos):
                    self.selected_weapon = button["weapon"]
                    return
            
            # Обработка действий игрока
            if self.player.turn:
                for button in self.action_buttons:
                    if button["rect"].collidepoint(pos):
                        self.play_round(button["action"])
                        return
            
            if self.back_button["rect"].collidepoint(pos):
                self.state = "menu"
        
        elif self.state == "stats":
            if self.back_button["rect"].collidepoint(pos):
                self.state = "menu"
        
        elif self.state == "game_over":
            if self.menu_button["rect"].collidepoint(pos):
                self.state = "menu"
    
    def play_round(self, player_action: str):
        result, damage = BattleSystem.player_action(self.player, self.current_enemy, player_action, self.selected_weapon)
        
        # Устанавливаем текст действия
        if result == "dodge_success":
            action_text = "УВОРОТ ПРОШЕЛ УСПЕШНО!"
        elif result == "dodge_fail":
            action_text = f"УВЕРНУТЬСЯ НЕ ВЫШЛО! -{damage} HP"
        elif result == "attack_success":
            action_text = f"ПРЯМОЙ УДАР ПРОШЕЛ УСПЕШНО! -{damage} HP"
        elif result == "attack_fail":
            action_text = "УДАР НЕ ПРОШЕЛ, ПРОТИВНИК УВЕРНУЛСЯ!"
        elif result == "ignore":
            action_text = f"ПРОТИВНИК АТАКУЕТ! -{damage} HP"
        
        self.player.action_text = action_text
        self.player.action_time = time.time()
        
        # Меняем ход
        self.player.turn = False
        self.current_enemy.turn = True
        self.current_enemy.action_time = time.time()
        
        # Проверка конца игры
        if not self.player.is_alive():
            self.state = "game_over"
            self.current_enemy.speech_text = f"ПОБЕДА ЗА {self.current_enemy.name}!"
            self.current_enemy.update_speech_bubble(self.current_enemy.speech_text)
            self.current_enemy.speech_time = time.time()
        elif not self.current_enemy.is_alive():
            self.player.wins += 1
            self.state = "game_over"
            self.current_enemy.speech_text = f"ПОБЕДА ЗА {self.player.name}!"
            self.current_enemy.update_speech_bubble(self.current_enemy.speech_text)
            self.current_enemy.speech_time = time.time()
    
    def update(self):
        if self.state == "loading":
            if time.time() - self.loading_start_time > 3:
                self.state = "nickname"
        
        elif self.state == "battle":
            # Обработка хода противника
            if self.current_enemy.turn:
                if not self.current_enemy.perform_enemy_turn(self.player):
                    # Если действие врага завершено, проверяем конец игры
                    if not self.player.is_alive():
                        self.state = "game_over"
                        self.current_enemy.speech_text = f"ПОБЕДА ЗА {self.current_enemy.name}!"
                        self.current_enemy.update_speech_bubble(self.current_enemy.speech_text)
                        self.current_enemy.speech_time = time.time()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Ретро-звездный фон
        for _ in range(5):
            pygame.draw.circle(self.screen, WHITE, 
                             (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)), 
                             1)
        
        if self.state == "loading":
            self.draw_loading_screen()
        elif self.state == "nickname":
            self.draw_nickname_input()
        elif self.state == "menu":
            self.draw_menu()
        elif self.state == "battle":
            self.draw_battle()
        elif self.state == "stats":
            self.draw_stats()
        elif self.state == "game_over":
            self.draw_game_over()
    
    def draw_loading_screen(self):
        progress = min(1.0, (time.time() - self.loading_start_time) / 3)
        
        # Текст
        title = font_large.render("КОСМИЧЕСКАЯ ВОЙНА", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        
        # Ретро-прогресс бар
        pygame.draw.rect(self.screen, (0, 0, 60), (200, 300, 400, 20))
        pygame.draw.rect(self.screen, (0, 200, 200), (200, 300, 400 * progress, 20))
        pygame.draw.rect(self.screen, CYAN, (200, 300, 400, 20), 2)
        
        # Текст загрузки
        loading_text = font_medium.render(f"ЗАГРУЗКА... {int(progress * 100)}%", True, CYAN)
        self.screen.blit(loading_text, (SCREEN_WIDTH//2 - loading_text.get_width()//2, 330))
    
    def draw_nickname_input(self):
        # Текст
        title = font_large.render("ВВЕДИТЕ ВАШ НИКНЕЙМ", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        
        # Ретро-поле ввода
        pygame.draw.rect(self.screen, (0, 0, 60), self.nickname_rect)
        pygame.draw.rect(self.screen, CYAN, self.nickname_rect, 2)
        
        # Текст в поле ввода
        if self.nickname:
            nickname_text = font_medium.render(self.nickname, True, CYAN)
        else:
            nickname_text = font_medium.render("ВВЕДИТЕ НИК", True, (100, 100, 180))
        
        self.screen.blit(nickname_text, (self.nickname_rect.x + 10, self.nickname_rect.y + 10))
        
        # Подсказка
        hint = font_small.render("НАЖМИТЕ ENTER ДЛЯ ПОДТВЕРЖДЕНИЯ", True, CYAN)
        self.screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 360))
    
    def draw_menu(self):
        # Текст
        title = font_large.render("ВЫБЕРИТЕ ПРОТИВНИКА", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        
        # Кнопки выбора противника
        for button in self.enemy_buttons:
            mouse_pos = pygame.mouse.get_pos()
            if button["rect"].collidepoint(mouse_pos):
                self.screen.blit(self.button_hover, button["rect"].topleft)
            else:
                self.screen.blit(self.button_normal, button["rect"].topleft)
            
            text = font_small.render(button["text"], True, CYAN)
            self.screen.blit(text, (
                button["rect"].x + button["rect"].width//2 - text.get_width()//2,
                button["rect"].y + button["rect"].height//2 - text.get_height()//2
            ))
        
        # Кнопка статистики
        mouse_pos = pygame.mouse.get_pos()
        if self.stats_button["rect"].collidepoint(mouse_pos):
            self.screen.blit(pygame.transform.scale(self.button_hover, (120, 30)), self.stats_button["rect"].topleft)
        else:
            self.screen.blit(pygame.transform.scale(self.button_normal, (120, 30)), self.stats_button["rect"].topleft)
        
        text = font_small.render(self.stats_button["text"], True, CYAN)
        self.screen.blit(text, (
            self.stats_button["rect"].x + self.stats_button["rect"].width//2 - text.get_width()//2,
            self.stats_button["rect"].y + self.stats_button["rect"].height//2 - text.get_height()//2
        ))
    
    def draw_battle(self):
        # Информация о противнике
        enemy_info = font_medium.render(f"ПРОТИВНИК: {self.current_enemy.name}", True, CYAN)
        self.screen.blit(enemy_info, (50, 50))
        
        # Изображение противника
        self.screen.blit(self.current_enemy.image, (SCREEN_WIDTH//2 - 125, 80))
        
        # Облачко реплики врага (если есть и не старше 3 секунд)
        if self.current_enemy.speech_text and time.time() - self.current_enemy.speech_time < 3:
            self.screen.blit(self.current_enemy.speech_bubble, (SCREEN_WIDTH//2 - 150, 30))
        
        # Полоски HP
        self.draw_health_bar(50, 80, 200, 20, self.player.current_hp / self.player.max_hp, GREEN)
        self.draw_health_bar(550, 80, 200, 20, self.current_enemy.current_hp / self.current_enemy.max_hp, RED)
        
        # Диалоговое окно
        self.screen.blit(self.dialog_bg, (50, 350))
        pygame.draw.rect(self.screen, CYAN, (50, 350, 700, 120), 2)
        
        # Текст действия (игрока или врага)
        if self.player.action_text and time.time() - self.player.action_time < 2:
            action_text = font_medium.render(self.player.action_text, True, YELLOW)
            self.screen.blit(action_text, (60, 380))
        elif self.current_enemy.action_text and time.time() - self.current_enemy.action_time < 2:
            action_text = font_medium.render(self.current_enemy.action_text, True, YELLOW)
            self.screen.blit(action_text, (60, 380))
        elif not self.player.turn:
            wait_text = font_medium.render("ХОД ПРОТИВНИКА...", True, YELLOW)
            self.screen.blit(wait_text, (60, 380))
        
        # Индикатор чей ход
        turn_text = font_medium.render("ВАШ ХОД" if self.player.turn else "ХОД ПРОТИВНИКА", True, YELLOW)
        self.screen.blit(turn_text, (SCREEN_WIDTH//2 - turn_text.get_width()//2, 320))
        
        # Кнопки действий (только во время хода игрока)
        if self.player.turn:
            for button in self.action_buttons:
                mouse_pos = pygame.mouse.get_pos()
                if button["rect"].collidepoint(mouse_pos):
                    self.screen.blit(self.button_hover, button["rect"].topleft)
                else:
                    self.screen.blit(self.button_normal, button["rect"].topleft)
                
                text = font_small.render(button["text"], True, CYAN)
                self.screen.blit(text, (
                    button["rect"].x + button["rect"].width//2 - text.get_width()//2,
                    button["rect"].y + button["rect"].height//2 - text.get_height()//2
                ))
        
        # Панель выбора оружия
        pygame.draw.rect(self.screen, (0, 0, 60), (640, 140, 140, 170))
        pygame.draw.rect(self.screen, CYAN, (640, 140, 140, 170), 2)
        weapon_title = font_medium.render("ОРУЖИЕ:", True, CYAN)
        self.screen.blit(weapon_title, (650, 110))
        
        for button in self.weapon_buttons:
            color = YELLOW if self.selected_weapon == button["weapon"] else CYAN
            mouse_pos = pygame.mouse.get_pos()
            if button["rect"].collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (0, 40, 80), button["rect"])
            else:
                pygame.draw.rect(self.screen, (0, 0, 60), button["rect"])
            pygame.draw.rect(self.screen, color, button["rect"], 2)
            
            text = font_small.render(button["text"], True, color)
            self.screen.blit(text, (
                button["rect"].x + button["rect"].width//2 - text.get_width()//2,
                button["rect"].y + button["rect"].height//2 - text.get_height()//2
            ))
        
        # Кнопка возврата
        mouse_pos = pygame.mouse.get_pos()
        if self.back_button["rect"].collidepoint(mouse_pos):
            self.screen.blit(pygame.transform.scale(self.button_hover, (120, 30)), self.back_button["rect"].topleft)
        else:
            self.screen.blit(pygame.transform.scale(self.button_normal, (120, 30)), self.back_button["rect"].topleft)
        
        text = font_small.render(self.back_button["text"], True, CYAN)
        self.screen.blit(text, (
            self.back_button["rect"].x + self.back_button["rect"].width//2 - text.get_width()//2,
            self.back_button["rect"].y + self.back_button["rect"].height//2 - text.get_height()//2
        ))
    
    def draw_stats(self):
        # Заголовок
        title = font_large.render("ТАБЛИЦА ЛИДЕРОВ", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Статистика игрока
        if self.player:
            player_stats = font_medium.render(f"ИГРОК: {self.player.name} | ПОБЕД: {self.player.wins}", True, CYAN)
            self.screen.blit(player_stats, (SCREEN_WIDTH//2 - player_stats.get_width()//2, 120))
        
        # Таблица лидеров
        headers = ["МЕСТО", "ИГРОК", "ПОБЕД"]
        y_pos = 180
        
        # Заголовки таблицы
        for i, header in enumerate(headers):
            text = font_medium.render(header, True, YELLOW)
            self.screen.blit(text, (150 + i * 200, y_pos))
        
        y_pos += 40
        
        # Данные таблицы
        for i, record in enumerate(self.leaderboard[:10]):
            place = font_medium.render(str(i+1), True, CYAN)
            nickname = font_medium.render(record["nickname"], True, CYAN)
            wins = font_medium.render(str(record["wins"]), True, CYAN)
            
            self.screen.blit(place, (150, y_pos))
            self.screen.blit(nickname, (350, y_pos))
            self.screen.blit(wins, (550, y_pos))
            
            y_pos += 30
        
        # Кнопка возврата
        mouse_pos = pygame.mouse.get_pos()
        if self.back_button["rect"].collidepoint(mouse_pos):
            self.screen.blit(pygame.transform.scale(self.button_hover, (120, 30)), self.back_button["rect"].topleft)
        else:
            self.screen.blit(pygame.transform.scale(self.button_normal, (120, 30)), self.back_button["rect"].topleft)
        
        text = font_small.render(self.back_button["text"], True, CYAN)
        self.screen.blit(text, (
            self.back_button["rect"].x + self.back_button["rect"].width//2 - text.get_width()//2,
            self.back_button["rect"].y + self.back_button["rect"].height//2 - text.get_height()//2
        ))
    
    def draw_game_over(self):
        # Результат игры
        if self.player.is_alive():
            result_text = font_large.render("ПОБЕДА!", True, GREEN)
            self.add_to_leaderboard(self.player.name, self.player.wins)
        else:
            result_text = font_large.render("ПОРАЖЕНИЕ", True, RED)
        
        self.screen.blit(result_text, (SCREEN_WIDTH//2 - result_text.get_width()//2, 200))
        
        # Статистика
        stats_text = font_medium.render(f"ПОБЕД: {self.player.wins}", True, CYAN)
        self.screen.blit(stats_text, (SCREEN_WIDTH//2 - stats_text.get_width()//2, 260))
        
        # Облачко реплики врага
        if self.current_enemy.speech_text:
            self.screen.blit(self.current_enemy.speech_bubble, (SCREEN_WIDTH//2 - 150, 300))
        
        # Кнопка возврата
        mouse_pos = pygame.mouse.get_pos()
        if self.menu_button["rect"].collidepoint(mouse_pos):
            self.screen.blit(pygame.transform.scale(self.button_hover, (200, 50)), self.menu_button["rect"].topleft)
        else:
            self.screen.blit(pygame.transform.scale(self.button_normal, (200, 50)), self.menu_button["rect"].topleft)
        
        text = font_medium.render(self.menu_button["text"], True, CYAN)
        self.screen.blit(text, (
            self.menu_button["rect"].x + self.menu_button["rect"].width//2 - text.get_width()//2,
            self.menu_button["rect"].y + self.menu_button["rect"].height//2 - text.get_height()//2
        ))
    
    def draw_health_bar(self, x, y, width, height, ratio, color):
        self.screen.blit(self.health_bar_bg, (x-1, y-1))
        pygame.draw.rect(self.screen, color, (x, y, width * ratio, height))

# Создаем более интересные изображения врагов
def create_enemy_images():
    # Корвет "Молния"
    enemy1_img = pygame.Surface((250, 250), pygame.SRCALPHA)
    pygame.draw.polygon(enemy1_img, (0, 150, 255), [(125, 10), (10, 240), (240, 240)])  # Основной корпус
    pygame.draw.circle(enemy1_img, (255, 255, 0), (125, 60), 20)  # Центральный реактор
    pygame.draw.line(enemy1_img, (255, 0, 0), (50, 100), (200, 100), 3)  # Лазерная пушка
    pygame.draw.line(enemy1_img, (255, 0, 0), (100, 150), (150, 150), 3)  # Дополнительное оружие
    
    # Линкор "Титан"
    enemy2_img = pygame.Surface((250, 250), pygame.SRCALPHA)
    pygame.draw.rect(enemy2_img, (200, 100, 0), (50, 50, 150, 150))  # Основной корпус
    pygame.draw.rect(enemy2_img, (150, 150, 150), (80, 80, 90, 90))  # Центральная часть
    pygame.draw.circle(enemy2_img, (255, 0, 0), (125, 125), 30)  # Реактор
    pygame.draw.rect(enemy2_img, (100, 100, 100), (30, 100, 20, 50))  # Левое оружие
    pygame.draw.rect(enemy2_img, (100, 100, 100), (200, 100, 20, 50))  # Правое оружие
    
    # Сохраняем изображения
    pygame.image.save(enemy1_img, "enemy1.png")
    pygame.image.save(enemy2_img, "enemy2.png")

# Запуск игры
if __name__ == "__main__":
    create_enemy_images()
    game = SpaceWarGame()
    game.run()
