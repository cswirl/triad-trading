import pygame

def play_sound():
    pygame.mixer.init()
    pygame.mixer.music.load("assets/soundfx/notification-4.mp3")
    pygame.mixer.music.play()