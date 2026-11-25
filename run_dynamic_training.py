import os
import sys

TEMPLATE_PATH = "/app/config_template.yaml"
FINAL_CONFIG_PATH = "/app/final_config.yaml"
GAME_PATH = "/app/game/mysim.x86_64"

batch_size = os.environ.get("BATCH_SIZE", "1024")
buffer_size = os.environ.get("BUFFER_SIZE", "10240")
learning_rate = os.environ.get("LEARNING_RATE", "3.0e-4")
hidden_units = os.environ.get("HIDDEN_UNITS", "128")
num_layers = os.environ.get("NUM_LAYERS", "2")
memory_size_str = os.environ.get("MEMORY_SIZE", "0")

memory_block = ""
try:
    mem_int = int(memory_size_str)
    if mem_int > 0:
        memory_block = (
            "memory:\n"
            "        sequence_length: 64\n"
            f"        memory_size: {mem_int}"
        )
except ValueError:
    pass

params = {
    "batch_size": batch_size,
    "buffer_size": buffer_size,
    "learning_rate": learning_rate,
    "hidden_units": hidden_units,
    "num_layers": num_layers,
    "memory_block": memory_block
}

print(f"[WRAPPER] Generating config from template...")

try:
    with open(TEMPLATE_PATH, "r") as f:
        template = f.read()
    
    final_yaml = template.format(**params)
    
    with open(FINAL_CONFIG_PATH, "w") as f:
        f.write(final_yaml)
        
    print(f"[WRAPPER] Config generated at {FINAL_CONFIG_PATH}")
    print(final_yaml)
except Exception as e:
    print(f"[WRAPPER] Error: {e}")
    sys.exit(1)

run_id = os.environ.get("RUN_ID", "Default_Run")
cmd = f"mlagents-learn {FINAL_CONFIG_PATH} --run-id={run_id} --env={GAME_PATH} --no-graphics --force"

print(f"[WRAPPER] Starting ML-Agents: {cmd}")
os.system(cmd)