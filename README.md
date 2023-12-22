# mimoLiveAPI v1.5

**Version 1.5** - Added qucker way to submit data to the API. It should be possible to submit changes for up to 6 pipWindow Layers within one frame.

**Version 1.4 - First Public Release**

This version introduces matrix-switching capabilities for pipWindow-Layers and audio-only Layers within mimoLive.

![Program Output Demo](https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/a0cb90c3-3017-4ead-b6a6-77be8637ecf9)

## Setup Instructions
1. **Clone or Download**: Retrieve the repository onto your local machine.
2. **Prepare Environment**: Open Terminal, navigate (`cd`) to the `script` folder within the downloaded repository.
3. **Initialization**: Type `sh start.sh` in Terminal and press Enter to run the script.
4. **Launch mimoLive**: Open the mimoLive application and load the extracted `show.tvshow` document from the `demo-show` folder. BTW: Copy it to any other folder if you want to do a project based on it.
5. **Web Control Access**: Engage with the Web Control feature in mimoLive.

![Web Control Demo](https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/f19823ae-991e-48d1-84cf-d94e8c529241)

## Important Notes
- **Demo Document**: A comprehensive starting point is provided by the demo document. It integrates pipWindow, audioOnly, and Automation-Layers into a cohesive matrix element.
- **Customization**: Add as many pipWindow and audio-only layers as your Mac can handle. It's necessary to add corresponding control buttons in the Web Control interface.
- **Layer Management**: Consistency is key. If you remove any layers from the demo, ensure to remove the corresponding elements from Web Control as well.

## Naming Conventions
- **Matrix Naming**: Use 'ANYNAME' as a placeholder for your matrix name. This needs to be consistent across all layers.

## Creating Matrix Elements
- **Matrix Layer**: Denote as "matrix_ANYNAME". Utilized in an automation layer with options such as ON, OFF.
- **Video Element**: "video_ANYNAME_NUMBER" signifies a pipWindow-Layer at a designated position.
- **Audio Element**: "audio_ANYNAME_NUMBER" is the respective audio layer for that position.
- **Automation Element**: "auto_ANYNAME_NUMBER" refers to the automation layer for a specific position, with options like ON, VIDEO, AUDIO, OFF.

## Special Features and Switches
- **Exclusive Control**: "exclusive_ANYNAME" manages fullscreen modes in an Automation Layer (Variants: 1, 2, 3, etc.).
- **Offset Control**: "offset_ANYNAME" modifies positions using an Automation Layer, with options such as TOP, LEFT, BOTTOM, RIGHT (values can be 0,0,0,0 or 0.5, 0.5, 0, 0).
- **Mode Control**: "mode_ANYNAME" allows switching between modes like MOVE and CUT in an Automation layer.

## This demonstrates the convention. The matrix is called "POS"
<img width="313" alt="two-positions" src="https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/dfa6a504-bb88-494f-bae1-dc2ddd938be8">

## Add at every Automation-Layer this code:
<img width="323" alt="Bildschirmfoto 2023-12-22 um 05 48 07" src="https://github.com/MeinDeutschkurs/mimoLiveAPI/assets/129950466/220c5952-7d76-4b11-aaf1-f3f359fe1c32">

If you want to switch immediately, add `httpRequest(http://localhost:8888/mimoLiveAPI)` to the Automation-Layer. In some cases, you may just want to pre-configure it. If so, you don't have to add it.

## Configuration File (config.ini)
- In `config.ini`, set default values and a web control password for enhanced security.

## Future Enhancements for Matrix Switcher
- **Multiple Matrix Arrangement**: Automate the simultaneous arrangement of multiple matrix switchers.
- **Additional Types**: Implement two new types of transition based on a square-root algorithm that considers only visible elements.
- **Type Change via Automation**: Enable changing types through an automation layer.
- **Prominent Mode**: Similar to the exclusive mode, this would allow one image to be significantly enlarged, with other images arranged around it.
- **server.py**: You should be able to configure the port in `config.ini`.
- **special functions**: multiple individual setLive/setOff and setValues of all mimoLive-Values should also be possible by typing a micro-script.
- **switcher background**: Automate the simultaneous arrangement of a background element.

## DONE since 1.4:
- **Faster HTTP-API Interaction**: Enhance the speed of submitting changes to the mimoLive HTTP-API.
