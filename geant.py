import socket
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# Ustawienie backendu na 'Agg' jest dobrą praktyką przy generowaniu
# plików graficznych na serwerach lub w skryptach bez interfejsu graficznego.
# Zapobiega to próbie otwierania okienek z wykresami podczas wykonywania skryptu.
matplotlib.use('Agg')

# --- KONFIGURACJA ---
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
NUM_EPISODES = 1000  # Ile cząstek wystrzelić w Geant4

def get_geant4_trajectory(sock):
    """
    Prosi serwer Geant4 o symulację jednej cząstki i odbiera jej kroki.
    """
    # 1. Wysyłamy sygnał do serwera (dowolny int), aby wywołać BeamOn(1)
    sock.sendall(struct.pack("i", 1))
    
    # 2. Odbieramy liczbę kroków (int - 4 bajty)
    data = sock.recv(4)
    if not data: return None
    num_steps = struct.unpack("i", data)[0]
    
    trajectory = []
    
    if num_steps > 0:
        # 3. Odbieramy dane kroków (każdy krok to 7 floatów: x, y, z, px, py, pz, e)
        # 7 floatów * 4 bajty = 28 bajtów na krok
        bytes_to_read = num_steps * 28
        buffer = b""
        while len(buffer) < bytes_to_read:
            chunk = sock.recv(bytes_to_read - len(buffer))
            if not chunk: break
            buffer += chunk
            
        # Rozpakowanie bufora
        for i in range(num_steps):
            offset = i * 28
            step_values = struct.unpack("7f", buffer[offset:offset+28])
            # Interesują nas tylko x, y, z (pozycja)
            trajectory.append([step_values[0], step_values[1], step_values[2]])
            
    return np.array(trajectory)

def setup_plot_axes(ax, title, xlabel, ylabel):
    """Pomocnicza funkcja do ustawiania stylu wykresu (fantom, siatka, limity)."""
    phantom_half_size = 5.0
    ax.set_facecolor('#f8f9fa')
    # Rysowanie fantomu
    rect = plt.Rectangle((-phantom_half_size, -phantom_half_size), 10.0, 10.0, 
                         linewidth=2, edgecolor='red', facecolor='none', linestyle='--', label='Phantom (NaI)')
    ax.add_patch(rect)
    
    ax.grid(True, alpha=0.3)
    # Ustawienie sztywnych limitów osi, żeby wszystkie wykresy wyglądały tak samo
    ax.set_xlim(-6, -2) # Zakładam, że to są pożądane limity X na podstawie poprzedniego kodu
    ax.set_ylim(-2, 2)  # Zakładam, że to są pożądane limity Y/Z
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

def main():
    print(f"--- Łączenie z serwerem Geant4 ({SERVER_IP}:{SERVER_PORT}) ---")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))
        print("Połączono pomyślnie.")
    except Exception as e:
        print(f"[BŁĄD] Nie można połączyć się z serwerem Geant4: {e}")
        return

    all_trajectories = []
    
    print(f"Pobieranie {NUM_EPISODES} trajektorii z Geant4...")
    for i in range(NUM_EPISODES):
        traj = get_geant4_trajectory(sock)
        if traj is not None and len(traj) > 0:
            all_trajectories.append(traj)
        if (i+1) % 20 == 0:
            print(f"  Postęp: {i+1}/{NUM_EPISODES}")

    sock.close()

    if not all_trajectories:
        print("Brak danych do wyrysowania.")
        return

    # --- RYSOWANIE WYKRESÓW ODDZIELNIE ---
    print("\nGenerowanie oddzielnych obrazów...")

    # === OBRAZ 1: Płaszczyzna XY ===
    print("Rysowanie płaszczyzny XY...")
    fig_xy = plt.figure(figsize=(8, 7)) # Tworzymy nową, pojedynczą figurę
    ax_xy = plt.gca()
    
    # Konfiguracja osi
    setup_plot_axes(ax_xy, 
                    title=f'Geant4: XY Plane\n({len(all_trajectories)} events)',
                    xlabel='X [cm]', 
                    ylabel='Y [cm]')

    # Rysowanie trajektorii (niebieskie)
    for traj in all_trajectories:
        ax_xy.plot(traj[:, 0], traj[:, 1], color='blue', alpha=0.15, linewidth=0.6)

    output_xy = 'geant4_physics_result_XY.png'
    plt.savefig(output_xy, dpi=300, bbox_inches='tight')
    print(f"[SUKCES] Zapisano: {output_xy}")
    plt.close(fig_xy) # Zamykamy figurę, żeby zwolnić pamięć


    # === OBRAZ 2: Płaszczyzna XZ ===
    print("\nRysowanie płaszczyzny XZ...")
    fig_xz = plt.figure(figsize=(8, 7)) # Tworzymy kolejną nową figurę
    ax_xz = plt.gca()
    
    # Konfiguracja osi
    setup_plot_axes(ax_xz, 
                    title='Geant4: XZ Plane',
                    xlabel='X [cm]', 
                    ylabel='Z [cm]')

    # Rysowanie trajektorii (zielone)
    for traj in all_trajectories:
        ax_xz.plot(traj[:, 0], traj[:, 2], color='green', alpha=0.15, linewidth=0.6)

    output_xz = 'geant4_physics_result_XZ.png'
    plt.savefig(output_xz, dpi=300, bbox_inches='tight')
    print(f"[SUKCES] Zapisano: {output_xz}")
    plt.close(fig_xz) # Zamykamy drugą figurę

    print("\nZakończono generowanie obu obrazów.")

if __name__ == "__main__":
    main()