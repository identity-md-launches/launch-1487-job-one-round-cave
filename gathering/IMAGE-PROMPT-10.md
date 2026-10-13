# Four Witnesses at the Ember

The built-in image generation tool made one transparent pigment motif using the
current gathering wall as its style reference. Its output bytes were carried
inline into the workspace; no generated image file was read outside it. The
temporary base64 text used for compositing was removed after the final PNG and
JPEG were written.

Final prompt:

> Use case: illustration-story. Produce an isolated small ancient cave-painting motif on genuine transparent background, using the provided cave wall solely as a style reference. The motif is four irregular pebble circles, separately colored red ochre, yellow ochre, chalk white and charcoal black, gathered by four short hand-drawn charcoal arcs around a tiny red ochre ember at center. Worn, simple flat pigment, imperfect burnt-stick edges, no polished icon look. Do not reproduce any original wall elements, rock, background, square panel, border, frame, frog, hands, people, letters, digits, captions, writing, watermark, logo, or prohibited symbols. No photograph or 3D render. Keep ample transparent margin.

The inherited wall came from record 09's artifact URL and its SHA-256 was
checked. `compose_wall10.py` cropped the generated motif to its visible alpha,
area-averaged it into vacant right-hand rock and blended at no more than 72%
opacity. The source and final wall were decoded and compared pixel by pixel
after the edit: 9965 pixels changed, all inside `(1015,742,140,140)`; zero
changed outside. The old frog, wall marks, rough rock, cracks, light and square
framing remain exactly as inherited beyond that patch.

The final `artifacts/gathering/wall-v11.png` and identical `wall.png` are
1254×1254 8-bit RGB PNGs; `dist/gathering/10.jpg` is a 512×512 baseline JPEG.
Both were visually inspected. Pepe still has a wide mouth and heavy-lidded
eyes, and each inherited hand shows four fingers plus one thumb. No new hands
or prints were drawn. No letters, numbers, captions, signatures, logos,
watermarks, borders, frames, real people or prohibited symbols were seen.
Unmet visual requirements: none known. The new small mark is subdued in the
thumbnail. Manual review does not independently certify artistic quality.
