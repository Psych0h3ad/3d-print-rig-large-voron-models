# Large VORON references for 3D Print Rig

[Open 3D Print Rig](https://psych0h3ad.github.io/3d-print-rig/viewer/).

VORON V2.4 1000 × 1000 × 969 mm and Trident 1000 × 1000 × 994 mm dimensional references, with Stealthburner / Clockwork 2 / Revo Voron. Fasteners, bearings, motors and toolhead hardware retain native dimensions; the frame, guides, bed and Trident lead-screw length are extended.

At this scale, consider frame and mechanism upgrades. Review frame rigidity, linear guides and drives, bed mass, power requirements and cable routing before a real build. This scaled reference has not been tested as a printer design.

CAD assets retain their upstream GPL-3.0/component terms; the application utility license does not relicense CAD. Exact original repository versions and changes are in [SOURCES.json](site/SOURCES.json); original licenses are in [licenses](site/licenses). The [native source release](https://github.com/Psych0h3ad/3d-print-rig-large-voron-models/releases/tag/voron1000-v1) contains editable BREP solids.

Flexible motion uses route previews. Physical belt tension, flexible material behavior and full continuous native clearance are not certified.

The Trident bed-chain upper end retains original CAD contacts between the link, cap and printed mount. Their intended mechanical fit remains unqualified; the reference is not certified for physical assembly.

The repository also supplies elcrni's Trident Internal Spool Holder v32 for standard Trident 300/350. Holder and guides are included; a spool body and filament feed path are not. Its original revision and component licenses are in [SOURCES.json](site/SOURCES.json), and editable placed solids are in the [internal spool source release](https://github.com/Psych0h3ad/3d-print-rig-large-voron-models/releases/tag/internal-spool-v1).

Build: `python scripts/build_site.py --output _site`.

FOX's A/B Stepper Fan V2 is available as a mounted geometry preview for standard Trident R2 250/300/350 with Stealthburner, CW2 and Revo Voron. The A-side holder has a small frame-corner relief. Original VORON 4010 fans and fasteners are reused without resizing; this hardware selection is separate from FOX's original printed design. The [derivation source](https://github.com/Psych0h3ad/3d-print-rig-large-voron-models/releases/download/requested-mods-v1/Trident_AB_Fan_V2_Derivation_Source_v2_96.zip) includes the unchanged source geometry, placement recipe, modification and individual license notices. The stock outside-spool PTFE remains a reference path; its moving attachment is not qualified.

Additional original bed-support, drive, enclosure and wiper parts are available in the viewer's Component CAD library. Exact author versions, file hashes and separate license records are in [REQUESTED_MOD_SOURCES.json](site/REQUESTED_MOD_SOURCES.json); the [source release](https://github.com/Psych0h3ad/3d-print-rig-large-voron-models/releases/tag/requested-mods-v1) retains the original uploads. A source-part preview does not imply a registered machine installation. FOX's printed fan, spacer and decoupler uploads retain the author's CC BY-NC record; the version is not specified by that record. VORON hardware retains its original GPL terms.
