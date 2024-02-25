import unittest
import utils

class TestUtils(unittest.TestCase):

    def test_play_sound(self):
        utils.play_sound()
        #warning - you will not hear the sound because the program terminates after quick
        # you need to place a debug break-point at the pass statement to hear the sound
        pass