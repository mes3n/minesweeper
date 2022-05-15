import pyglet
import random

from pyglet import image

top_bar_height = 50
border_width = 5
width, height = 300*2 + border_width*2, 160*2 + top_bar_height + border_width*2

factor_x, factor_y = 1, 1

# current defualt settings are for hardmode
board_width, board_height = 30, 16
tile_width, tile_height = (width - border_width*2)/board_width, (height - top_bar_height - border_width*2)/board_height
mine_count = 99

background_color = (191, 191, 191)

window = pyglet.window.Window(width, height, resizable=True)
pyglet.gl.glClearColor(0.75, 0.75, 0.75, 1)

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

tiles_side = 16
tile_sprites = {
    'sheet': image.load('sprites/tiles.png'),
    'side': tiles_side,

    'regions': {

        '1':            (tiles_side*0, 0,           tiles_side, tiles_side),
        '2':            (tiles_side*1, 0,           tiles_side, tiles_side),
        '3':            (tiles_side*2, 0,           tiles_side, tiles_side),
        '4':            (tiles_side*3, 0,           tiles_side, tiles_side),
        '5':            (tiles_side*4, 0,           tiles_side, tiles_side),
        '6':            (tiles_side*5, 0,           tiles_side, tiles_side),
        '8':            (tiles_side*7, 0,           tiles_side, tiles_side),
        '7':            (tiles_side*6, 0,           tiles_side, tiles_side),
        'unknown':      (tiles_side*0, tiles_side, tiles_side, tiles_side),
        '0':            (tiles_side*1, tiles_side, tiles_side, tiles_side),
        'flagged':      (tiles_side*2, tiles_side, tiles_side, tiles_side),
        'question1':    (tiles_side*3, tiles_side, tiles_side, tiles_side),
        'question2':    (tiles_side*4, tiles_side, tiles_side, tiles_side),
        'mine':         (tiles_side*5, tiles_side, tiles_side, tiles_side),
        'red_mine':     (tiles_side*6, tiles_side, tiles_side, tiles_side),
        'crossed_mine': (tiles_side*7, tiles_side, tiles_side, tiles_side)

    }
}
# could probably be reworked into "pyglet.image.ImageGrid"

faces_side = 24
face_sprites = {
    'sheet': image.load('sprites/faces.png'),
    'side': faces_side,

    'regions': {

        'happy':            (faces_side*0, 0, faces_side, faces_side),
        'happy_pressed':    (faces_side*1, 0, faces_side, faces_side),
        'chocked':          (faces_side*2, 0, faces_side, faces_side),
        'cool':             (faces_side*3, 0, faces_side, faces_side),
        'dead':             (faces_side*4, 0, faces_side, faces_side)

    }
}

scores_width = 13
scores_height = 23
scores_sprites = {
    'sheet': image.load('sprites/scores.png'),
    'side': (scores_width, scores_height),

    'regions': {

        '0': (scores_width*0, 0, scores_width, scores_height),
        '1': (scores_width*1, 0, scores_width, scores_height),
        '2': (scores_width*2, 0, scores_width, scores_height),
        '3': (scores_width*3, 0, scores_width, scores_height),
        '4': (scores_width*4, 0, scores_width, scores_height),
        '5': (scores_width*5, 0, scores_width, scores_height),
        '6': (scores_width*6, 0, scores_width, scores_height),
        '7': (scores_width*7, 0, scores_width, scores_height),
        '8': (scores_width*8, 0, scores_width, scores_height),
        '9': (scores_width*9, 0, scores_width, scores_height)

    }
}

class Button():
    def __init__(self, x=0, y=0, w=tile_width, h=tile_height, sprites=tile_sprites, sprite_name='unknown', batch=None):
        self.coordinates = {'x': x + border_width, 'y': y + border_width}

        self.width, self.height = w, h

        self.sprites = sprites

        self.batch = batch
        self.sprite_name = sprite_name
        self.change_sprite()

    def change_sprite(self):
        self.sprite = pyglet.sprite.Sprite(
                self.sprites['sheet'].get_region(*self.sprites['regions'][self.sprite_name]),
                                        **self.coordinates, batch=self.batch if self.batch else None
                )
        self.sprite.update(
            scale_x = (self.width / self.sprites['side']),
            scale_y = (self.height / self.sprites['side'])
        )

    def resize(self):
        self.coordinates = {'x': self.coordinates['x']*factor_x,
                            'y': self.coordinates['y']*factor_y}

        self.width *= factor_x
        self.height *= factor_y

        self.sprite.update(
            **self.coordinates,
            scale_x = (self.width / self.sprites['side']),
            scale_y = (self.height / self.sprites['side']),
            )

    def collision(self, x, y):
        if self.coordinates['x'] <= x <= self.coordinates['x'] + self.width and \
           self.coordinates['y'] <= y <= self.coordinates['y'] + self.height:
            return True


class Face(Button):
    def __init__(self, x=(width - faces_side)*0.5, y=(height - ((top_bar_height + faces_side)*0.5))):
        super().__init__(x=x, y=y, w=faces_side, h=faces_side, sprites=face_sprites, sprite_name='happy')

    def mouse_press(self):
        self.sprite_name = 'happy_pressed'
        self.change_sprite()

    def mouse_release(self):
        global game_state
        game_state = 'running'

        self.sprite_name = 'happy'
        self.change_sprite()

        restart()


class Tile(Button):
    def __init__(self, x=0, y=0, i=0, batch=None):
        super().__init__(x=x*tile_width, y=y*tile_height, batch=batch)

        self.board_coordinates = (x, y)
        self.index = i

        self.mine_count = 0
        self.revealed = False
        self.flagged = False
        self.mine = False


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


    def mouse_press(self):
        if not self.revealed and not self.flagged:
            self.sprite_name = '0'
            self.change_sprite()


    def mouse_release(self, key):

        if key == pyglet.window.mouse.RIGHT:  # toggle flagged
            if self.revealed:
                return
            self.flagged = not self.flagged
            self.sprite_name = 'flagged' if self.flagged else 'unknown'
            self.change_sprite()

            mines_left.value += (-1 if self.flagged else 1)
            mines_left.change_sprite()

        elif key == pyglet.window.mouse.LEFT:
            if self.flagged:
                return
            elif self.revealed:
                if self.mine_count == len([tile for tile in self.surrounding() if tile.flagged]):
                    for tile in self.surrounding():
                        tile.reveal()
            else:
                self.reveal()

        if len([tile for tile in tiles if not tile.revealed]) == mine_count:
            win()


    def reveal(self):
        if self.flagged or self.revealed:
            return
        elif self.mine:
            boom(self)
        else:

            self.sprite_name = str(self.mine_count)
            self.change_sprite()
            self.revealed = True

            if self.mine_count == 0:
               for tile in self.surrounding():
                    tile.reveal()


class Scores():
    def __init__(self, x=0, y=0, w=scores_width, h=scores_height, val=0, batch=None):
        self.coordinates = {'x': x + border_width, 'y': y + border_width}

        self.width, self.height = w, h

        self.value = val

        self.batch = batch
        self.sprite = []
        self.change_sprite()

    def change_sprite(self):
        self.sprite = []
        if self.value >= 0:
            str_num = (3 - len(str(self.value))) * '0' + str(self.value)
        else:
            str_num = '000'

        for i, num in enumerate(str_num):
            sprite = pyglet.sprite.Sprite(
                        scores_sprites['sheet'].get_region(*scores_sprites['regions'][num]),
                        **self.coordinates, batch=self.batch if self.batch else None
                    )
            sprite.update(
                x = self.coordinates['x'] + i*self.width,
                scale_x = (self.width / scores_sprites['side'][0]),
                scale_y = (self.height / scores_sprites['side'][1])
            )
            self.sprite.append(sprite)

    def resize(self):
        self.coordinates = {'x': self.coordinates['x']*factor_x,
                            'y': self.coordinates['y']*factor_y}

        self.width *= factor_x
        self.height *= factor_y

        for i, sprite in enumerate(self.sprite):
            sprite.update(
                x = self.coordinates['x'] + i*self.width,
                y = self.coordinates['y'],
                scale_x = (self.width / scores_sprites['side'][0]),
                scale_y = (self.height / scores_sprites['side'][1])
            )

@window.event
def on_draw():  # draw to window
    window.clear()

    face.sprite.draw()
    number_batch.draw()
    tiles_batch.draw()


@window.event
def on_resize(new_width, new_height):
    global width, height, top_bar_height
    global factor_x, factor_y

    factor_x = new_width / width
    factor_y = new_height / height

    width = new_width
    height = new_height
    top_bar_height *= factor_y

    face.resize()
    mines_left.resize()
    for tile in tiles:
        tile.resize()

@window.event
def on_key_press(symbol, modifiers):  # keybinds for application
    pass

@window.event
def on_mouse_drag(x, y, dx, dy, button, modifiers):

    if game_state != 'over' and game_state != 'won':
        face.sprite_name = 'chocked'
        face.change_sprite()

        for tile in tiles:
            if not tile.revealed:
                if tile.collision(x, y):
                    tile.mouse_press()
                elif tile.sprite_name == '0':
                    tile.sprite_name = 'unknown'
                    tile.change_sprite()

@window.event
def on_mouse_press(x, y, button, modifiers):
    if face.collision(x, y):
        face.mouse_press()

    if game_state != 'over' and game_state != 'won':
        face.sprite_name = 'chocked'
        face.change_sprite()
        for tile in tiles:
            if tile.collision(x, y):
                tile.mouse_press()

@window.event
def on_mouse_release(x, y, button, modifiers):
    if face.collision(x, y):
        face.mouse_release()

    if game_state != 'over' and game_state != 'won':
        face.sprite_name = 'happy'
        face.change_sprite()
        for tile in tiles:
            if tile.collision(x, y):
                tile.mouse_release(button)

def boom(exploded_mine):
    global game_state
    game_state = 'over'

    for tile in tiles:
        if tile == exploded_mine:
            tile.sprite_name = 'red_mine'
            tile.change_sprite()
        elif tile.mine and not tile.flagged:
            tile.sprite_name = 'mine'
            tile.change_sprite()
        elif tile.flagged and not tile.mine:
            tile.sprite_name = 'crossed_mine'
            tile.change_sprite()

    face.sprite_name = 'dead'
    face.change_sprite()


def win():
    global game_state
    game_state = 'won'

    face.sprite_name = 'cool'
    face.change_sprite()

    for tile in tiles:
        if tile.mine:
            tile.sprite_name = 'flagged'
            tile.change_sprite()
    mines_left.value = 0
    mines_left.change_sprite()

def restart():
    mines_left.value = mine_count
    mines_left.change_sprite()

    for tile in tiles:
        tile.mine_count = 0
        tile.revealed = False
        tile.flagged = False
        tile.mine = False

        tile.sprite_name = 'unknown'
        tile.change_sprite()

    for i in random.sample(range(len(tiles)), mine_count):
        tiles[i].mine = True

    for tile in tiles:
        tile.count_mines()

if __name__ == '__main__':

    face = Face()

    number_batch = pyglet.graphics.Batch()
    mines_left = Scores(x=0, y=(height - ((top_bar_height + scores_sprites['side'][1])*0.5)), val=mine_count, batch=number_batch)

    tiles_batch = pyglet.graphics.Batch()
    for y in range(board_height):
        for x in range(board_width):
            tiles.append(Tile(x=x, y=y, i=x + y*board_width, batch=tiles_batch))

    for i in random.sample(range(len(tiles)), mine_count):
        tiles[i].mine = True

    for tile in tiles:
        tile.count_mines()



    pyglet.app.run()
