import pyglet
import random

from pyglet import shapes
from pyglet import image

top_bar_height = 50
width, height = 400, 400 + top_bar_height

board_width, board_height = 22, 22
tile_width, tile_height = width/board_width, (height - top_bar_height)/board_height
mine_count = 99

window = pyglet.window.Window(width, height, resizable=True)
game_state = 'running'
tiles = []

relative_surrounding = [
                    1,
                    -1,
                    board_width + 1,
                    board_width,
                    board_width - 1,
                    -board_width + 1,
                    -board_width,
                    -board_width - 1
                ]

sprite_sheet = image.load('sprites/tiles.png')
sprite_side = 16

sprite_regions = {
        '1': (sprite_side*0, 0, sprite_side, sprite_side),
        '2': (sprite_side*1, 0, sprite_side, sprite_side),
        '3': (sprite_side*2, 0, sprite_side, sprite_side),
        '4': (sprite_side*3, 0, sprite_side, sprite_side),
        '5': (sprite_side*4, 0, sprite_side, sprite_side),
        '6': (sprite_side*5, 0, sprite_side, sprite_side),
        '7': (sprite_side*6, 0, sprite_side, sprite_side),
        '8': (sprite_side*7, 0, sprite_side, sprite_side),
        'unknown': (sprite_side*0, sprite_side, sprite_side, sprite_side),
        '0': (sprite_side*1, sprite_side, sprite_side, sprite_side),
        'flagged': (sprite_side*2, sprite_side, sprite_side, sprite_side),
        'question1': (sprite_side*3, sprite_side, sprite_side, sprite_side),
        'question2': (sprite_side*4, sprite_side, sprite_side, sprite_side),
        'mine': (sprite_side*5, sprite_side, sprite_side, sprite_side),
        'red_mine': (sprite_side*6, sprite_side, sprite_side, sprite_side),
        'crossed_mine': (sprite_side*7, sprite_side, sprite_side, sprite_side)
        }

class Tile():
    def __init__(self, x=0, y=0, i=0):
        self.board_coordinates = (x, y)
        self.index = i

        self.coordinates = {'x': x*tile_width, 'y': y*tile_height}
        self.mine_count = 0
        self.revealed = False
        self.flagged = False
        self.mine = False
        
        self.sprite_name = 'unknown'
        self.change_sprite()

    def change_sprite(self):
        self.sprite = pyglet.sprite.Sprite(
                sprite_sheet.get_region(*sprite_regions[self.sprite_name]), 
                                        **self.coordinates
                )
        self.sprite.scale_x = tile_width/sprite_side
        self.sprite.scale_y = tile_height/sprite_side
    
    def resize(self):
        x, y = self.board_coordinates
        self.coordinates = {'x': x*tile_width, 'y': y*tile_height}
        self.change_sprite()

    def surrounding(self):
        modified_surrounding = relative_surrounding
        if self.index % board_width == 0:  # left edge
            modified_surrounding = [i for i in modified_surrounding if i % board_width != board_width - 1]       
        if self.index % board_width == board_width - 1:  # right edge
            modified_surrounding = [i for i in modified_surrounding if i % board_width != 1] 
        if self.index // board_width == board_height -1:  # top
            modified_surrounding = [i for i in modified_surrounding if (i) // (board_width - 1) != 1]
        if self.index // board_width == 0:  # bottom
            modified_surrounding = [i for i in modified_surrounding if (-i) // (board_width - 1) != 1]
        
        return [tiles[self.index + i] for i in modified_surrounding]
            

    def count_mines(self):
        for tile in self.surrounding():
            if tile.mine:        
                self.mine_count += 1

    def collision(self, x, y):
        if self.coordinates['x'] <= x <= self.coordinates['x'] + tile_width and \
           self.coordinates['y'] <= y <= self.coordinates['y'] + tile_height:
            return True
    
    def mouse_press(self):
        pass

    def mouse_release(self, key):  # add symbol to differentiate between left and right
        global game_state
        if self.revealed:
            return
        if key == pyglet.window.mouse.RIGHT:
            self.flagged = not self.flagged
            self.sprite_name = 'flagged' if self.flagged else 'unknown'
            self.change_sprite()
            return
        elif key == pyglet.window.mouse.LEFT:
            if self.flagged:
                return
            if self.mine:
                self.sprite_name = 'red_mine'
                self.change_sprite()
                for tile in tiles:
                    if tile.mine and tile != self:
                        tile.sprite_name = 'mine'
                        tile.change_sprite()
                game_state = 'over'
            else:
                self.reveal()

    def reveal(self):
        self.sprite_name = str(self.mine_count)
        self.change_sprite()
        if self.revealed == True:
            return
        else:
            self.revealed = True
        if self.mine_count == 0:
           for tile in self.surrounding():
                tile.reveal()


@window.event
def on_draw():  # draw to window
    window.clear()

    for tile in tiles:
        tile.sprite.draw()

@window.event
def on_resize(_width, _height):
    global width, height, top_bar_height
    global tile_width, tile_height

    top_bar_height = 50
    width, height = _width, _height

    board_width, board_height = 22, 22
    tile_width, tile_height = width/board_width, (height - top_bar_height)/board_height
    mine_count = 99 
    
    for tile in tiles:
        tile.resize()

@window.event
def on_key_press(symbol, modifiers):  # keybinds for application
    pass  # add keybinds

@window.event
def on_mouse_press(x, y, button, modifiers):
    pass

@window.event
def on_mouse_release(x, y, button, modifiers):
    if game_state != 'over':
        for tile in tiles:
            if tile.collision(x, y):
                tile.mouse_release(button)

def init():
    global tiles
    tiles = []
    for y in range(board_height):
        for x in range(board_width):
            tiles.append(Tile(x=x, y=y, i=x + y*board_width))

    for i in random.sample(range(len(tiles)), mine_count):
        tiles[i].mine = True

    for tile in tiles:
        tile.count_mines()



if __name__ == '__main__':
    init()
    pyglet.app.run()
