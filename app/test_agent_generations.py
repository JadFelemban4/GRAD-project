"""Replacing a model must invalidate cached/streamed frames and answers."""
import threading
import time
import unittest
import numpy as np

from app.agent_api import EpisodeStore
from app.agent_api import install
from fastapi import FastAPI
from fastapi.testclient import TestClient
from engine_env import OBS_DIM


class GenerationTests(unittest.TestCase):
    key = ('runs_fixture', 0, 1)

    def make(self, generation, tracer=None, loader=None):
        def record(policies, episode, emit):
            emit({'k': 0}, [np.zeros(OBS_DIM), np.zeros(OBS_DIM)])
            return [{}, {}]
        return EpisodeStore(loader=loader or (lambda runs, seed: (lambda *a: None, lambda *a: None)),
                            tracer=tracer or record, episode_for=lambda *a: {},
                            generation_for=lambda key: generation[0])

    def finish(self, store):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            body = store.poll(self.key)
            if body['status'] == 'ready':
                return body
            time.sleep(.005)
        self.fail('fixture build did not finish')

    def test_cached_trace_cannot_be_read_as_a_replacement_generation(self):
        generation = ['old']
        store = self.make(generation)
        body = self.finish(store)
        self.assertEqual(body['generation'], 'old')
        self.assertEqual(store.trace(self.key).generation, 'old')
        generation[0] = 'new'
        self.assertIsNone(store.trace(self.key))
        stale = store.poll(self.key, since=1, generation='old')
        self.assertEqual(stale['status'], 'invalidated')
        self.assertEqual(stale['frames'], [])
        self.assertEqual(self.finish(store)['generation'], 'new')

    def test_unrelated_inputs_leave_selected_trace_available(self):
        generation = ['selected']
        store = self.make(generation)
        self.finish(store)
        trace = store.trace(self.key)
        self.assertIs(store.trace(self.key), trace)
        self.assertEqual(store.poll(self.key, generation='selected')['status'], 'ready')

    def test_source_changed_during_build_never_publishes_trace(self):
        generation = ['old']
        entered, release = threading.Event(), threading.Event()
        def tracer(policies, episode, emit):
            entered.set()
            release.wait(2)
            emit({'k': 0}, [np.zeros(OBS_DIM), np.zeros(OBS_DIM)])
            return [{}, {}]
        store = self.make(generation, tracer=tracer)
        store.poll(self.key)
        self.assertTrue(entered.wait(2))
        generation[0] = 'new'
        release.set()
        deadline = time.monotonic() + 2
        while store._active is not None and time.monotonic() < deadline:
            time.sleep(.005)
        self.assertIsNone(store.trace(self.key))
        self.assertEqual(len(store._cache), 0)

    def test_answer_for_replaced_generation_is_refused_before_and_after_the_call(self):
        generation = ['a' * 64]
        store = self.make(generation)
        self.finish(store)
        class FakeModel:
            calls = 0
            def ask(self, trace, step):
                self.calls += 1
                generation[0] = 'b' * 64
                return {'answers': {'fixture': 'obsolete'}}
        model, app = FakeModel(), FastAPI()
        install(app, store=store, laya=model)
        client = TestClient(app, base_url='http://localhost:8000')
        headers = {'Origin': 'http://localhost:8000'}
        body = {'trace': 'runs_fixture/0/1', 'step': 0, 'generation': 'f' * 64}
        stale = client.post('/api/agents/laya', json=body, headers=headers)
        self.assertEqual(stale.json()['code'], 'no_trace')
        self.assertEqual(model.calls, 0)
        body['generation'] = 'a' * 64
        changed = client.post('/api/agents/laya', json=body, headers=headers)
        self.assertEqual(changed.json()['code'], 'no_trace')
        self.assertNotIn('answers', changed.json())
        self.assertEqual(model.calls, 1)


if __name__ == '__main__':
    unittest.main()
