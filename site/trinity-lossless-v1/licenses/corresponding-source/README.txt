Exact lossless storage recipe
License: GPL-3.0-only; see ../Martin-Ivanc/LICENSE for the license text. Separate CAD licenses remain unchanged.
Input: decoded original model SHA256 ff8557d93e9d3803b3e4ba2729d6fb947c4134c2e84098a653069ce337d2fcfb.
The original gzip and editable native source are linked in ../provenance.json.
Install the pinned dependency from requirements.txt. Python 3.13 was used for reproducibility.
Run: python repack.py --source original.glb --output recipe-output --reference path-to-trinity-lossless-v1
The recipe verifies the exact repacked GLB SHA256, then regenerates 11 accessor-only GLBs and gzip files.
Reference validation checks the repacked assembly, reassembly prefix, every gzip file and every decoded chunk against the immutable manifest.
Gzip byte reproducibility also depends on the compression implementation; decoded GLB hashes establish content identity.
Recipe intermediates are for verification. Publication uses only the explicitly whitelisted gzip chunks, manifest, assembly, parts, prefix, proof and license/source records.
No native CAD processing is needed for this storage-only transformation.
