"""Reviewed memory is disposable; budgets and stale/private sources fail closed."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from mindgarden.application.memory import plan_memory
from mindgarden.domain.contracts import canonical_json, ContractRegistry
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import memory_fixture as fixture


class MemoryTests(unittest.TestCase):
    def setUp(self):fixture.setup(self)

    def test_all_actions_compress_bodies_and_preserve_provenance_deterministically(self):
        preview,files=plan_memory(self.context,self.request)
        self.assertEqual(preview['violations'],[])
        self.assertEqual(preview,plan_memory(self.context,self.request)[0])
        self.assertEqual({d['action'] for d in preview['projection']['decisions']},{'keep','merge','rewrite','demote','expire','split','pin'})
        self.assertLess(preview['metrics']['snippet_body_bytes'],preview['metrics']['source_body_bytes']//10)
        self.assertEqual(ContractRegistry().errors(preview['projection'],'memory-projection'),[])
        for snippet in preview['projection']['snippets']:self.assertTrue(snippet['sources'][0]['evidence'])
        self.assertIn(b'Sources: synthetic-garden/',files['memory-snippets.md'])
        self.assertFalse(preview['projection']['canonical'])

    def test_overflow_keeps_all_candidates_for_explicit_review(self):
        self.request['budgets'].update(max_total_bytes=100,max_snippets=1,minimum_priority=99)
        self.request['budgets']['category_quotas']['preference']=1
        preview,_=plan_memory(self.context,self.request)
        self.assertEqual(preview['status'],'review-required-over-budget')
        self.assertEqual(len(preview['projection']['snippets']),6)
        reasons={v['reason'] for v in preview['violations']}
        self.assertTrue({'total-byte-budget','snippet-count-budget','priority-below-profile-minimum','category-quota:preference'}<=reasons)

    def test_unknown_tokenizer_fails_and_explicit_counter_enforces_its_own_contract(self):
        self.request['budgets']['max_tokens']=1
        with self.assertRaisesRegex(ContractError,'MEMORY_TOKENIZER_UNAVAILABLE'):plan_memory(self.context,self.request)
        self.request['target']['tokenizer']='synthetic-whitespace/v1'
        result,_=plan_memory(self.context,self.request,tokenizers={'synthetic-whitespace/v1':lambda text:len(text.split())})
        self.assertIn('declared-token-budget',{v['reason'] for v in result['violations']})

    def test_source_revision_scope_and_review_conflicts_do_not_export(self):
        original=deepcopy(self.request)
        self.request['candidates'][0]['sources'][0]['revision']='sha256:'+'0'*64
        with self.assertRaisesRegex(ContractError,'MEMORY_SOURCE_CHANGED'):plan_memory(self.context,self.request)
        self.request=deepcopy(original);self.request['scope']=local_scope('public',publication='publishable')
        with self.assertRaisesRegex(ContractError,'MEMORY_SCOPE'):plan_memory(self.context,self.request)
        self.request=deepcopy(original);self.request['candidates'][0]['action']='demote';self.request['candidates'][0]['outputs']=[];self.request['scope']=local_scope('public')
        with self.assertRaisesRegex(ContractError,'MEMORY_SCOPE'):plan_memory(self.context,self.request)

    def test_temporary_dates_specific_values_and_review_half_life_are_visible(self):
        output=self.request['candidates'][0]['outputs'][0]
        output.update(category='temporary',durability='temporary',body='Synthetic balance $1234 on 2026-11-04.',half_life_days=1)
        preview,_=plan_memory(self.context,self.request)
        reasons={v['reason'] for v in preview['violations']}
        self.assertTrue({'temporary-context-needs-expiry','specific-value-needs-expiry-or-explicit-pin','half-life-requires-review'}<=reasons)
        output['stale_after']='2026-11-05T00:00:00Z'
        self.assertIn('expired',{v['reason'] for v in plan_memory(self.context,self.request)[0]['violations']})

    @patch("mindgarden.application.memory.QueryContext.load")
    def test_cli_apply_is_digest_bound_and_canonical_sources_remain_identical(self, load):
        load.return_value=self.context
        before={p:p.read_bytes() for p in self.workspace.rglob('*') if p.is_file()}
        path=self.root/'memory-plan.json';path.write_bytes(canonical_json(self.request));destination=self.root/'memory-export'
        args=['memory','--local-config',str(self.configuration),'--scope',str(self.session_path),'--input',str(path)]
        with redirect_stdout(io.StringIO()) as preview:self.assertEqual(main(args),0)
        digest=json.loads(preview.getvalue())['plan_sha256'];apply=args+['--apply','--output-directory',str(destination),'--plan-digest',digest]
        with redirect_stdout(io.StringIO()):self.assertEqual(main(apply),0);self.assertEqual(main(apply),0)
        self.request['candidates'][0]['outputs'][0]['body']='Changed proposed wording.';path.write_bytes(canonical_json(self.request))
        with redirect_stderr(io.StringIO()):self.assertEqual(main(apply),3)
        self.assertEqual(before,{p:p.read_bytes() for p in self.workspace.rglob('*') if p.is_file()})

    def test_committed_authored_plan_and_metrics_match(self):
        root=Path(__file__).parent/'fixtures/memory'
        self.assertEqual(self.request,json.loads((root/'authored-plan.json').read_text()))
        self.assertEqual(plan_memory(self.context,self.request)[0]['metrics'],json.loads((root/'expected-metrics.json').read_text()))

    def test_unreviewed_or_overflow_apply_leaves_no_output(self):
        path=self.root/'blocked.json';destination=self.root/'blocked-output'
        self.request['budgets']['max_total_bytes']=1;path.write_bytes(canonical_json(self.request))
        preview,_=plan_memory(self.context,self.request)
        args=['memory','--local-config',str(self.configuration),'--scope',str(self.session_path),'--input',str(path),
              '--apply','--output-directory',str(destination),'--plan-digest',preview['plan_sha256']]
        with patch('mindgarden.application.memory.QueryContext.load',return_value=self.context),redirect_stderr(io.StringIO()):
            self.assertEqual(main(args),3)
        self.assertFalse(destination.exists())
