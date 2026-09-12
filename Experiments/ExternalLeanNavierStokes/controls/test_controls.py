"""Adversarial parser/report checks; Lean controls execute only on the runner."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runner'))
from closure import Export, ClosureError, print_axioms, dumps
from execute import P, Run
from seal import validate, inventory, seal


def fixture(offset=0):
    name=lambda n:n+offset
    return [
      {'meta':{'format':{'version':'3.1.0'},'lean':{'version':'fixture'},'exporter':{'name':'fixture'}}},
      *[{'in':name(i),'str':{'pre':0,'str':n}} for i,n in enumerate(['used','unused','helper','target'],1)],
      {'ie':0,'sort':0},
      {'axiom':{'name':name(1),'levelParams':[],'type':0,'isUnsafe':False}},
      {'axiom':{'name':name(2),'levelParams':[],'type':0,'isUnsafe':False}},
      {'ie':1,'const':{'name':name(1),'us':[]}},
      {'thm':{'name':name(3),'levelParams':[],'type':0,'value':1,'all':[]}},
      {'ie':2,'const':{'name':name(3),'us':[]}},
      {'thm':{'name':name(4),'levelParams':[],'type':0,'value':2,'all':[]}}]


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.d=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def parse(self,rows=None,limits=None):
        p=self.d/'e.ndjson';p.write_text(''.join(dumps(r)+'\n' for r in (fixture() if rows is None else rows)))
        return Export(p,P['resource_limits'] if limits is None else limits)
    def test_transitive_used_not_unused(self):
        e=self.parse();g,n,path=e.graph('target')
        self.assertEqual(g['axioms'],['used']);self.assertNotIn('unused',n)
        self.assertEqual(path('used'),['target','helper','used'])
    def test_missing_target_never_empty_success(self):
        with self.assertRaisesRegex(ClosureError,'missing exact target'):self.parse().graph('absent')
    def test_missing_reference_is_not_a_primitive(self):
        rows=[r for r in fixture() if not ('axiom' in r and r['axiom']['name']==1)]
        with self.assertRaisesRegex(ClosureError,'missing referenced constant'):self.parse(rows).graph('target')
    def test_unknown_duplicate_truncated_records_fail(self):
        with self.assertRaises(ClosureError):self.parse(fixture()+[{'future':{}}])
        with self.assertRaises(ClosureError):self.parse(fixture()+[fixture()[-1]])
        p=self.d/'bad';p.write_text(dumps(fixture()[0]))
        with self.assertRaisesRegex(ClosureError,'truncated'):Export(p,P['resource_limits'])
    def test_normalized_graph_independent_of_name_indices(self):
        a=self.parse().graph('target')[0];b=self.parse(fixture(20)).graph('target')[0]
        self.assertEqual(a,b)
    def test_caps_fail_closed(self):
        cap={**P['resource_limits'],'edges_per_target':1}
        with self.assertRaisesRegex(ClosureError,'edge cap'):self.parse(limits=cap).graph('target')
    def test_axiom_output_is_measured_target_specific(self):
        self.assertEqual(print_axioms("'probe' does not depend on any axioms",'probe'),[])
        self.assertEqual(print_axioms("'probe' depends on axioms: [sorryAx]",'probe'),['sorryAx'])
        with self.assertRaises(ClosureError):print_axioms('', 'probe')
        with self.assertRaises(ClosureError):print_axioms("'other' depends on axioms: []", 'probe')
    def test_statement_shape_change_changes_digest(self):
        a=self.parse().graph('target')[0]['type_digest'];rows=fixture();rows[-1]['thm']['type']=1
        b=self.parse(rows).graph('target')[0]['type_digest'];self.assertNotEqual(a,b)
    def test_failure_bundle_and_forged_success(self):
        work=self.d/'work';work.mkdir();raw=self.d/'raw'
        r=Run(work,raw);r.failure={'failure_class':'UNAVAILABLE_RUNNER_CAPABILITY','reason':'test fixture','command_id':None};r.finish()
        validate(raw);self.assertEqual(r.targets['R3']['primary_disposition'],'ENVIRONMENT_NOT_REPRODUCIBLE')
        p=raw/'targets.json';obj=json.loads(p.read_text());obj['R3']['axes']['dependency_graph']={'status':'PASS','reason':None,'failure_class':None};p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ClosureError,'sentinel'):validate(raw)
    def test_sealing_rejects_symlink_and_missing_files(self):
        (self.d/'link').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ClosureError,'symlink'):inventory(self.d)
        (self.d/'link').unlink()
        with self.assertRaisesRegex(ClosureError,'missing required'):validate(self.d)
    def test_replay_cannot_trigger_on_pr_or_document_commit(self):
        workflow=(ROOT.parents[1]/'.github/workflows/external-lean-navier-stokes.yml').read_text()
        self.assertIn('  create:',workflow)
        self.assertNotIn('  pull_request:',workflow);self.assertNotIn('  push:',workflow)
        self.assertIn("github.event.ref == 'execute/external-ns-replay-v1'",workflow)
        self.assertIn('github.run_attempt == 1',workflow)
        self.assertIn('persist-credentials: false',workflow)
        self.assertNotIn('${{ secrets.',workflow)


if __name__=='__main__':unittest.main()
