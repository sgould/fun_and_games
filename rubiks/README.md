# Rubik's Cube Scanner & Solver

Show a scrambled cube to your webcam, check the colours it read, then watch an animated
3D solution you can follow move by move.

## Run

```
python serve.py
```

This serves the folder at http://localhost:8765 and opens your browser. The page must be
served instead of opened as a file, because webcam access and JS modules need a real origin.
Everything runs offline; three.js and the solver are in `vendor/`.

## Use

1. **Scan**, in one of two modes:
   - **Auto** (default): just turn the cube in front of the camera. Whenever a face is held
     flat and still in the grid, it is captured (the grid turns yellow while reading and
     flashes on capture). Faces can come in any order and any way up. Repeat views are
     recognised and make the reading more reliable. Once six different faces are seen, the app
     works out how they fit together by trying every layout and every face rotation until it
     finds a valid cube. Turn the whole cube only; don't twist layers mid-scan.
   - **Guided**: the page walks you through the six faces in a fixed order and you press
     **Space** for each. Coloured bars around the grid show which neighbouring centre should
     be on each side.
   In either mode, if the six faces don't form a possible cube, the app searches every
   arrangement and rotation of the faces for one that does. If none fits as read, it looks for
   one or two pairs of misread stickers, chosen by how well the camera colours fit, and
   outlines the corrected stickers (amber if another fix was nearly as likely). *Find a valid
   layout* reruns the search.
2. **Check**: the unfolded net shows what was read. Pick a colour and click any sticker
   that is wrong. The page checks that the cube is actually solvable and says what looks wrong
   if it isn't. With no camera, use *Fill in by hand*.
3. **Solve**: play, step (← / →), or click any move. Drag to orbit the cube.

## Tips for good scans

- Use even, diffuse light. Avoid glare and coloured lamps.
- Fill most of each grid cell with its sticker.
- Red/orange and white/yellow are the usual mix-ups. Each centre sets the reference colour
  for its face, and stickers are assigned so every colour appears exactly nine times, which
  fixes most of these. Correct the rest in the net.

## Files

- `js/scanner.js`: webcam, grid overlay, per-cell median colour sampling
- `js/autoscan.js`: hands-free mode: steadiness detection, face matching
- `js/layout.js`: search over face positions, rotations and misread-sticker repairs
- `js/colors.js`: Lab colour matching and balanced assignment (Hungarian algorithm)
- `js/validate.js`: solvability checks (piece identity, twist, flip, parity)
- `js/cubemodel.js`: 3D cubie model and face turns, shared by the renderer
- `js/viewer.js`: three.js scene
- `js/main.js`: UI and playback
- `vendor/cubejs`: Kociemba two-phase solver ([cubejs](https://github.com/ldez/cubejs), MIT)

## License

MIT, see [LICENSE](LICENSE). Bundled third-party code keeps its own MIT licence:
three.js (`vendor/LICENSE-three.txt`) and cubejs (`vendor/cubejs/LICENSE`).
