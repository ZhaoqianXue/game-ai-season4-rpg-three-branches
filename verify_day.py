"""Local full-day behavior probes. No LLM or network calls.

The visitor is the supplied scripted visitor with its random stream explicitly
seeded for this probe. Chat is delivered only within current hearing; observations
remain private to each actor. This complements, not replaces, the official harness.
"""
import json
import argparse
import time
import agent
from sandbox.env import META, make_env
from sandbox.env.three_branches import scripted_visitor
from sandbox.harness.environment import resolve_parameters
from sandbox.village import action, day, geometry, layout, me, people


def probe(seed, limit=1200):
    env = make_env(resolve_parameters(META, {"seat_plan": "cast_10", "daynight": True}))
    obs, _ = env.reset(seed=seed)
    actors = {player: agent.Agent() for player in obs if player != "player_0"}
    visitor = scripted_visitor.Agent()
    visitor.reset(seed, obs["player_0"])
    visitor._rng.seed(seed)  # Test-only reproducibility; production builtin chooses its own stream.
    for player, actor in actors.items():
        actor.reset(seed, obs[player])
    inbox = {player: [] for player in obs}
    jobs = {player: [] for player in actors}
    successes = {player: 0 for player in actors}
    greeted = set()
    messages = 0
    max_act = 0.0
    max_cpu = 0.0
    ticks = 0
    phases_seen = {}
    while env.agents and ticks < limit:
        orders = {"player_0": visitor.act(obs["player_0"])}
        for player, actor in actors.items():
            started = time.perf_counter()
            cpu_started = time.process_time()
            orders[player] = actor.act(obs[player])
            max_act = max(max_act, time.perf_counter() - started)
            max_cpu = max(max_cpu, time.process_time() - cpu_started)
            if not jobs[player] or jobs[player][-1][1] != actor.memory["routine"]:
                jobs[player].append((day.tick(obs[player]), actor.memory["routine"]))
            if actor.memory["routine"] == "greet":
                greeted.add(player)
        assert all(env.action_space(p).contains(order) for p, order in orders.items())
        outgoing = {p: a.chat(inbox[p]) for p, a in actors.items()}
        outgoing["player_0"] = visitor.chat(inbox["player_0"])
        inbox = {player: [] for player in obs}
        for sender, lines in outgoing.items():
            listeners = {str(p["id"]) for p in people.nearby(obs[sender])}
            for line in lines:
                assert len(line["text"]) <= 200
                messages += 1
                recipients = listeners if line["to"] is None else listeners & {line["to"]}
                for recipient in recipients:
                    inbox[recipient].append({"from": sender, "to": line["to"], "text": line["text"]})
        obs, *_ = env.step(orders)
        ticks += 1
        if ticks in (120, 480, 720, 960, 1200):
            phases_seen[ticks] = {p: {"position": dict(me.position(obs[p])),
                                     "goal": a.memory["goal"], "work": a.memory["work_prop"],
                                     "expression": dict(me.expression(obs[p]))}
                                 for p, a in actors.items()}
        for player in actors:
            if me.expression(obs[player])["type"] == "use":
                successes[player] += 1
    homes = [p for p, a in actors.items() if layout.building_at(obs[p], me.position(obs[p])) == a.memory["home"]]
    sleeping = [p for p in actors if me.expression(obs[p])["type"] == "sleep"]
    result = {"seed": seed, "ticks": ticks, "workers": sum(n > 0 for n in successes.values()),
              "at_home": len(homes), "sleeping": len(sleeping), "visitor_greeted_by": sorted(greeted),
              "work_counts": successes,
              "messages": messages, "max_act_ms": round(max_act * 1000, 2),
              "max_act_cpu_ms": round(max_cpu * 1000, 2),
              "example_plans": {p: jobs[p] for p in ("player_1", "player_6")}}
    print(json.dumps(result), flush=True)
    missing = [p for p, count in successes.items() if not count]
    if missing:
        print(json.dumps({"seed": seed, "missing_work_details":
                          {tick: {p: values[p] for p in missing} for tick, values in phases_seen.items()}}, default=str), flush=True)
    env.close()
    if limit < 1200:
        return
    assert ticks == 1200 and len(homes) == 10 and len(sleeping) == 10
    assert all(successes.values())
    assert max_act < 0.25


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 11, 23])
    parser.add_argument("--ticks", type=int, default=1200)
    args = parser.parse_args()
    for seed in args.seeds:
        probe(seed, args.ticks)
