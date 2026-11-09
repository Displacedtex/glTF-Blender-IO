import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('assembly_export', Path(__file__).with_name('export_assembly.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Object(dict):
    def __init__(self, name, parent=None, **metadata):
        super().__init__(metadata)
        self.name = name
        self.parent = parent


class MetadataTests(unittest.TestCase):
    def test_attached_components_keep_identity(self):
        layer = Object('support', layerId='support-layer')
        pipe = Object('pipe', parent=layer, componentId='pipe-1', id='meprough', part='plumbing')
        assembly_id, components, layers = module.validate_objects([layer, pipe])
        self.assertEqual((assembly_id, len(components), len(layers)), ('meprough', 1, 1))

    def test_detached_component_is_rejected(self):
        layer = Object('support', layerId='support-layer')
        pipe = Object('pipe', componentId='pipe-1', id='meprough', part='plumbing')
        with self.assertRaisesRegex(ValueError, 'detached'):
            module.validate_objects([layer, pipe])

    def test_duplicate_identity_is_rejected(self):
        layer = Object('support', layerId='support-layer')
        pipes = [Object(str(index), parent=layer, componentId='pipe-1', id='meprough', part='plumbing')
                 for index in range(2)]
        with self.assertRaisesRegex(ValueError, 'unique'):
            module.validate_objects([layer, *pipes])


if __name__ == '__main__':
    unittest.main()
