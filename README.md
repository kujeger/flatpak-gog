# Flatpak generator for GOG installers
The hope is to have this eventually work with almost any GOG game, but that is probably a ways off.

These recipes require flatpak 0.9.1 or later.

Presently there are hacks, like decompressing and then re-compressing the installer provided by GOG as it is not "really" a zip, which throws flatpak-builder for a loop.

Currently all the scripts create i386 builds, as only some GOG games have x86_64 builds.

## Usage
Before you build your first game, you will need to build and install the Base image, for both 32 and 64-bit.
The following will build the Base image, put it into the repo dir "repo", add that repo with the name "gog-repo", and finally install Base:

`flatpak-builder Base com.gog.Base.json --force-clean --arch=i386 --repo repo`

`flatpak-builder Base com.gog.Base.json --force-clean --arch=x86_64 --repo repo`

`flatpak --user remote-add --no-gpg-verify --if-not-exists gog-repo repo`

`flatpak --user install gog-repo com.gog.Base/i386`

`flatpak --user install gog-repo com.gog.Base/x86_64`


To prepare a game, you can use the provided "maker.sh" script, e.g.

`./maker.sh ~/Downloads/gog_baldur_s_gate_2_enhanced_edition_2.6.0.11.sh`

which will create a new json in the current dir based on the com.gog.Template.json file, with a name like gen_com.gog.BaldursGate2EnhancedEdition.json .

You can then build it and export it into a flatpak repo thus:

`flatpak-builder BaldursGate2EnhancedEdition gen_com.gog.BaldursGate2EnhancedEdition.json --force-clean --arch=i386 --repo repo`

MAKE SURE TO USE ARCH i386 HERE IF THE GAME ONLY SUPPORTS 32BIT.

which will build the game flatpak, and put it into the repository "repo" in the current directory.

Install it like this:

`flatpak --user install gog-repo com.gog.BaldursGate2EnhancedEdition`

..and finally start it up like this:

`flatpak run com.gog.BaldursGate2EnhancedEdition`

## Troubleshooting
Sometimes the start.sh script provided from GOG does not work right in our flatpak.
You can "override" this by placing a custom start-script in overrides/starter-GAMENAME .

## Compatibility
This has not been tested with many GOG games yet, and it is extremely likely that a lot of further work will be needed to cover more games.

See the [compatibility list](https://github.com/kujeger/flatpak-gog/wiki/Compatibility) for details.

## Further work
Things that would be nice to implement:

* .desktop files for starting the games. Converting the existing files GOG provides should be a good starting point.
* It might make sense to create a sort of GOG runtime instead of using the current Base-image approach.
* Support more GOG games. Most of this work is likely to be:
  * Additional libraries to install, possibly conflicting with other games.
* It would be nice to pick 32/64bit automatically. This might need to be a manual list the build scripts consult.
* DLC installation
* Use installers as extra-data instead of the current archive hack? extra-data currently only supprots http(s), not local files.
