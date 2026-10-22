"""Rebuild the extended constructed formulas in a temporary workspace and compare bytes."""
import contextlib
import importlib
import io
import json
from pathlib import Path
import tempfile

import common
from common import ROOT, read_rows, sha, write_json


def main():
    expected=read_rows(ROOT/'parts'/'extensions.jsonl')
    supplement=ROOT/'parts'/'rb-supplement.jsonl'
    if supplement.exists(): expected+=read_rows(supplement)
    with tempfile.TemporaryDirectory(prefix='matt-v3-repro-') as directory:
        out=Path(directory).resolve()
        assert out.is_relative_to(Path(tempfile.gettempdir()).resolve()) and out.name.startswith('matt-v3-repro-')
        module=importlib.import_module('build_extensions')
        common.ROOT=out; module.ROOT=out; module.archive_v2=lambda:None
        with contextlib.redirect_stdout(io.StringIO()): module.build()
        regenerated=read_rows(out/'parts'/'extensions.jsonl')
        if supplement.exists():
            supplement_module=importlib.import_module('build_rb_supplement'); supplement_module.ROOT=out
            with contextlib.redirect_stdout(io.StringIO()): supplement_module.main()
            regenerated+=read_rows(out/'parts'/'rb-supplement.jsonl')
        expected_by_id={r['id']:r for r in expected}
        assert set(expected_by_id)=={r['id'] for r in regenerated}
        for row in regenerated:
            assert row['sha256']==expected_by_id[row['id']]['sha256'],row['id']
            assert sha((out/row['path']).read_bytes())==row['sha256']
        report=dict(version='3.0.0',status='PASS',regenerated_formula_files=len(regenerated),
            generated_scenarios=len({r['scenario_id'] for r in regenerated}),
            byte_identical_formula_hashes=True,temporary_copy_removed_on_completion=True,
            source_originals='Preserved exact source archives and per-original SHA256; not re-downloaded for this check.',
            label_metadata='Budget-dependent oracle metadata is not required to reproduce byte-for-byte; formula bytes are.')
    common.ROOT=ROOT
    write_json(ROOT/'reproducibility-v3.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
