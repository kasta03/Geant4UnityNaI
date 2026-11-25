import os
import subprocess
import textwrap
import yaml

# --- KONFIGURACJA GLOBALNA ---
PROJECT_ID = "geant4-sim-kuba"
IMAGE_URL = f"europe-west1-docker.pkg.dev/{PROJECT_ID}/geant-repo/unity-cloud:v1"
UNITY_EXEC_PATH = "/app/game/mysim.x86_64" 

# --- PARAMETRY EKSPERYMENTU ---
common_params = {
    "particle": "e+",
    "material": "G4_SODIUM_IODIDE",
    "max_steps": 1000000,
    "checkpoint_interval": 100000, # Checkpoint co 100k
}

# 3 Warianty PPO
ppo_exps = [
    {"name": "ppo-eplus-nai-std", "lr": 3e-4, "batch": 1024, "beta": 1e-3},
    {"name": "ppo-eplus-nai-slow", "lr": 1e-4, "batch": 2048, "beta": 1e-3},
    {"name": "ppo-eplus-nai-ent", "lr": 3e-4, "batch": 1024, "beta": 5e-3},
]

# 3 Warianty SAC
sac_exps = [
    {"name": "sac-eplus-nai-std", "lr": 3e-4, "batch": 256, "ent": 0.5},
    {"name": "sac-eplus-nai-fast", "lr": 5e-4, "batch": 512, "ent": 0.5},
    {"name": "sac-eplus-nai-lowent", "lr": 3e-4, "batch": 256, "ent": 0.1},
]

def create_config(exp, trainer_type):
    config = {
        "behaviors": {
            "ElectronBehavior": {
                "trainer_type": trainer_type,
                "hyperparameters": {
                    "batch_size": exp["batch"],
                    "learning_rate": exp["lr"],
                    "buffer_size": exp["batch"] * 10 if trainer_type == "ppo" else 100000,
                },
                "network_settings": {
                    "normalize": True,
                    "hidden_units": 128,
                    "num_layers": 2
                },
                "max_steps": common_params["max_steps"],
                "checkpoint_interval": common_params["checkpoint_interval"],
                "summary_freq": 5000,
                "time_horizon": 128,
            }
        }
    }
    
    hp = config["behaviors"]["ElectronBehavior"]["hyperparameters"]
    if trainer_type == "ppo":
        hp.update({"beta": exp["beta"], "epsilon": 0.2, "lambd": 0.95, "num_epoch": 3})
    else: # SAC
        hp.update({
            "init_entcoef": exp["ent"],
            "tau": 0.005,
            "steps_per_update": 1,
            "save_replay_buffer": False
        })
    return config

def deploy(exp, trainer_type):
    name = exp["name"]
    print(f"Deploying job: {name}...")

    # 1. Tworzenie config.yaml
    conf = create_config(exp, trainer_type)
    with open("config_tmp.yaml", "w") as f:
        yaml.dump(conf, f)

    # 2. Tworzenie manifestu Joba
    job_manifest = textwrap.dedent(f"""
        apiVersion: batch/v1
        kind: Job
        metadata:
          name: {name}
        spec:
          template:
            spec:
              containers:
              - name: geant-ml-container
                image: {IMAGE_URL}
                resources:
                  requests:
                    cpu: "2"
                    memory: "4Gi"
                env:
                - name: PARTICLE_NAME
                  value: "{common_params['particle']}"
                - name: DETECTOR_MATERIAL
                  value: "{common_params['material']}"
                - name: W_POS
                  value: "50"
                - name: W_ENERGY
                  value: "15"
                volumeMounts:
                - name: config-volume
                  mountPath: /app/config.yaml
                  subPath: config.yaml
                command: ["/app/entrypoint.sh"]
                # URUCHOMIENIE + SLEEP NA KOŃCU
                args: ["bash", "-c", "mlagents-learn /app/config.yaml --run-id={name} --no-graphics --env={UNITY_EXEC_PATH} --num-envs=1; echo 'TRENING ZAKONCZONY'; sleep infinity"]
              volumes:
              - name: config-volume
                configMap:
                  name: {name}-config
              restartPolicy: Never
          backoffLimit: 0
    """).strip()

    with open("job_tmp.yaml", "w") as f:
        f.write(job_manifest)

    # 3. Wysyłka do klastra
    subprocess.run(["kubectl", "delete", "job", name], stderr=subprocess.DEVNULL)
    subprocess.run(["kubectl", "delete", "configmap", f"{name}-config"], stderr=subprocess.DEVNULL)
    subprocess.run(["kubectl", "create", "configmap", f"{name}-config", "--from-file=config.yaml=config_tmp.yaml"])
    subprocess.run(["kubectl", "apply", "-f", "job_tmp.yaml"])
    
    # Usuwanie plików tymczasowych
    os.remove("config_tmp.yaml")
    os.remove("job_tmp.yaml")

if __name__ == "__main__":
    for e in ppo_exps: deploy(e, "ppo")
    for e in sac_exps: deploy(e, "sac")
    print("\n[SUKCES] 6 jobów wysłanych. Każdy trenuje e+ w NaI do 1M kroków.")