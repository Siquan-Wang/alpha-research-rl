"""Original tiny artificial fixtures exercise format, not redistributed source data."""

import io
import json
import zipfile

import numpy as np
import pytest

from alpha_research_rl.dsl import ExpressionError, evaluate_expression
from alpha_research_rl.evaluation import forward_returns
from alpha_research_rl.french import ASSETS, TABLE_NAME, download_french49, load_french49


def _fixture(rows=None, header=None):
    rows = rows if rows is not None else [
        ("20000103", [1.0] * 49), ("20000104", [2.0] * 49),
        ("20000105", [-1.0] * 49), ("20000106", [3.0] * 49),
    ]
    header = header or ASSETS
    return ("Original artificial parser fixture\nMissing values: -99.99 and -999.\n\n"
            + TABLE_NAME + "\n," + ",".join(header) + "\n"
            + "".join(date + "," + ",".join(str(value) for value in values) + "\n"
                      for date, values in rows)
            + "\nAverage Equal Weighted Returns -- Daily\n," + ",".join(ASSETS)
            + "\n20000103," + ",".join(["99"] * 49) + "\n")


def _write_csv(tmp_path, text=None):
    path = tmp_path / "49_Industry_Portfolios_Daily.csv"
    path.write_text(text if text is not None else _fixture(), encoding="utf-8")
    return path


def _zip_payload(text=None, member="49_Industry_Portfolios_Daily.csv"):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr(member, text if text is not None else _fixture())
    return payload.getvalue()


def test_selects_value_weighted_table_and_scales_compounds_once(tmp_path):
    panel = load_french49(_write_csv(tmp_path))
    assert panel.assets == ASSETS
    np.testing.assert_allclose(panel.close[:, 0], [100, 102, 100.98, 104.0094])
    np.testing.assert_allclose(panel.returns[1:, 0], [0.02, -0.01, 0.03])
    np.testing.assert_allclose(forward_returns(panel, 2)[:2, 0], [1.02 * 0.99 - 1, 0.99 * 1.03 - 1])
    assert np.isnan(panel.returns[0]).all()
    assert np.isnan(panel.volume).all()
    assert panel.metadata["synthetic"] is False
    assert panel.metadata["price_semantics"] == "cumulative_wealth_index"
    with pytest.raises(ExpressionError, match="unavailable"):
        evaluate_expression("volume", panel)
    assert np.isfinite(evaluate_expression("ts_mean(returns,2)", panel)[2:]).all()


def test_explicit_slice_resets_base_and_discards_only_first_retained_return(tmp_path):
    panel = load_french49(_write_csv(tmp_path), start="2000-01-04", end="2000-01-06")
    np.testing.assert_allclose(panel.close[:, 0], [100, 99, 101.97])
    np.testing.assert_allclose(panel.returns[1:, 0], [-0.01, 0.03])
    assert panel.metadata["wealth_base_date"] == "2000-01-04"
    assert panel.metadata["excluded_outside_range_dates"] == 1


@pytest.mark.parametrize("sentinel", [-99.99, -999])
def test_missing_source_returns_are_not_bridged_or_filled(tmp_path, sentinel):
    rows = [("20000103", [sentinel] + [1] * 48), ("20000104", [2] * 49),
            ("20000105", [3] * 49)]
    path = _write_csv(tmp_path, _fixture(rows))
    with pytest.raises(ValueError, match="missing return cells"):
        load_french49(path)
    panel = load_french49(path, start="2000-01-04")
    assert panel.metadata["source_missing_cells"] == 1
    assert panel.metadata["retained_missing_cells"] == 0


@pytest.mark.parametrize("text", [
    _fixture(header=tuple(reversed(ASSETS))),
    _fixture().replace(TABLE_NAME, "Unrecognized Returns"),
    _fixture().replace("20000104", "20000103"),
    _fixture().replace("20000104", "20001304"),
    _fixture().replace("20000104,2.0", "20000104,nan"),
    _fixture().replace("20000104,2.0", "20000104,-100"),
    _fixture().replace("20000104,2.0", "20000104,10001"),
    _fixture().replace("20000104,2.0", "20000104,unknown"),
])
def test_rejects_ambiguous_headers_dates_and_numeric_cells(tmp_path, text):
    with pytest.raises(ValueError):
        load_french49(_write_csv(tmp_path, text))


def test_zip_matches_csv_and_hash_tampering_is_rejected(tmp_path):
    path = tmp_path / "official.zip"
    path.write_bytes(_zip_payload())
    zipped = load_french49(path)
    plain = load_french49(_write_csv(tmp_path))
    np.testing.assert_array_equal(zipped.close, plain.close)
    path.with_suffix(".manifest.json").write_text(json.dumps({"raw_sha256": "wrong"}), encoding="utf-8")
    with pytest.raises(ValueError, match="hash differs"):
        load_french49(path)


@pytest.mark.parametrize("member", ["../49_Industry_Portfolios_Daily.csv", "/bad.csv", "other.csv"])
def test_unsafe_or_unsupported_archive_members_rejected(tmp_path, member):
    path = tmp_path / "bad.zip"
    path.write_bytes(_zip_payload(member=member))
    with pytest.raises(ValueError):
        load_french49(path)


def test_downloader_records_snapshot_without_overwriting(monkeypatch, tmp_path):
    class Response(io.BytesIO):
        status = 200

        def geturl(self):
            return "https://mba.tuck.dartmouth.edu/mock"

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response(_zip_payload()))
    manifest = download_french49(tmp_path / "raw")
    assert manifest["response_status"] == 200
    assert len(manifest["raw_sha256"]) == 64
    assert manifest["selected_table"] == TABLE_NAME
    panel = load_french49(manifest["raw_path"])
    assert panel.metadata["download_manifest"]["raw_sha256"] == manifest["raw_sha256"]
    with pytest.raises(FileExistsError):
        download_french49(tmp_path / "raw")
