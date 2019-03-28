# Flatpak generator for GOG installers
The hope is to have this eventually work with almost any GOG game, but that is probably a ways off.

## Prerequisites
You will need flatpak 0.9.7 or later, and python3. Both should be available in your repository if not already installed.

This all uses the [Freedesktop runtime](http://flatpak.org/runtimes.html).
If you haven't already got it, add the repo like this:

`flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`

then install the runtime plus SDK:

`flatpak --user install flathub org.freedesktop.Platform/i386/18.08`

`flatpak --user install flathub org.freedesktop.Sdk/i386/18.08`

`flatpak --user install flathub org.freedesktop.Platform/x86_64/18.08`

`flatpak --user install flathub org.freedesktop.Sdk/x86_64/18.08`

## Usage
When building flatpaks, you can either install them directly or export them to a repository and then install them from that repository. If you're doing everything on a single machine, it probably makes the most sense to install directly. However, if you're going to install on several machines exporting to a (shared) repo makes sense. Before you build your first game, you will need to build and install the Base image, for both 32 and 64-bit.

In order to build and install directly, run the following commands:

`flatpak-builder --user --install build com.gog.Base.json --force-clean --arch=i386`

`flatpak-builder --user --install build com.gog.Base.json --force-clean --arch=x86_64`


In order to build and export to a repo, run the following commands:

`flatpak-builder build com.gog.Base.json --force-clean --arch=i386 --repo ~/FlatPak/gog-repo`

`flatpak-builder build com.gog.Base.json --force-clean --arch=x86_64 --repo ~/FlatPak/gog-repo`

`flatpak --user remote-add --no-gpg-verify --if-not-exists gog-repo ~/FlatPak/gog-repo`

`flatpak --user install gog-repo com.gog.Base/i386`

`flatpak --user install gog-repo com.gog.Base/x86_64`


To prepare a game, you can use the provided "json-maker.py" script, e.g.

`./json-maker.py ~/Downloads/gog_baldur_s_gate_2_enhanced_edition_2.6.0.11.sh`

which will create a new json in the current dir based on the com.gog.Template.json file, with a name like gen_com.gog.BaldursGate2EnhancedEdition.json .

You can then build and install it directly thus:

`flatpak-builder --user --install build gen_com.gog.BaldursGate2EnhancedEdition.json --force-clean --arch=i386`

Or build and export it to a repo before installing it:

`flatpak-builder build gen_com.gog.BaldursGate2EnhancedEdition.json --force-clean --arch=i386 --repo ~/FlatPak/gog-repo`

`flatpak --user install gog-repo com.gog.BaldursGate2EnhancedEdition`

(see also the suggested command in the output of json-maker.py)

After installation you can start it like this, or use the desktop/menu icon that should have also been created.

`flatpak run com.gog.BaldursGate2EnhancedEdition`

## Disk-space use
flatpak-builder leaves some caching in .flatpak-builder, and the prepared Build/GAMENAME directory. These can be safely removed once you have the game running.

The flatpak repo contains the games you have packaged. Don't delete this if you want to be able to reinstall the game.

If you are planning to build a lot of flatpaks, disk use will quickly balloon, as each game takes space in both the (local) flatpak repo, and when installed.

## Troubleshooting
Sometimes the start.sh script provided from GOG does not work right in our flatpak.
You can "override" this by placing a custom start-script in overrides/starter-GAMENAME .

## Compatibility
This has not been tested with many GOG games yet, and it is extremely likely that a lot of further work will be needed to cover more games.

See the [compatibility list](https://github.com/kujeger/flatpak-gog/wiki/Compatibility) for details.

## Further work
Things that would be nice to implement:

* Converting GOG's .desktop files for cases where there are separate "settings" desktop files.
* It might make sense to create a sort of GOG runtime instead of using the current Base-image approach.
* Support more GOG games. Most of this work is likely to be:
  * Additional libraries to install, possibly conflicting with other games.
* Use installers as extra-data instead of embedding the complete game? extra-data currently only supports http(s), not local files.
