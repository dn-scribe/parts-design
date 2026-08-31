# parts-design

Parametric mechanical parts, designed as FreeCAD Python scripts. Each part lives in its own
folder under `designs/`; running its `generate.py` regenerates the model and exports
fabrication-ready outputs (STL, GLB, STEP, and a `preview.png`).

See [docs/agents-instructions.md](docs/agents-instructions.md) for repo conventions, folder
layout, and the build/validation workflow. Build a part with `make <name>` (needs FreeCAD —
run `make install-freecad` first).

## Parts

GitHub markdown can't embed an interactive glTF/GLB viewer inline, so each row shows a static
render; click the STL/GLB links in a part's own README to open GitHub's real 3D viewer.

<table>
<tr>
  <th>Preview</th>
  <th>Part</th>
  <th>Build</th>
  <th>Description</th>
</tr>
<tr>
  <td><a href="designs/parametric-bird/"><img src="designs/parametric-bird/outputs/preview.png" width="160" alt="Parametric Bird preview" /></a></td>
  <td><a href="designs/parametric-bird/"><b>Parametric Bird</b></a><br /><code>parametric-bird</code></td>
  <td><code>make parametric-bird</code></td>
  <td>Flat-plaque spread-wing bird — two grid-pattern wings that slot into one saddle connector riding on a flat-backed "arrow" body. Scaled so all four pieces fit one 350&nbsp;mm Voron plate.</td>
</tr>
</table>

Add a row here (preview.png, folder name, `make <name>` command, one-line description) whenever
a new design is added — see [docs/agents-instructions.md](docs/agents-instructions.md).
