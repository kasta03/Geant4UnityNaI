import os
import subprocess
import time
import random

# --- KONFIGURACJA ---
IMAGE_NAME = "kasta03/geant-unity:v1"

# Definicja 3 strategii
strategies = {
    "balanced": {"reward": 1.0, "penalty": 0.1,  "steps": 400000},
    "greedy":   {"reward": 5.0, "penalty": 0.01, "steps": 400000},
    "precise":  {"reward": 2.0, "penalty": 1.0,  "steps": 400000}
}

# Ile podów na każdą strategię
REPLICAS_PER_STRATEGY = 5

yaml_template = """
apiVersion: batch/v1
kind: Job
metadata:
  name: g4-{JOB_ID}
spec:
  backoffLimit: 0
  template:
    spec:
      containers:
      - name: trainer
        image: {IMAGE}
        imagePullPolicy: Always # W chmurze zawsze pobieramy najnowszy
        
        resources:
          # GKE Autopilot wymaga zdefiniowania zasobów
          requests:
            cpu: "1000m"  # 1 vCPU
            memory: "2Gi" # 2 GB RAM
            ephemeral-storage: "1Gi"

        env:
        - name: AGENT_MAX_STEPS
          value: "{STEPS}"
        - name: AGENT_REWARD_SUCCESS
          value: "{REWARD}"
        - name: AGENT_PENALTY_MULTIPLIER
          value: "{PENALTY}"
        
        # Hack: Po treningu czekaj w nieskończoność, żebyśmy mogli pobrać pliki
        command: ["/bin/bash", "-c"]
        args:
          - |
            /app/entrypoint.sh mlagents-learn /app/config.yaml --run-id={JOB_ID} --env=/app/game/mysim.x86_64 --no-graphics --seed={SEED} && \
            echo "✅ TRENING ZAKOŃCZONY! Czekam na pobranie plików..." && \
            sleep infinity

      restartPolicy: Never
"""

def deploy_to_cloud():
    print(f"☁️ Rozpoczynam wdrażanie na GKE...")
    
    total_jobs = 0

    for strat_name, params in strategies.items():
        print(f"\n--- Generowanie strategii: {strat_name} ---")
        
        for i in range(1, REPLICAS_PER_STRATEGY + 1):
            # Unikalne ID: np. g4-greedy-3
            job_id = f"{strat_name}-{i}"
            
            # Losowy seed dla ML-Agents, żeby każdy pod uczył się trochę inaczej
            seed = random.randint(1, 10000)

            # Wypełnianie szablonu
            job_yaml = yaml_template.replace("{JOB_ID}", job_id) \
                                    .replace("{IMAGE}", IMAGE_NAME) \
                                    .replace("{REWARD}", str(params['reward'])) \
                                    .replace("{PENALTY}", str(params['penalty'])) \
                                    .replace("{STEPS}", str(params['steps'])) \
                                    .replace("{SEED}", str(seed))

            # Zapisz i uruchom
            filename = f"temp_job_{job_id}.yaml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(job_yaml)

            try:
                # Najpierw usuń stary job o tej samej nazwie (jeśli jest)
                subprocess.run(f"kubectl delete job g4-{job_id} --ignore-not-found=true", shell=True, check=False)
                
                # Wyślij do chmury
                subprocess.run(f"kubectl apply -f {filename}", shell=True, check=True)
                print(f"   🚀 Wysłano: g4-{job_id} (Seed: {seed})")
                total_jobs += 1
            except Exception as e:
                print(f"   ❌ Błąd: {e}")

            os.remove(filename)
            time.sleep(0.5) # Krótka przerwa dla API servera

    print(f"\n✅ Zlecono {total_jobs} zadań do chmury! Sprawdź status: kubectl get pods")

if __name__ == "__main__":
    deploy_to_cloud()