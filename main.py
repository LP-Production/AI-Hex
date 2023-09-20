import pygame
from game import *
from player import *


if __name__ == '__main__':
    pygame.init()
    game = Game(board_size=13, player_1=Human_player(1), player_2=AI_random_player(2))
    game.start()