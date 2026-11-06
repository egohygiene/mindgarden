"""Authored observations, exact dependencies, missed-event reconciliation and safe apply."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from mindgarden.application.dependency_builds import plan_build, reconcile_build
from mindgarden.adapters.generated_files import apply_generated
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import dependency_fixture as fixture


class DependencyBuildTests(unittest.TestCase):
    def setUp(self): fixture.setup(self)

    def test_full_reconciliation_changes_only_declared_consumers_without_events(self):
        before=plan_build(self.context,self.request)
        original_objects=self.vault.audit()['objects']
        fixture.update(self)
        after=plan_build(self.context,self.request)
        states={r['id']:r['state'] for r in reconcile_build(after,before.manifest)['outputs']}
        self.assertEqual(states,{'professional-profile':'stale','agent-context':'stale','unrelated-view':'current'})
        self.assertEqual(before.files['unrelated-view.json'],after.files['unrelated-view.json'])
        self.assertTrue(all(item in self.vault.audit()['objects'] for item in original_objects))
        self.assertFalse(after.manifest['canonical_evidence'])
        self.assertEqual(reconcile_build(after,after.manifest)['outputs'][0]['state'],'current')

    def test_same_inputs_have_identical_manifests_and_renderer_is_replaceable(self):
        first=plan_build(self.context,self.request)
        self.assertEqual(first.document(),plan_build(self.context,self.request).document())
        custom=plan_build(self.context,self.request,renderer=lambda records,contract:(canonical_json({'references':[r['reference'] for r in records]}),'json'))
        self.assertNotEqual(first.files['agent-context.json'],custom.files['agent-context.json'])
        self.assertEqual(first.manifest['projections'][0]['dependencies'],custom.manifest['projections'][0]['dependencies'])

    def test_denied_selection_unknown_policy_and_lower_scope_fail_without_leaks(self):
        original=deepcopy(self.request)
        self.request['outputs'][0]['records']=['denied-garden/denied-canary']
        with self.assertRaisesRegex(ContractError,'BUILD_INPUT') as diagnostic:plan_build(self.context,self.request)
        self.assertNotIn('denied-canary',str(diagnostic.exception))
        self.request=deepcopy(original);self.request['outputs'][0]['scope']=local_scope('public',publication='publishable')
        with self.assertRaisesRegex(ContractError,'BUILD_SCOPE'):plan_build(self.context,self.request)
        self.request=deepcopy(original);self.request['outputs'][0]['scope']['policy']['id']='unknown'
        with self.assertRaises(ContractError):plan_build(self.context,self.request)

    def test_observation_review_evidence_and_staleness_are_not_inferred(self):
        original=deepcopy(self.request)
        for mutate in (lambda o:o.update(state='proposed'),lambda o:o['evidence'][0].update(content_sha256='0'*64),lambda o:o.update(stale_after='2000-01-01T00:00:00Z')):
            self.request=deepcopy(original);mutate(self.request['outputs'][0]['observations'][0])
            with self.assertRaises(ContractError):plan_build(self.context,self.request)

    def test_cli_preview_apply_replay_and_source_change_invalidate_review(self):
        path=self.root/'request.json';path.write_bytes(canonical_json(self.request));output=self.root/'derived'
        args=['build-projections','--local-config',str(self.configuration),'--scope',str(self.session_path),'--input',str(path)]
        with redirect_stdout(io.StringIO()) as preview:self.assertEqual(main(args),0)
        digest=json.loads(preview.getvalue())['plan_sha256']
        apply=args+['--apply','--output-directory',str(output),'--plan-digest',digest]
        with redirect_stdout(io.StringIO()):self.assertEqual(main(apply),0);self.assertEqual(main(apply),0)
        fixture.update(self);path.write_bytes(canonical_json(self.request))
        with redirect_stderr(io.StringIO()):self.assertEqual(main(apply),3)
        self.assertEqual(json.loads((output/'projection-dependencies.json').read_text())['schema'],'mindgarden.projection-dependencies/v1')

    def test_unknown_existing_outputs_are_never_overwritten(self):
        plan=plan_build(self.context,self.request);output=self.root/'human';output.mkdir(mode=0o700);(output/'notes.txt').write_text('preserve')
        with self.assertRaisesRegex(ContractError,'GENERATED_CONFLICT'):
            apply_generated(output,plan.files,plan.document()['plan_sha256'],plan.document()['plan_sha256'],check_live=self.context.check_live,verify_inputs=lambda:None)
        self.assertEqual((output/'notes.txt').read_text(),'preserve')

    def test_committed_authored_fixture_and_lost_event_golden_match(self):
        root=Path(__file__).parent/'fixtures/dependency-builds'
        self.assertEqual(self.request,json.loads((root/'authored-request.json').read_text()))
        before=plan_build(self.context,self.request);fixture.update(self)
        actual=reconcile_build(plan_build(self.context,self.request),before.manifest)
        self.assertEqual(actual,json.loads((root/'expected-reconciliation.json').read_text()))
