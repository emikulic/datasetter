import json
from pathlib import Path
from unittest import mock, TestCase

from PIL import Image

from add import main
import tempfile


class MainTestCase(TestCase):
    def test_args(self):
        with tempfile.TemporaryDirectory() as img_dir:
            img_filename = Path(img_dir) / 'img.jpg'
            img = Image.new('RGB', (123, 456))
            img.save(img_filename)
            state_filename = Path(img_dir) / 'state.json'

            expected = {
                'fn': str(img_filename),
                'md5': mock.ANY,
                'fsz': mock.ANY,
                'orig_w': 123,
                'orig_h': 456,
                'rot': 0,
                'needs_rebuild': 1,
                'w': 123,
                'h': 123,
                'x': 0,
                'y': 166,
                'n': 0,
            }

            with mock.patch('sys.argv', ['add.py', str(state_filename), img_dir]):
                main()
                with open(state_filename) as fp:
                    state = json.load(fp)
                    self.assertDictEqual(state, expected)
