import socket
import struct
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

HOST = '127.0.0.1'
PORT = 5000

def get_geant_data():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        print(f"Połączono z Geant4 na {HOST}:{PORT}")

        client.send(b'\x01')

        count_bytes = client.recv(4)
        count = struct.unpack('<i', count_bytes)[0]
        print(f"Odebrano liczbę kroków: {count}")

        if count == 0:
            print("Brak kroków - coś jest nie tak (cząstka zginęła od razu?)")
            return []

        steps = []
        floats_per_step = 7
        bytes_to_read = count * floats_per_step * 4
        
        raw_data = b''
        while len(raw_data) < bytes_to_read:
            packet = client.recv(bytes_to_read - len(raw_data))
            if not packet: break
            raw_data += packet

        for i in range(count):
            offset = i * floats_per_step * 4
            data = struct.unpack_from('<7f', raw_data, offset)
            steps.append(data)

        client.close()
        return steps

    except Exception as e:
        print(f"Błąd: {e}")
        return []

steps = get_geant_data()

if steps:
    xs = [s[0] for s in steps]
    ys = [s[1] for s in steps]
    zs = [s[2] for s in steps]
    energies = [s[6] for s in steps]

    print("\n--- ANALIZA FIZYKI ---")
    print(f"Start: ({xs[0]:.2f}, {ys[0]:.2f}, {zs[0]:.2f}) cm, Energia: {energies[0]:.2f} MeV")
    print(f"Koniec: ({xs[-1]:.2f}, {ys[-1]:.2f}, {zs[-1]:.2f}) cm, Energia: {energies[-1]:.2f} MeV")
    
    dx = xs[-1] - xs[0]
    dy = ys[-1] - ys[0]
    dz = zs[-1] - zs[0]
    dist = (dx**2 + dy**2 + dz**2)**0.5
    print(f"Całkowite przemieszczenie: {dist:.2f} cm")

    dev_y = max(ys) - min(ys)
    dev_z = max(zs) - min(zs)
    print(f"Rozrzut boczny (Y/Z): {dev_y:.2f} cm / {dev_z:.2f} cm")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(xs, zs, ys, marker='o', markersize=2)
    ax.set_xlabel('X (cm)')
    ax.set_ylabel('Z (cm)')
    ax.set_zlabel('Y (cm)')
    ax.set_title('Trajektoria elektronu 10 MeV w NaI')
    plt.show()

    plt.figure()
    plt.plot(energies)
    plt.title("Utrata energii w funkcji kroków")
    plt.xlabel("Krok")
    plt.ylabel("Energia (MeV)")
    plt.grid(True)
    plt.show()