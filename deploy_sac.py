import os
import subprocess
import textwrap

# --- GLOBALNA KONFIGURACJA ---
PROJECT_ID = "geant4-sim-kuba"
IMAGE_URL = f"europe-west1-docker.pkg.dev/{PROJECT_ID}/geant-repo/unity-cloud:v1"
BUCKET_NAME = "geant-results-kuba"
UNITY_EXEC_PATH = "/app/game/mysim.x86_64" 

# --- LISTA TWOICH EKSPERYMENTÓW SAC ---
experiments = [
    {
        "name": "sac-electron-10mev-nai",
        "particle": "e-",
        "energy": "10.0",
        "material": "G4_SODIUM_IODIDE",
        "w_pos": "50",
        "w_energy": "15",
        "trainer": "sac",
        "lr": "3.0e-4",
        "batch_size": 256,
    },
    {
        "name": "sac-electron-50mev-pb",
        "particle": "e-",
        "energy": "50.0",
        "material": "G4_Pb",
        "w_pos": "100",
        "w_energy": "30",
        "trainer": "sac",
        "lr": "1.0e-4",
        "batch_size": 512,
    },
    {
        "name": "sac-proton-20mev-water",
        "particle": "proton",
        "energy": "20.0",
        "material": "G4_WATER",
        "w_pos": "30",
        "w_energy": "10",
        "trainer": "sac",
        "lr": "3.0e-4",
        "batch_size": 256,
    },
]

def run_experiment(exp):
    print(f"\n>>> [SAC] Przygotowuję eksperyment: {exp['name']}...")

    # 1. GENERUJEMY CONFIG DLA SAC
    config_content = textwrap.dedent(f"""
        behaviors:
          ElectronBehavior:
            trainer_type: sac
            hyperparameters:
              batch_size: {exp['batch_size']}
              buffer_size: 50000
              learning_rate: {exp['lr']}
              learning_rate_schedule: constant
              init_entcoef: 0.5
              tau: 0.005
              steps_per_update: 1
              save_replay_buffer: false
            network_settings:
              normalize: true
              hidden_units: 128
              num_layers: 2
            reward_signals:
              extrinsic:
                gamma: 0.99
                strength: 1.0
            max_steps: 100000
            time_horizon: 64
            summary_freq: 1000
    """).strip()

    with open(f"config_{exp['name']}.yaml", "w") as f:
        f.write(config_content)

    # 2. GENERUJEMY MANIFEST JOBA
    job_manifest = textwrap.dedent(f"""
        apiVersion: batch/v1
        kind: Job
        metadata:
          name: {exp['name']}
        spec:
          template:
            spec:
              containers:
              - name: geant-ml-container
                image: {IMAGE_URL}
                resources:
                  requests:
                    cpu: "1.5"    # SAC i Geant4 potrzebują trochę mocy
                    memory: "4Gi"
                env:
                - name: PARTICLE_NAME
                  value: "{exp['particle']}"
                - name: PARTICLE_ENERGY
                  value: "{exp['energy']}"
                - name: DETECTOR_MATERIAL
                  value: "{exp['material']}"
                - name: W_POS
                  value: "{exp['w_pos']}"
                - name: W_ENERGY
                  value: "{exp['w_energy']}"
                - name: GCS_BUCKET
                  value: "{BUCKET_NAME}"
                - name: RUN_ID
                  value: "{exp['name']}"
                volumeMounts:
                - name: config-volume
                  mountPath: /app/config.yaml
                  subPath: config.yaml
                command: ["/app/entrypoint.sh"]
                args: [
                    "mlagents-learn", "/app/config.yaml", 
                    "--run-id={exp['name']}", 
                    "--no-graphics", 
                    "--env={UNITY_EXEC_PATH}", 
                    "--num-envs=1",
                    "--time-scale=30"
                ]
              volumes:
              - name: config-volume
                configMap:
                  name: {exp['name']}-config
              restartPolicy: Never
          backoffLimit: 0
    """).strip()

    job_filename = f"job_{exp['name']}.yaml"
    with open(job_manifest_path := f"job_{exp['name']}.yaml", "w") as f:
        f.write(job_manifest)

    subprocess.run(["kubectl", "delete", "job", exp['name']], stderr=subprocess.DEVNULL)
    subprocess.run(["kubectl", "delete", "configmap", f"{exp['name']}-config"], stderr=subprocess.DEVNULL)

    subprocess.run(["kubectl", "create", "configmap", f"{exp['name']}-config", f"--from-file=config.yaml=config_{exp['name']}.yaml"])
    subprocess.run(["kubectl", "apply", "-f", job_filename])
    
    os.remove(f"config_{exp['name']}.yaml")
    os.remove(job_filename)
    
    print(f"[OK] SAC Experiment {exp['name']} wystartował.")

if __name__ == "__main__":
    for e in experiments:
        run_experiment(e)