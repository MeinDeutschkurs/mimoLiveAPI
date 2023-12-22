# mimoLiveAPI v1.4

**Version 1.4 - First Public Release**

This version enables matrix-switching of pipWindow-Layers and audio-only Layers in mimoLive.

![Program Output Demo](https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/a0cb90c3-3017-4ead-b6a6-77be8637ecf9)

## How to Set Up
1. **Clone or Download**: Get the repository onto your local machine.
2. **Prepare**: Open Terminal, navigate (`cd`) to the `script` folder within the downloaded directory.
3. **Initialize**: Execute `sh start.sh` by typing it into Terminal and pressing enter.
4. **Launch mimoLive**: Open mimoLive and load the `show.tvshow` document from the `demo-show` folder.
5. **Access Web Control**: Utilize the Web Control feature in mimoLive.

![Web Control Demo](https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/f19823ae-991e-48d1-84cf-d94e8c529241)

## Important Notes
- **Demo Document**: The included demo document is an excellent starting point. It combines pipWindow, audioOnly, and Automation-Layers into a single element in the matrix.
- **Customization**: You can add as many pipWindow and audio-only layers as your Mac can support. Corresponding buttons need to be added to the Web Control interface.
- **Layer Management**: If you remove layers from the demo setup, ensure to also remove them from Web Control to maintain consistency.

## Naming Conventions
- **Matrix Name**: Use 'ANYNAME' to represent the name of your matrix. This name should be consistent across all layers.

## How to Create Elements
- **Matrix**: Name it as "matrix_ANYNAME". This will be used in an automation layer with variants like ON, OFF.
- **Video Element**: "video_ANYNAME_NUMBER" represents a pipWindow-Layer at a specific position.
- **Audio Element**: "audio_ANYNAME_NUMBER" corresponds to the audio layer for a given position.
- **Automation Element**: "auto_ANYNAME_NUMBER" links to the automation layer for a particular position, with variants ON, VIDEO, AUDIO, OFF.

## Special Features and Switches
- **Exclusive Control**: "exclusive_ANYNAME" controls fullscreen through an Automation Layer (Variants: 1, 2, 3, etc.).
- **Offset Control**: "offset_ANYNAME" adjusts positions through an Automation Layer. Variants include TOP, LEFT, BOTTOM, RIGHT, and can be set to values like 0,0,0,0 or 0.5, 0.5, 0, 0.
- **Mode Control**: "mode_ANYNAME" switches between modes (MOVE, CUT) in an Automation layer.

## Configuration File (config.ini)
Configure default values and set a web control password for additional security in the `config.ini` file.
