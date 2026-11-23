# Volumetric audio

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Audio</span>
  <span>Last updated: <time datetime="2026-11-22">2026-11-22</time></span>
</div>

<p class="doc-lede">An optional mixer that simulates how sound travels through the world: it arrives late, is Doppler shifted, is muffled by what lies in its way, bends round corners, echoes and rings with the room, and clears up as you get close.</p>

`VolumetricMixer` (`src/caffeine/audio/volumetric/`) is separate from `AudioService`: a game that wants plain 2D or 3D sound keeps
using that. The mixer needs no sound card. It renders blocks of stereo samples, so the same code feeds a device in play, a WAV file
in a test and a video in the demos.

## 1. What a voice goes through

| Stage | What it does |
|---|---|
| Propagation | The clip is read at `t - distance / c`, so a shot 150 m away is heard 0.44 s late. A moving source changes that delay continuously, which **is** the Doppler shift: exact, with no pitch trick (`dopplerScale` 0 freezes it) |
| Distance | Inverse law gain (half for every doubling) and air absorption: the cutoff falls with distance, so near sound is clear and far sound is dull |
| Occlusion | The segment source to listener is traced through the `AcousticWorld`. What a wall lets through is quiet and dull: lows pass walls far better than highs, and thicker walls keep less |
| Diffraction | If the sound can bend round the obstacle (the end of a wall, a doorway) that path is mixed in too, quieter and duller with the extra distance, and the voice is heard coming from the opening |
| The room | 31 rays round the listener (up to 300 m) give its size, openness, sky exposure and reflectivity. A feedback delay network (8 lines) fits the reverb tail and level to them, and far hard surfaces send back distinct echoes at `2 d / c`. A source behind a wall is in another room: that room is read too, and its own reverb leaks through the wall |
| Clarity | The reverb falls slower than the direct sound, so distant sound is washier and near sound is dry and clear. What reaches the room from behind a wall is only what the wall lets through |
| Ears | A spherical head (8.75 cm): Woodworth's time difference (up to 0.66 ms) and Brown & Duda's head shadow, a filter that boosts the highs in the ear facing the sound and cuts them deeply in the far ear (the lows reach both), and a duller rear. No HRTF data files |
| Layers | **World** is spatial; **Ambient** (rain, wind) covers the scene and follows the listener's exposure, muffled and quieter under a roof; **Music** and **Ui** are plain. Each layer has its own volume |

## 2. Using it

```cpp
AcousticBoxWorld world;                       // or your own AcousticWorld over the game's colliders
world.add({-500, -1, -500}, {500, 0, 500}, AcousticMaterial::ground(), false);
world.addRoom({-8, 0, -6}, {8, 3, 6}, AcousticMaterial::brick(), 0.3f, /*door*/ 2.0f);

VolumetricMixer mixer(48000);
mixer.setWorld(&world);
mixer.setListener(camera.position, camera.forward);
VoiceId siren = mixer.play({.clip = clip, .position = start, .loop = true});
// each audio block (about 5 ms): move things, then mix
mixer.setPosition(siren, vehicle.position);
mixer.render(stereo, 256);
```

Move voices and the listener between blocks, with small blocks: the Doppler shift is the change of delay from one block to the
next. `debug(voice)` reports what the mixer decided (distance, delay, pitch ratio, gain, cutoff, blocked, diffracted, where the
sound seems to come from), and `room()` what the rays read. `settings()` switches each stage off (`occlusion`, `diffraction`,
`reverb`, `airAbsorption`, `propagationDelay`, `ears`).

## 3. The world sound travels through

`AcousticWorld` answers two questions: the transmission between two points, and how far a ray goes before it hits something.
`AcousticBoxWorld` is a set of boxes, axis-aligned or **oriented** (centre, half extents, three axes: a cube entity scaled and turned into a wall), with materials (`concrete`, `brick`, `wood`, `glass`, `foliage`, `curtain`, `ground`), and `addRoom` for four walls, a ceiling and an optional doorway. A material says how much of the lows and the highs pass 20 cm of it and
how much energy it reflects. A game with other shapes implements the interface over its own colliders.

## 4. In the editor and in a scene

The scene decides what is heard, with three reflected components (the Inspector and scripts edit them like any other):

| Component | What it does |
|---|---|
| `Volumetric Audio` | The settings: on, the layer and master volumes, the Doppler scale, the speed of sound, and a switch for each stage of section 1. Nothing is mixed without an enabled one |
| `Audio Emitter` | A sound: `Clip Path` (a WAV, looked for as written, then under the asset root), `Volume`, `Loop`, `Play On Spawn`, `Max Distance`, and the new `Layer` (0 World, 1 Ambient, 2 Music, 3 Ui), `Ref Distance` and `Doppler` |
| `Acoustic Obstacle` | The entity's transform applied to a unit cube is a box sound cannot cross: a preset material (`Material`) or a custom one (`Custom`, `Transmission Low/High`, `Reflectivity`) |

Weather is played by the same mixer when a scene has both: the rain and wind beds are Ambient voices (muffled and quieter under a roof) and every thunder clap is a World voice up in the sky at its bearing, so a wall muffles it, a hall rings with it and the ears place it. `Weather` > `Audio Enabled` and `Audio Volume` switch it on, as before; the clap is not delayed twice (`propagate` off on that voice, because the strike's own clock already waited out the travel time).

`SceneAudio` reads them once a frame, builds a new box world only when the obstacles changed, and gives voices and the listener a
velocity from the time between frames, so the mixer carries them on smoothly and the Doppler shift stays continuous at any frame rate.
The viewport camera is the listener. `VolumetricAudio` owns the mixer, a lock and the optional sound device (the system default or one of `outputDevices()`, listed in a stable order), which pulls blocks on the
audio thread; with no device the session mixes silently ("monitors"), so the numbers keep moving and tests can pull samples
with `caffeine_session_volumetric_render`. C ABI v20 adds `caffeine_session_volumetric_state`, `caffeine_session_volumetric_voice`,
`caffeine_session_set_audio_output`, `caffeine_session_set_audio_output_device`, `caffeine_audio_output_device_count`/`_name` and `caffeine_session_volumetric_render`.

Doppio's **Audio** tab (View menu, with Inspector, Profiler, Photon and Environment) adds the component, edits it with undo, switches the
speakers on and off, picks the sound device, adds a source or a 6 x 3 x 0.3 m wall, and shows live what the mixer decides: the room round the listener and one
line per sound (distance, level, low-pass, pitch shift, behind a wall or round a corner). Agents use `show_audio`, `audio`,
`audio_add`, `audio_set`, `audio_output`, `audio_device`, `audio_add_source` and `audio_add_wall`.

`caffeine-runtime` hosts it too: each frame it syncs the scene from the active Camera 3D, feeds the weather from its renderer, and opens the sound device the first frame the scene has a `Volumetric Audio` component.

## 5. Hear it

`scripts/render-audio-demo.py` renders four scenarios with sounds from `references/moodist` and writes videos to
`build/audio-demo/videos/` (a top view of the scene with what the mixer is doing, and the audio):

| Video | What to listen for |
|---|---|
| `doppler.mp4` | An ambulance at 108 km/h with Doppler on and off, then an aeroplane at 150 m/s |
| `shots.mp4` | A shot 150 m away in a field with a far cliff (late, dull, echoed), the same shot in a concrete hall, and from outside its wall |
| `occlusion.mp4` | A radio behind a wall, then round its end; a fan inside a house, then at its door |
| `layers.mp4` | Rain and wind outside and in a house, a fireplace you walk up to, thunder through the walls, and the ambient layer at 30% |

It needs `cmake --build build --target caffeine-audio-demo`, ffmpeg, Pillow and numpy.

## 6. Tests and limits

* `tests/test_scene_audio.cpp`: emitters become voices, an obstacle blocks them, moving and removing, no component means silence, and
  the weather through the mixer (beds follow it, a roof muffles them, a clap comes from its side of the sky).
  `tests/test_volumetric_audio.cpp`: level halves with distance, the delay is `d / c`, the Doppler shift matches `1 / (1 -+ v / c)`
  within 2%, near sound is brighter, a wall takes at least 15 dB and the highs more than the lows, a thicker wall takes more, a short
  wall is bent round and heard from its corner, the rays read open and shut rooms and far echoes, a shot rings in a hall and echoes off a
  cliff, the ears, the ambient layer indoors and layer volumes, and the limiter.
* Geometry is boxes (oriented ones from a scene); triangle meshes are not traced. The acoustics are a model, not a wave solver: occlusion
  is one traced segment plus one best detour, the listener's room and the room of a source behind a wall are each fitted by their own rays
  and shared reverb, and echoes come from the listener's rays.
* The mixer is mono per voice, and the ears are a model of a spherical head, not measured HRTF data: left and right are good, front and back
  and up and down are only suggested (a dull rear). Nothing else changes: a scene without the component sounds as before.
