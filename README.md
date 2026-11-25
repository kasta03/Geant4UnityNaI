# Geant4 + Unity ML-Agents (NaI)

Symulacja transportu elektronu w krysztale jodku sodu i uczenie agenta, który odtwarza jego trajektorię.

Geant4 liczy prawdziwą fizykę i wystawia kolejne kroki cząstki po TCP. Unity ML-Agents trenuje politykę (PPO albo SAC), która z pozycji, kierunku i energii przewiduje następny krok. Ten sam układ da się odpalić lokalnie, w Dockerze albo jako Job na Kubernetesie.

## Jak to jest złożone

1. `Geant4Server` (`src/main_server.cc`) startuje run Geant4 i słucha na porcie `5000`.
2. Klient wysyła dowolny `int`. Serwer robi jeden `BeamOn` i odsyła liczbę kroków oraz rekordy `x, y, z, px, py, pz, energia`.
3. `Geant4NetworkClient` w Unity odbiera trajektorię. `ElectronAgent` dostaje ją jako ground truth i uczy się nagrodą za zgodność kierunku, pozycji i energii.
4. `mlagents-learn` trenuje zachowanie `ElectronBehavior` z `config.yaml`.

Domyślna geometria to światło powietrza 15 cm i fantom 5 cm z `G4_SODIUM_IODIDE`. Krok maksymalny w fantomie to 0.1 cm. Cząstka startuje w `(-5, 0, 0)` cm z kierunkiem `+X`.

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `PARTICLE_NAME` | `e-` | nazwa cząstki Geant4 (`e+`, `gamma`, …) |
| `PARTICLE_ENERGY` | `10.0` | energia w MeV |
| `DETECTOR_MATERIAL` | `G4_SODIUM_IODIDE` | materiał fantomu z NIST |
| `W_POS`, `W_ENERGY` | `10` i `5` | wagi kary za błąd pozycji i energii w agencie |

## Co jest w repozytorium

| Ścieżka | Rola |
|---|---|
| `src/`, `include/`, `CMakeLists.txt` | serwer Geant4 |
| `macros/` | makra wizualizacji i batcha |
| `Simulation/` | projekt Unity 6000.2.7f2, scena `SampleScene`, ML-Agents 2.0.2 |
| `config.yaml`, `config_template.yaml` | hiperparametry PPO |
| `geant.py`, `check_physics.py` | odpytanie serwera i rysunek trajektorii |
| `evaluate.py` | inferencja zapisanego modelu ONNX |
| `deploy.py`, `deploy_ppo.py`, `deploy_sac.py`, `cloud_deploy.py` | puszczenie serii jobów (GKE / obrazy) |
| `k8s-local/` | lokalny Job Kubernetesa |
| `Dockerfile.1.geant`, `Dockerfile.2.python`, `Dockerfile.3` | warstwy obrazu: Geant4 11.3.2, Python, trening |
| `upload_results.py` | wysyłka `results/` do GCS, gdy ustawione jest `GCS_BUCKET` |

Poza gitem zostają `Library`, logi, build Unity, checkpointy (`.onnx`, `.pt`) i katalogi wyników. Unity odtworzy `Library` po otwarciu projektu.

## Wymagania

- Geant4 11.3.x, CMake 3.16+, kompilator C++17
- Unity `6000.2.7f2` z pakietem `com.unity.ml-agents` 2.0.2
- Python 3.9 z `mlagents==0.30.0` (w obrazie Dockera: też `torch==1.13.1`, `onnx==1.14.1`)
- Do pełnego treningu: Docker. Do klastra: `kubectl` i obraz wrzucony do rejestru

## Serwer Geant4

Na Linuxie, po `source /opt/geant4/bin/geant4.sh`:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/Geant4Server
```

Serwer wypisze gotowość i zostanie na `0.0.0.0:5000`. Potem można zebrać trajektorie:

```bash
python geant.py
```

`build.bat` pochodzi ze starszej wersji, która budowała wtyczkę DLL do Unity. Aktualny cel CMake to wykonywalny `Geant4Server`.

## Unity

1. Otwórz katalog `Simulation` w Unity `6000.2.7f2`.
2. Scena agenta to `Assets/Scenes/SampleScene.unity`. W scenie muszą być `ElectronAgent` i `Geant4NetworkClient` (adres `127.0.0.1:5000`).
3. Player do treningu headless buduj jako Linux 64-bit do `Simulation/Builds`. Skrypty i `Dockerfile.3` oczekują pliku `Simulation/Builds/mysim.x86_64`. Ten katalog jest w `.gitignore`.

## Trening

Geant4 musi już nasłuchiwać, a obok niego leci środowisko Unity:

```bash
mlagents-learn config.yaml --env=Simulation/Builds/mysim.x86_64 --run-id=local --no-graphics
```

Obraz treningowy skleja serwer i player. Najpierw zbuduj player Unity, potem warstwy:

```bash
docker build -f Dockerfile.1.geant -t geant-layer-1 .
docker build -f Dockerfile.2.python -t python-layer-2 .
docker build -f Dockerfile.3 -t geant-unity:latest .
```

`Dockerfile.3` w entrypoincie odpala Xvfb, `Geant4Server` i na końcu `upload_results.py`. `Dockerfile.unity` to wcześniejszy wariant, bez serwera Geant4 w tym samym kontenerze.

Lokalny Kubernetes (`k8s-local/`) montuje wyniki z dysku hosta. Ustaw ścieżkę przed startem:

```bash
# PowerShell
$env:HOST_RESULTS_PATH = "C:\ścieżka\do\Geant4UnityNaI\results_k8s"
python k8s-local/run_experiments.py
```

W `k8s-local/local-job.yaml` podmień `hostPath` na ten sam katalog. Obraz w tym manifeście to lokalny tag `k8s:latest` (`imagePullPolicy: Never`).

Skrypty `deploy.py`, `deploy_ppo.py` i `deploy_sac.py` składają Job dla Google Kubernetes Engine i obrazu z Artifact Registry projektu `geant4-sim-kuba`. `cloud_deploy.py` używa obrazu `kasta03/geant-unity`. Przed puszczeniem serii podmień identyfikator projektu, bucket i URL obrazu na swoje.
