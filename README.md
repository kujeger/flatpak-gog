# Flatpak generator for GOG installers
The hope is to have this eventually work with almost any GOG game, but that is probably a ways off.

## Prerequisites
You will need flatpak 0.9.7 or later, and python3. Both should be available in your repository if not already installed.
64-bit OS only, but building and playing 32-bit games works.

This all uses the [Freedesktop runtime](http://flatpak.org/runtimes.html).
If you haven't already got it, add the repo like this:

`flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`

then install the runtime plus SDK:

`flatpak --user install flathub org.freedesktop.Platform/x86_64/24.08`

`flatpak --user install flathub org.freedesktop.Sdk/x86_64/24.08`

For x86 games additionally install the required compatibility packages:

`flatpak --user install flathub org.freedesktop.Platform.Compat.i386/x86_64/24.08`

`flatpak --user install flathub org.freedesktop.Platform.GL32.default/x86_64/24.08`

`flatpak --user install flathub org.freedesktop.Sdk.Compat.i386/x86_64/24.08`

`flatpak --user install flathub org.freedesktop.Sdk.Extension.toolchain-i386/x86_64/24.08`

## Usage
First, clone the repo and then pull the submodules:
```
git clone https://github.com/kujeger/flatpak-gog.git
cd flatpak-gog
git submodule update --init --recursive
```

To prepare a game, you can use the provided `json-maker` script, e.g.

`./json-maker ~/Downloads/baldur_s_gate_ii_enhanced_edition_2_6_6_0_47292.sh`

which will create a new json in the current dir based on the com.gog.Template.json file, with a name like gen_com.gog.BaldursGate2EnhancedEdition.json .

You can then build and install it directly thus:

`flatpak-builder --user --install build gen_com.gog.BaldursGateIIEnhancedEdition.json --force-clean --arch x86_64`

(see also the suggested command in the output of `json-maker`)

After installation you can start it like this, or use the desktop/menu icon that should have also been created.

`flatpak run com.gog.BaldursGateIIEnhancedEdition`

## Disk-space use
flatpak-builder leaves some caching in .flatpak-builder, and the prepared Build/GAMENAME directory. These can be safely removed once you have the game running.

## Troubleshooting
Sometimes the start.sh script provided from GOG does not work right in our flatpak.
You can "override" this by placing a custom start-script in overrides/starter-GAMENAME .

## Compatibility
This has not been tested with many GOG games yet, and it is extremely likely that a lot of further work will be needed to cover more games.

See the [compatibility list](https://github.com/kujeger/flatpak-gog/wiki/Compatibility) for details.

## Further work
Things that would be nice to implement:

* Converting GOG's .desktop files for cases where there are separate "settings" desktop files.
