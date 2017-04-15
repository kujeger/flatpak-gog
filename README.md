# Flatpak generator for GOG installers
The hope is to have this eventually work with almost any GOG game, but that is probably a ways off.

Presently there are hacks, like decompressing and then re-compressing the installer provided by GOG as it is not "really" a zip, which throws flatpak-builder for a loop.

Currently all the scripts create i386 builds, as only some GOG games have x86_64 builds.

## Usage
Before you build your first game, you will need to build and install the Base image.
The following will build the Base image, put it into the repo dir "repo", add that repo, and finally install Base:
`flatpak-builder Base com.gog.Base.json --force-clean --arch=i386 --repo repo`
`flatpak --user remote-add --no-gpg-verify --if-not-exists gog-repo repo`
`flatpak --user install gog-repo com.gog.Base`

To prepare a game, you can use the provided "maker.sh" script, e.g.
`./maker.sh ~/Downloads/gog_baldur_s_gate_2_enhanced_edition_2.6.0.11.sh`
which will create a new json in the current dir based on the com.gog.Template.json file, with a name like com.gog.BaldursGate2EnhancedEdition.json .

You can then build it and export it into a flatpak repo thus:
`flatpak-builder BaldursGate2EnhancedEdition com.gog.BaldursGate2EnhancedEdition.json --force-clean --arch=i386 --repo repo`
which will build the game flatpak, and put it into the repository "repo" in the current directory.

Install it like this:
`flatpak --user install gog-repo com.gog.BaldursGate2EnhancedEdition`
..and finally start it up like this:
`flatpak run com.gog.BaldursGate2EnhancedEdition`

## Compatibility
This has not been tested with many GOG games yet, and it is extremely likely that a lot of further work will be needed to cover more games.
Currently the following have been tested OK:

* [Baldur's Gate: Enhanced Edition](https://www.gog.com/game/baldurs_gate_enhanced_edition)
* [Baldur's Gate 2: Enhanced Edition](https://www.gog.com/game/baldurs_gate_2_enhanced_edition)
* [Icewind Dale: Enhanced Edition](https://www.gog.com/game/icewind_dale_enhanced_edition)
* [Planescape: Torment: Enhanced Edition](https://www.gog.com/game/planescape_torment_enhanced_edition)

## Further work
Things that would be nice to implement:

* .desktop files for starting the games. Converting the existing files GOG provides should be a good starting point.
* It might make sense to create a sort of GOG runtime instead of using the current Base-image approach.
* Support more GOG games. Most of this work is likely to be:
  * Additional libraries to install, possibly conflicting with other games.
  * Game-specific start scripts. Some of the bundled start-scripts with games try to be clever, and will almost certainly make things "interesting."
