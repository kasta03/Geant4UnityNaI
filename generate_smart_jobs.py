import os
import random
import argparse

STRATEGIES = {
    "SNIPER": { "w_pos": (100.0, 200.0), "w_en": (1.0, 5.0) },
    "ECO":    { "w_pos": (10.0, 20.0),   "w_en": (50.0, 100.0) },
    "BALANCED": { "w_pos": (40.0, 60.0), "w_en": (10.0, 20.0) }
}

BRAINS = {
    "SMALL":  { "hidden": 128, "layers": 2, "mem": 0 },
    "LARGE":  { "hidden": 512, "layers": 3, "mem": 0 },
}

JOB_TEMPLATE = """apiVersion: batch/v1
kind: Job
metadata:
  name: train-{id}
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: trainer
        image: {image}
        imagePullPolicy: Always
        resources:
          requests:
            cpu: "1000m"
            memory: "2Gi"
        env:
        - name: W_POS
          value: "{w_pos:.2f}"
        - name: W_ENERGY
          value: "{w_en:.2f}"
        - name: HIDDEN_UNITS
          value: "{hidden}"
        - name: NUM_LAYERS
          value: "{layers}"
        - name: MEMORY_SIZE
          value: "{mem}"
        - name: LEARNING_RATE
          value: "{lr:.5f}"
        - name: RUN_ID
          value: "{run_id}"

        command: ["/bin/bash", "-c"]
        args:
        - >-
          chmod +x /app/entrypoint.sh && 
          /app/entrypoint.sh python3 /app/run_dynamic_training.py &&
          echo "TRENING ZAKOŃCZONY. CZEKAM NA KOPIOWANIE..." &&
          sleep infinity
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-jobs", type=int, default=1)
    parser.add_argument("--image", type=str, default="kasta03/geant-unity:latest")
    args = parser.parse_args()

    os.makedirs("k8s_jobs", exist_ok=True)
    for f in os.listdir("k8s_jobs"):
        os.remove(os.path.join("k8s_jobs", f))

    print(f"Generowanie {args.num_jobs} jobów BEZ DYSKU...")

    for i in range(args.num_jobs):
        strat_name = random.choice(list(STRATEGIES.keys()))
        strat = STRATEGIES[strat_name]
        val_w_pos = random.uniform(*strat["w_pos"])
        val_w_en = random.uniform(*strat["w_en"])

        brain_name = random.choice(list(BRAINS.keys()))
        brain = BRAINS[brain_name]
        val_lr = 0.0003

        run_id = f"{strat_name}_{brain_name}_{i}"

        yaml_content = JOB_TEMPLATE.format(
            id=i,
            image=args.image,
            w_pos=val_w_pos,
            w_en=val_w_en,
            hidden=brain["hidden"],
            layers=brain["layers"],
            mem=brain["mem"],
            lr=val_lr,
            run_id=run_id
        )

        with open(f"k8s_jobs/job_{i}.yaml", "w") as f:
            f.write(yaml_content)

    print(f"✅ Gotowe. Uruchom: kubectl apply -f k8s_jobs/")

if __name__ == "__main__":
    main()