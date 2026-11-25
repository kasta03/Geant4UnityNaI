import os
import subprocess
import time

# --- CONFIG ---
experiments = [
    ("exp-cautious",  0.9,  5.0),  
    ("exp-balanced",  0.1,  10.0), 
    ("exp-aggressive", 0.01, 20.0) 
]

HOST_PATH_RESULTS = os.environ.get(
    "HOST_RESULTS_PATH",
    "/absolute/path/to/Geant4UnityNaI/results_k8s",
)

# --- YAML ---
yaml_template = """
apiVersion: batch/v1
kind: Job
metadata:
  name: geant-{EXP_ID}
spec:
  backoffLimit: 0 # Nie restartuj w nieskończoność jak padnie
  template:
    spec:
      containers:
      - name: trainer
        image: k8s:latest
        imagePullPolicy: Never
        
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi" # Limit pamięci, żeby nie zabić laptopa
            cpu: "1000m"

        env:
        - name: AGENT_MAX_STEPS
          value: "3000" # Krótki trening dla testu
        - name: AGENT_REWARD_SUCCESS
          value: "{REWARD}"
        - name: AGENT_PENALTY_MULTIPLIER
          value: "{PENALTY}"

        volumeMounts:
        - name: results-vol
          mountPath: /app/results
        
        command: ["/app/entrypoint.sh"]
        args:
          - "mlagents-learn"
          - "/app/config.yaml"
          - "--run-id={EXP_ID}" # Unikalne ID, żeby wyniki się nie nadpisały
          - "--env=/app/game/mysim.x86_64"
          - "--no-graphics"

      restartPolicy: Never
      volumes:
      - name: results-vol
        hostPath:
          path: {HOST_PATH}
          type: Directory
"""

def run_grid_search():
    print(f"🚀 Rozpoczynam uruchamianie {len(experiments)} eksperymentów na Kubernetes...")

    for exp_id, penalty, reward in experiments:
        print(f"\n--- Konfigurowanie: {exp_id} ---")
        print(f"    Penalty: {penalty}, Reward: {reward}")

        job_yaml = yaml_template.replace("{EXP_ID}", exp_id) \
                                .replace("{PENALTY}", str(penalty)) \
                                .replace("{REWARD}", str(reward)) \
                                .replace("{HOST_PATH}", HOST_PATH_RESULTS)

        filename = f"temp_{exp_id}.yaml"
        with open(filename, "w") as f:
            f.write(job_yaml)

        try:
            subprocess.run(f"kubectl delete job geant-{exp_id} --ignore-not-found=true", shell=True, check=False)
            
            subprocess.run(f"kubectl apply -f {filename}", shell=True, check=True)
            print(f"✅ Uruchomiono Job: geant-{exp_id}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd podczas uruchamiania {exp_id}: {e}")
        
        os.remove(filename)
        
        time.sleep(1)

    print("\n🎉 Wszystkie zadania zlecone! Sprawdź status komendą: kubectl get pods")

if __name__ == "__main__":
    run_grid_search()