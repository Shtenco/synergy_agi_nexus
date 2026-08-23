import json, traceback

result = {"stage": "START", "ok": False}
try:
    import arc_agi
    result["arc_agi_import"] = "OK"
    result["stage"] = "ARCADE_INIT"
    arc = arc_agi.Arcade()
    result["arcade_init"] = "OK"
    result["stage"] = "GET_ENVIRONMENTS"
    envs = arc.get_environments()
    result["environment_count"] = len(envs) if envs is not None else None
    result["environments"] = [getattr(e, "game_id", str(e)) for e in (envs or [])]
    result["stage"] = "MAKE_LS20"
    env = arc.make("ls20")
    result["make_ls20"] = env is not None
    if env is not None:
        result["action_space"] = [str(a) for a in env.action_space]
        result["reset_type"] = str(type(env.reset()))
    result["stage"] = "DONE"
    result["ok"] = True
except Exception as e:
    result["error_type"] = type(e).__name__
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()
finally:
    with open("arc3_probe_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
