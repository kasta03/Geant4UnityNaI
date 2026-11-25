import numpy as np
import onnxruntime as ort
import matplotlib.pyplot as plt
import os
from pathlib import Path

# --- KONFIGURACJA GŁÓWNA ---
BASE_RESULTS_DIR = "wyniki_finalne"  # Folder z wynikami z klastra
OUTPUT_DIR = "trajektorie_wizualizacja_XY"
NUM_EPISODES = 3000       
MAX_STEPS = 300           

# Parametry normalizacji
NORM_POS = 15.0
NORM_ENERGY = 10.0
MAX_STEP_SIZE = 0.5

# Parametry startowe
START_POS = np.array([-5.0, 0.0, 0.0], dtype=np.float32)
START_MOM = np.array([1.0, 0.0, 0.0], dtype=np.float32)
START_ENERGY = 10.0

def run_inference(session, episode_idx=0):
    pos = START_POS.copy()
    mom = START_MOM.copy()
    energy = START_ENERGY
    trajectory = [pos.copy()]
    
    input_name = session.get_inputs()[0].name
    
    for _ in range(MAX_STEPS):
        if energy <= 0: break
            
        obs = np.array([
            pos[0] / NORM_POS, pos[1] / NORM_POS, pos[2] / NORM_POS,
            mom[0], mom[1], mom[2],
            energy / NORM_ENERGY
        ], dtype=np.float32).reshape(1, -1)
        
        outputs = session.run(None, {input_name: obs})
        
        actions_vector = None
        for out in outputs:
            if len(out.shape) == 2:
                if out.shape[1] == 7:
                    actions_vector = out[0]
                    break
                elif out.shape[1] == 3: 
                    if actions_vector is None: actions_vector = out[0]
                    else: actions_vector = np.concatenate((actions_vector, out[0]))

        if actions_vector is None: raise RuntimeError("Błąd wyjścia modelu")
        if len(actions_vector) == 6: actions_vector = np.append(actions_vector, [0.0])

        # Fizyka
        pos += actions_vector[0:3] * MAX_STEP_SIZE
        mom = (mom + actions_vector[3:6] * 0.1)
        if np.linalg.norm(mom) > 0: mom /= np.linalg.norm(mom)
        energy += actions_vector[6] * 5.0
        
        trajectory.append(pos.copy())
        
    return np.array(trajectory)

def plot_and_save_xy(trajectories, model_name, save_path):
    # Tworzymy pojedynczy wykres
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.suptitle(f"Model: {model_name}\nTrajectories: {len(trajectories)} (XY Plane)", fontsize=14)
    
    ax.set_facecolor('#f8f9fa')
    ax.set_xlabel('X [cm]')
    ax.set_ylabel('Y [cm]')
    ax.grid(True, alpha=0.3)
    
    # Rysowanie granicy Phantoma (jeśli mieści się w zakresie)
    phantom_half_size = 5.0
    rect = plt.Rectangle((-phantom_half_size, -phantom_half_size), 10.0, 10.0, 
                         linewidth=2, edgecolor='red', facecolor='none', linestyle='--', alpha=0.5, label='Phantom')
    ax.add_patch(rect)

    # Rysowanie trajektorii
    for traj in trajectories[::5]: # Co 5-ta dla przejrzystości
        ax.plot(traj[:, 0], traj[:, 1], color='blue', alpha=0.1, linewidth=0.7)

    # Ustawienia zakresów zgodnie z prośbą
    ax.set_xlim(-6, -2)
    ax.set_ylim(-4, 4) # Zakres od -4 do 4 dla osi Y

    plt.legend(loc='upper right')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    model_files = list(Path(BASE_RESULTS_DIR).rglob("*.onnx"))
    print(f"Znaleziono {len(model_files)} modeli do przetestowania.")

    for model_path in model_files:
        experiment_name = model_path.parent.parent.name
        checkpoint_name = model_path.stem
        full_id = f"{experiment_name}_{checkpoint_name}"
        
        print(f"\n--- Przetwarzanie: {full_id} ---")
        
        try:
            sess = ort.InferenceSession(str(model_path))
            trajectories = [run_inference(sess, i) for i in range(NUM_EPISODES)]
            
            save_file = os.path.join(OUTPUT_DIR, f"plot_XY_{full_id}.png")
            plot_and_save_xy(trajectories, full_id, save_file)
            print(f"[OK] Wykres XY zapisany: {save_file}")
            
        except Exception as e:
            print(f"[BŁĄD] Nie udało się przetworzyć {model_path}: {e}")

    print(f"\n[KONIEC] Wykresy XY znajdziesz w folderze: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()