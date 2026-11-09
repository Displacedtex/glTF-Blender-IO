# Multifamily Anatomy assembly export

This companion workflow prepares semantically tagged construction assemblies for the Three.js learning app. It preserves component identities, semantic layer parents, prerequisite-support tags. The app rebuilds installation clips from its learning manifest after export; imported seed animation is cleared to avoid exporting a hidden or displaced pose. It adds shallow edge bevels to larger meshes for lighting readability.

## Compatibility

Use the glTF exporter bundled with your installed Blender version by default. This fork's current main branch declares Blender 5.3 as its minimum version. Use `--exporter-path /path/to/glTF-Blender-IO/addons` only with a compatible Blender build. The script rejects an incompatible version before importing the assembly.

The runtime web app consumes `.glb` files and a separate learning manifest. Blender and its exporter run during asset authoring, outside the browser.

## Export

Generate an uncompressed seed with the Multifamily Anatomy app's `npm run assemblies:seed` command. The seed contains named `componentId` and `layerId` objects and custom properties for part identity and supporting construction.

```sh
blender --background --python integrations/multifamily-anatomy/export_assembly.py -- \
  --source /path/to/site/.sites-runtime/assembly-seeds/window.glb \
  --output /path/to/site/authoring/exports/window.glb \
  --save-blend /path/to/site/authoring/window.blend
```

Repeat for `meprough` and `roof`, then run the Site's `npm run assemblies:build` and `npm run assemblies:verify` commands. Those commands compress the assets, run Khronos glTF validation, check semantic identity, and compare imported playback and inspection geometry with the original teaching assemblies.

For later edits, open the `.blend`, preserve the named layer and component objects, and export GLB with Custom Properties enabled. Mesh children can be refined, but each teaching component must continue to own exactly one mesh. Keep prerequisite supports attached to their actual semantic layer. Record new component metadata and installation steps in the app manifest before extending a package.

## Checks

```sh
python -m unittest discover -s integrations/multifamily-anatomy -p 'test_*.py'
```

These tests verify metadata errors without requiring Blender. A real Blender round trip and the Site's geometry checks remain necessary when changing the authoring pipeline.

## Verified pilot

Tested with Blender 5.0.1 and its bundled Khronos glTF exporter 5.0.21. Window, MEP bay and roof-edge assemblies retained 230 component identities across 25 semantic layers. All 18 learning steps passed the app’s imported-versus-procedural playback and layer-inspection geometry comparisons. The optional fork-exporter path requires Blender 5.3 or newer and has not been exercised on that runtime. No exporter core files are changed.
