"""Season4-specific bounded encounters and schedules, using real seeded observations."""
import copy
import agent
from test_neighbor import scene, _example, _visitor_at, _FakeLLM
from sandbox.village import me, people


def test_meeting_ends_and_evening_stall_keeper_goes_home(scene, monkeypatch):
    _, observations, _, _ = scene
    obs = copy.deepcopy(observations["player_6"])
    resident = agent.Agent()
    resident.reset(9, obs)
    monkeypatch.setattr(people, "nearby", lambda obs: ())
    resident.memory["phase_started"] = 481
    obs.update(phase="midday", tick=510)
    assert agent.assign(obs, resident.memory) == ("gather_at", "inn")
    obs["tick"] = 700
    assert agent.assign(obs, resident.memory) == ("tend", resident.memory["work_prop"])
    resident.memory["phase_started"] = 721
    obs.update(phase="evening", tick=730)
    assert agent.assign(obs, resident.memory) == ("gather_at", "pump_0")
    obs["tick"] = 850
    assert agent.assign(obs, resident.memory) == ("go_to", resident.memory["home"])


def test_brief_visitor_departure_cannot_reset_greeting_cooldown(scene, monkeypatch):
    resident, obs = _example(scene)
    obs.update(phase="morning", tick=100)
    near = [_visitor_at(me.position(obs))]
    monkeypatch.setattr(people, "nearby", lambda obs: tuple(near))
    monkeypatch.setattr(people, "seen", lambda obs: tuple(near))
    resident.act(obs)
    assert resident.memory["routine"] == "greet"
    obs["tick"] += agent.REACTION_TICKS
    resident.act(obs)
    assert resident.memory["routine"] == "tend"
    near.clear()
    obs["tick"] += 1
    resident.act(obs)
    near.append(_visitor_at(me.position(obs)))
    obs["tick"] += 1
    resident.act(obs)
    assert resident.memory["routine"] == "tend"


def test_season4_visitor_reply_never_calls_llm(scene):
    resident, obs = _example(scene)
    talk = agent.VillageDialogue("a pump worker")
    talk.llm = fake = _FakeLLM()
    obs["nearby"] = (_visitor_at(me.position(obs)),)
    obs["phase"] = "morning"
    talk.observe(obs)
    talk.receive([{"from": "player_0", "to": None, "text": "Hello"}])
    lines = talk.messages()
    assert lines and lines[0]["to"] == "player_0"
    assert fake.requests == []
