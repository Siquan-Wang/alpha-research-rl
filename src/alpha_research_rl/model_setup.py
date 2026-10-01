"""Download a revision-pinned public model; no paid inference service is used."""

import argparse
from pathlib import Path

from .artifacts import write_json


def download_model(destination: str, model_id: str = "Qwen/Qwen3-0.6B") -> dict:
    from huggingface_hub import HfApi, snapshot_download

    info = HfApi(token=False).model_info(model_id)
    license_name = (info.card_data or {}).get("license")
    if license_name != "apache-2.0":
        raise ValueError("This downloader currently supports only verified Apache-2.0 model cards")
    snapshot_download(
        repo_id=model_id, revision=info.sha, local_dir=destination, token=False,
        allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "LICENSE*", "README.md"],
    )
    manifest = {"model_id": model_id, "revision": info.sha, "model_card_license": license_name,
                "source": f"https://huggingface.co/{model_id}/tree/{info.sha}",
                "weights_published_in_repository": False}
    write_json(Path(destination) / "source-manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", default="models/Qwen3-0.6B")
    arguments = parser.parse_args()
    print(download_model(arguments.destination))
