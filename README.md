V1.4: First public version: It makes matrix-switching of pipWindow-Layers + audio-only Layers possible.

<img width="731" alt="pgm-out-demo" src="https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/a0cb90c3-3017-4ead-b6a6-77be8637ecf9">

How to?
1. Clone or download the repository.
2. Open Terminal and 'cd' to the folder script.
3. write sh start.sh and press enter.
4. Open mimoLive and the show.tvshow-document from demo-show folder.
5. Open Web Control

<img width="992" alt="webcontrol-deom" src="https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/f19823ae-991e-48d1-84cf-d94e8c529241">

Notice:
The Demo-Document is a great starting point:
- pipWindow + audioOnly + Automation-Layer = One element at the matrix.
- You can add as many pipWindow and audio-only- Layers as your Mac can handle. You have to add buttons at the Web Control.
- If you remove Layers from the demo, you might have to remove these also from WebControl.

Naming-Convention:
ANYNAME represents the name of your matrix. This has to match through all the layers.

Create Matrix:
"matrix_ANYNAME" names the matrix through an automation layer (variants ON, OFF).

Create an Element:
"video_ANYNAME_NUMBER" is the pipWindow-Layer at Position X (one variant)
"audio_ANYNAME_NUMBER" is the matching audio-Layer for Position X (one variant)
"auto_ANYNAME_NUMBER" is the corresponding automation-Layer for Position X (Variants: ON, VIDEO, AUDIO, OFF)

Special Features and Switches:
"exclusive_ANYNAME" is the Automation Layer which controlls Fullscreen (Variants: 1,2,3...)
"offset_ANYNAME" is an Automation-Layer. The variant-Names controll the offset. TOP, LEFT, BOTTOM, RIGHT (0,0,0,0 or 0.5, 0,5, 0, 0)
"mode_ANYNAME" is an Automation-layer. It controlls modes. Currently it supports MOVE or CUT as variants.

config.ini
At config ini, you can set several default values, as well as the web control password, if you need extra security.
