"""python3 -B evals/test_session_tools.py — 원본 형식·시각·기존 알림 이행 회귀 시험."""
import contextlib
import datetime
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

timeline = load('timeline')
hook = load('session_hook')

class SessionToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='session-tools-', dir=ROOT / 'evals')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.transcript = self.root / 'session.jsonl'
        self.state = self.root / 'pending.tsv'
        self.daily = self.root / 'daily'
        self.daily.mkdir()
        self.now = datetime.datetime.now(timeline.KST).replace(second=0, microsecond=0)
        self.sid = 'abcdef12-1234-1234-1234-123456789abc'
        self.addCleanup(patch.stopall)
        patch.object(hook, 'STATE', self.state).start()
        patch.object(hook, 'DAILY', self.daily).start()

    def write(self, records):
        self.transcript.write_text('\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8')

    def msg(self, role, text, at, codex=False):
        stamp = at.isoformat() if hasattr(at, 'isoformat') else at
        if codex:
            return {'timestamp': stamp, 'type': 'response_item', 'payload': {'type': 'message', 'role': role, 'content': [{'type': 'input_text' if role == 'user' else 'output_text', 'text': text}]}}
        return {'timestamp': stamp, 'type': role, 'message': {'content': [{'type': 'text', 'text': text}]}}

    def run_timeline(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            timeline.main(['--session', str(self.transcript), *args])
        return out.getvalue()

    def run_start(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out): hook.on_start({})
        return out.getvalue()

    def recorded(self, at):
        (self.daily / (self.now.strftime('%Y-%m-%d') + '.md')).write_text('---\nsessions:\n  - "Claude Code · ' + self.sid + ' · 01-01 00:00 ~ ' + at.strftime('%m-%d %H:%M') + '"\n---\n')

    def test_formats_have_same_kst_utterances_and_span(self):
        outputs=[]
        for codex in (False, True):
            self.write([self.msg('user', '기록해줘', '2026-11-09T23:59:00Z', codex), self.msg('assistant', '처리 완료', '2026-11-10T00:02:00Z', codex)])
            outputs.append(self.run_timeline('--span'))
        self.assertEqual(*outputs)
        self.assertIn('11-10 08:59  발언  기록해줘', outputs[0])
        self.assertIn('11-10 08:59 ~ 09:02', outputs[0])

    def test_codex_mirrors_and_injected_context_do_not_extend_span(self):
        self.write([self.msg('user', '실제 요청', '2026-11-10T00:00:00Z', True), {'timestamp':'2026-11-10T01:00:00Z','type':'event_msg','payload':{'type':'user_message','message':'실제 요청'}},self.msg('user','# AGENTS.md instructions\n설정','2026-11-10T02:00:00Z',True), self.msg('developer','지침','2026-11-10T03:00:00Z',True)])
        out=self.run_timeline('--span')
        self.assertEqual(out.count('실제 요청'),1)
        self.assertIn('09:00 ~ 09:00',out)
        self.assertNotIn('설정',out)

    def test_function_and_custom_tools_and_filters(self):
        self.write([self.msg('user','첫 발언','2026-11-10T00:00:00Z',True), {'timestamp':'2026-11-10T00:01:00Z','type':'response_item','payload':{'type':'function_call','name':'read','arguments':'{"title":"파일 읽기"}'}},{'timestamp':'2026-11-10T00:02:00Z','type':'response_item','payload':{'type':'custom_tool_call','name':'exec','input':'raw code'}},self.msg('assistant','완료','2026-11-10T00:03:00Z',True)])
        out=self.run_timeline('--tools','--span','--since','11-10 09:01','--until','11-10 09:02')
        self.assertNotIn('첫 발언',out)
        self.assertIn('도구  read 파일 읽기',out)
        self.assertIn('도구  exec',out)
        self.assertIn('09:01 ~ 09:02',out)
        self.assertNotIn('도구',self.run_timeline())

    def test_claude_commands_answers_rejections_and_queued(self):
        records=[self.msg('user','<command-name>/record</command-name><command-args>today</command-args>','2026-11-10T00:00:00Z')]
        for text in ['Your questions have been answered: 승인','The user doesn\'t want to proceed with this tool use; the user said: 중지']:
            records.append({'timestamp':'2026-11-10T00:01:00Z','type':'user','message':{'content':[{'type':'tool_result','content':text}]}})
        records.append({'timestamp':'2026-11-10T00:02:00Z','type':'attachment','attachment':{'type':'queued_command','prompt':'추가 요청'}})
        self.write(records);out=self.run_timeline('--span')
        for text in ['명령  /record today','답변  승인','거절  중지','발언  추가 요청','09:00 ~ 09:02']:self.assertIn(text,out)

    def test_invalid_lines_are_skipped_and_width_is_honored(self):
        self.write([self.msg('user','abcdefghijk','bad-date'),self.msg('user','abcdefghijk','2026-11-10T00:00:00Z')])
        with self.transcript.open('a') as f:f.write('{broken\n')
        self.assertIn('abcd…',self.run_timeline('--width','5'))

    def test_codex_id_lookup(self):
        dest=self.root/'codex/2026/11/10';dest.mkdir(parents=True)
        p=dest/('rollout-2026-11-10-'+self.sid+'.jsonl');p.write_text('')
        with patch.object(timeline,'PROJECTS',self.root/'claude'),patch.object(timeline,'CODEX_SESSIONS',self.root/'codex'):
            self.assertEqual(timeline.find_session('abcdef12'),p)

    def three_messages(self, at):
        self.write([self.msg('user',f'요청 {i}',at-datetime.timedelta(minutes=3-i)) for i in range(3)]+[self.msg('assistant','완료',at)])

    def test_end_uses_activity_and_keeps_close_time_for_retention(self):
        at=self.now-datetime.timedelta(days=60)
        self.three_messages(at)
        hook.on_end({'session_id':self.sid,'transcript_path':str(self.transcript),'cwd':str(self.root)})
        row=hook.read_state()[0]
        self.assertEqual(row[1],at.strftime('%Y-%m-%d %H:%M'))
        self.assertEqual(row[4],str(self.transcript))
        self.assertEqual(row[5],self.now.strftime('%Y-%m-%d %H:%M'))
        self.assertIn('아직 기록하지 않은',self.run_start())

    def test_legacy_close_time_is_resolved_to_already_recorded_activity(self):
        at=self.now-datetime.timedelta(days=60);self.three_messages(at);self.recorded(at)
        hook.write_state([[self.sid,self.now.strftime('%Y-%m-%d %H:%M'),str(self.root),'3']])
        with patch.object(hook.timeline,'find_session',return_value=self.transcript):self.assertEqual(self.run_start(),'')
        self.assertEqual(hook.read_state(),[])

    def test_resume_with_new_activity_still_notifies(self):
        at=self.now-datetime.timedelta(minutes=5);self.recorded(at);self.three_messages(self.now)
        hook.on_end({'session_id':self.sid,'transcript_path':str(self.transcript),'cwd':str(self.root)})
        self.assertIn('마지막 활동',self.run_start())
        self.assertEqual(len(hook.read_state()),1)

    def test_missing_transcript_preserves_pending_until_expiry(self):
        hook.write_state([[self.sid,self.now.strftime('%Y-%m-%d %H:%M'),str(self.root),'3']])
        with patch.object(hook.timeline,'find_session',side_effect=FileNotFoundError):self.assertIn('아직 기록하지 않은',self.run_start())
        row=hook.read_state()[0];row[5]=(self.now-datetime.timedelta(days=15)).strftime('%Y-%m-%d %H:%M');hook.write_state([row])
        self.assertEqual(self.run_start(),'')

    def test_fewer_than_three_user_utterances_are_not_queued(self):
        self.write([self.msg('user','요청',self.now),self.msg('assistant','답변',self.now)])
        hook.on_end({'session_id':self.sid,'transcript_path':str(self.transcript)})
        self.assertEqual(hook.read_state(),[])

    def test_isolated_hook_invocation_imports_shared_parser(self):
        result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/session_hook.py'),'invalid-test-event'],input='{}',capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stderr,'')

if __name__=='__main__':unittest.main(verbosity=2)
