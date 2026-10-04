import json, sys, platform, os, subprocess
env = {
 "commit_sha": subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip(),
 "commit_date": subprocess.check_output(["git","log","-1","--format=%ci"]).decode().strip(),
 "python_version": sys.version,
 "platform": platform.platform(),
 "machine": platform.machine(),
 "cpu_count": os.cpu_count(),
 "cwd": os.getcwd(),
}
for m in ["torch","torch_geometric","sklearn","numpy","pandas","networkx","matplotlib","psutil","scipy","fastavro"]:
    try:
        mod = __import__(m)
        env[m+"_version"] = getattr(mod, "__version__", "?")
    except Exception:
        env[m+"_version"] = "MISSING"
try:
    import torch
    env["cuda_available"] = torch.cuda.is_available()
    env["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
except Exception:
    env["cuda_available"] = False
    env["gpu"] = None
with open("audit/original_reproduction/env/environment.json", "w") as f:
    json.dump(env, f, indent=2)
print(json.dumps(env, indent=2))
