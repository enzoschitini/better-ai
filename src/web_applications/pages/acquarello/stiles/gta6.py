TEXT_TO_IMAGE_INSTRUCTIONS = """
Create an image in the signature "Grand Theft Auto VI" key-art / loading-screen illustration style, using the user_input as the main theme and context.
The result must look like a polished, hand-painted digital illustration of the kind used in modern open-world crime-game promotional art: a stylized semi-realistic vector-comic rendering, NOT a photograph and NOT a 3D render.

LINEWORK AND RENDERING
- Semi-realistic, graphic-novel style figures with realistic anatomy and proportions, confident faces, and intense, serious or defiant expressions.
- Thin, crisp dark contour lines around figures, clothing and props, with slightly thicker, tapered lines on the shadow side.
- Flat, sharp-edged vector-like color blocks for skin, hair, fabric and metal, with hard-edged cel-style shadow shapes (angular, faceted shadows on faces, arms and clothes) instead of smooth airbrushed gradients.
- Subtle painterly detail only where it adds realism: hair strands, fabric folds, tattoos, jewelry, sweat sheen and skin texture, always rendered in clean graphic shapes.
- Strong, bright rim light along edges of skin, shoulders and hair, as if lit by a low golden sun from behind or the side, with a soft warm glow on the lit side of the subject.

COLOR PALETTE AND LIGHTING
- A saturated neon-pastel "Miami sunset" palette: hot magenta pink, violet, lavender, electric purple and indigo skies fading into peach, coral and warm orange near the horizon.
- Alternative bright-day variant when the theme calls for daytime: pale cyan and turquoise sky, aqua water, soft pastel yellow and pink buildings, still with the same flat graphic look.
- Warm orange and pink light on the skin, highlights in cream or pale yellow, shadows pushed toward purple, magenta and deep blue (never neutral gray or black).
- Skies are smooth gradients with faint horizontal banding and soft streaks of contrail or cloud; the overall image has a hazy, dreamy, sun-drenched atmosphere.

BACKGROUND AND ENVIRONMENT
- Sub-tropical Florida-inspired setting: tall palm trees rendered as large flat purple-violet silhouettes framing the sides of the image, a coastal skyline of pastel art-deco and modern high-rise buildings in desaturated lavender and peach, calm bay water with simplified mirror-like reflections, bridges, beaches, neon signs, gas stations, motels, convertibles and classic muscle cars where fitting.
- Background elements are simplified, flatter and lower in contrast than the foreground, tinted heavily in the sky colors to create atmospheric depth, with a few small details such as seagulls, flamingos, a helicopter or a plane.
- Text on signs and clothing must be minimal and stylized, only if it fits naturally.

COMPOSITION
- Poster-like, cinematic key-art composition: characters in the foreground in a confident, cool pose (leaning on a car, standing close together, holding props, covering the face with a bandana, walking toward the viewer), eyes engaging the camera, torso or three-quarter framing, often with a slightly low camera angle.
- Strong depth separation: sharply lit foreground subjects, simplified silhouettes and tinted shapes behind them, with the sky and sunset as the emotional backdrop.
- Everyday modern streetwear and beachwear (tank tops, crop tops, cut-off shorts, cargo pants, gold chains, hoop earrings, sneakers, bandanas) with a gritty yet glamorous, sun-soaked, rebellious mood.
- Do not add any game logo, watermark, publisher logo or caption unless the user asks for one.
"""

IMAGE_TO_IMAGE_INSTRUCTIONS = """
Transform the provided image into an illustration in the signature "Grand Theft Auto VI" key-art / loading-screen style.

Preserve the original composition, pose, number of subjects, facial identity, hairstyle, clothing and main objects so that the people and things remain clearly recognizable, but fully repaint them as a polished hand-painted digital illustration, NOT a photograph and NOT a 3D render.

Apply:
- Semi-realistic graphic-novel figures with realistic proportions and intense, confident expressions, keeping the likeness of every person in the photo
- Thin, crisp dark contour lines around figures, clothing and props, slightly thicker on the shadow side
- Flat, sharp-edged vector-like color blocks with hard, angular cel-style shadow shapes on faces, arms and clothes instead of smooth gradients or photographic texture
- Bright rim light on edges of skin, shoulders and hair from a low golden sun, with a warm glow on the lit side
- Skin lit in warm orange and pink, highlights in cream or pale yellow, shadows pushed toward purple, magenta and deep blue
- A saturated neon-pastel "Miami sunset" palette: hot pink, violet, lavender and indigo sky blending into peach, coral and orange at the horizon (or, for daytime scenes, pale cyan sky, turquoise water and pastel buildings)
- A smooth gradient sky with faint horizontal banding, soft contrails or clouds, and a hazy, dreamy, sun-drenched atmosphere

Rework the background by:
- Converting the original setting into a simplified, flatter, lower-contrast backdrop tinted in the sky colors for atmospheric depth
- Framing the scene with large flat violet palm-tree silhouettes, a pastel coastal skyline of art-deco and modern buildings, calm reflective water, and fitting touches such as seagulls, neon signs, gas stations or classic cars, without hiding the main subjects
- Keeping the original place recognizable (indoor scenes should keep their layout, with the same warm sunset color grading and flat graphic shading)

Enhance the key-art feel by:
- Giving the subjects a cool, confident, poster-like presence with the camera engaging them heroically
- Rendering clothing, jewelry, tattoos, hair strands and fabric folds in clean graphic shapes with small realistic details
- Keeping a gritty yet glamorous, sun-soaked, rebellious mood

Avoid:
- Photorealistic skin, camera noise, lens blur or photographic textures
- Smooth airbrushed gradients on skin, 3D/CGI plastic look, or flat childlike cartoon proportions
- Neutral gray or black shadows, dull or desaturated colors, or cold overcast lighting
- Changing the identity, pose or number of people from the original photo
- Adding game logos, watermarks, captions or any text that was not in the original image

The final result should look like official GTA VI promotional artwork: semi-realistic, graphic, neon-pastel sunset colors, crisp outlines, flat angular shading, rim-lit subjects and silhouetted palm trees.
"""
