# Financial adapter release: source and byte review

Reviewed 2026-10-01 before release publication. This
[internal AI-assisted review](README.md) inspected the builder/verifier,
artificial tests, actual ZIP bytes, five-checkpoint freeze, model card and
license. It loaded no model and performed no training or financial evaluation.

## Artifact identity

The reviewed archive is **46,046,805 bytes**, SHA256
`310326c0df16e50a4d5f709d42ecea9c5d1a74e9c80b06b24c21c866b3b64636`.
It contains exactly thirteen regular-file entries: the five declared adapter
directories each contain an `adapter/` subdirectory holding `adapter_config.json` and
`adapter_model.safetensors`, followed by `LICENSE`, `MODEL_CARD.md` and `NOTICE`.

Independently checked every member size and hash, all ten adapter/config entries
against the original five-checkpoint freeze, the freeze-file byte hash and the
builder-source hash against the release manifest. The bundled license and card
equal their current source-file bytes, and the notice equals the builder's
declared notice. No checkpoint was rewritten to make it distributable.

Independently extracted the final verified archive into a new local review
directory and called the existing `checkpoint_manifest` on all five
`<checkpoint>/adapter/` paths. Every complete result equals its original frozen
dictionary, including the checkpoint name, filenames, sizes, hashes and combined
identity. This checks loader-facing provenance as well as tensor-byte identity.

Each safetensors header contains exactly 224 LoRA tensors totaling 2,293,760
FP32 parameters, with no base-model tensor names. All configurations retain
rank eight, alpha sixteen, zero dropout and q/k/v/o projection targets.
Textual members and tensor metadata contain no absolute private paths. The
literal inventory excludes base weights, tokenizers, optimizer states, raw
market data and unrelated local logs. The original relative base-model path
is preserved; the card instructs readers to supply the pinned base explicitly.

## Verification and extraction behavior

The builder reads only the ten literal checkpoint paths and three declared
documentation/license inputs. It checks frozen adapter identity before writing
the archive. ZIP timestamps and permissions are fixed for deterministic bytes.
Existing different archives or manifests are not overwritten.

The fetch command accepts only the declared GitHub release URL and caps the
download at 60 MB plus one rejection byte. Verification checks the archive hash,
size, exact member inventory, duplicate entries, per-member size/hash and
agreement with the checkpoint freeze. Both compressed and declared uncompressed
totals are bounded. Every member is verified before extraction begins.
Extraction creates a new destination and writes only allowlisted literal paths;
it never calls `extractall` or honors ZIP links/permissions as executable logic.
An existing destination is refused.

Nine tests passed independently, covering deterministic packaging,
excluded extra files, corrupt bytes, re-signed but freeze-inconsistent adapter
content, unexpected/traversal paths, preservation of existing destinations and
changed local checkpoint rejection and extraction-layout checkpoint naming.
These are consistency checks against the
trusted repository manifest and freeze; hashes alone do not authenticate an
untrusted replacement of both documents.

## License, card and resolved finding

The official [pinned Qwen license](https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/LICENSE)
identifies Apache-2.0 and the Alibaba Cloud copyright notice. The archive
includes the unchanged local copy. The notice and card identify the newly
trained adapter/config contribution under Apache-2.0, preserve the base
attribution, state that base weights are not included, and keep repository
source code under its separate MIT license. The card's parent relationships,
96/16/15/16/16 update counts and bounded result claims match the recorded studies.

Review found two relative results links that would break in the standalone ZIP.
The author replaced them with public repository URLs. A subsequent integration
check identified that flat extraction paths changed the checkpoint name inferred
by `checkpoint_manifest`. The author restored the original
`<checkpoint>/adapter/` layout and rebuilt the archive/manifest. The final byte
identity above includes both corrections; the ten adapter/config identities
remained unchanged. No blocking discrepancy remains
in the reviewed local release. Remote upload/download integrity and actual
execution on another machine are separate checks; this review does not claim
they have already occurred or that stochastic generations are hardware-invariant.
