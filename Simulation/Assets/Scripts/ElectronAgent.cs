using UnityEngine;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;
using System;

public class ElectronAgent : Agent
{
    private const float NORM_POS = 15.0f;
    private const float NORM_ENERGY = 10.0f;

    [Header("Simulation Settings")]
    public int MaxSteps = 2000; 

    [Header("Inference Settings")]
    public bool IsInferenceMode = false;
    public float DefaultInferenceStepSize = 0.1f; 

    private float[] _groundTruthBuffer;
    private int _trajectoryLength = 0;
    private int _currentStep = 0;

    private Vector3 _agentPosition;
    private Vector3 _agentMomentum; 
    private float _agentEnergy;

    private float W_POS = 10.0f;
    private float W_ENERGY = 5.0f;

    public override void Initialize()
    {
        _groundTruthBuffer = new float[MaxSteps * 7];
        LoadSettingsFromEnv();
    }

    private void LoadSettingsFromEnv()
    {
        if (float.TryParse(Environment.GetEnvironmentVariable("W_POS"), out float wp)) W_POS = wp;
        if (float.TryParse(Environment.GetEnvironmentVariable("W_ENERGY"), out float we)) W_ENERGY = we;
    }

    public override void OnEpisodeBegin()
    {
        _currentStep = 0;
        if (!IsInferenceMode)
        {
            if (Geant4NetworkClient.Instance == null) return;
            _trajectoryLength = Geant4NetworkClient.Instance.RunSimulationBatch(_groundTruthBuffer, MaxSteps);
            if (_trajectoryLength < 2) { EndEpisode(); return; }
            SetAgentStateFromBuffer(0);
        }
        else
        {
            _agentPosition = new Vector3(-5.0f, 0.0f, 0.0f);
            _agentMomentum = Vector3.right;
            _agentEnergy = 10.0f;
            _trajectoryLength = MaxSteps;
        }
    }

    public override void CollectObservations(VectorSensor sensor)
    {
        bool useGroundTruth = !IsInferenceMode && UnityEngine.Random.value < 0.05f;

        Vector3 pos, mom;
        float energy;

        if (useGroundTruth && _currentStep < _trajectoryLength)
        {
            int idx = _currentStep * 7;
            pos = new Vector3(_groundTruthBuffer[idx+0], _groundTruthBuffer[idx+1], _groundTruthBuffer[idx+2]);
            // Zawsze normalizujemy pęd z G4 przed podaniem do sieci!
            Vector3 rawMomG4 = new Vector3(_groundTruthBuffer[idx+3], _groundTruthBuffer[idx+4], _groundTruthBuffer[idx+5]);
            mom = rawMomG4.sqrMagnitude > 0.001f ? rawMomG4.normalized : Vector3.right;
            energy = _groundTruthBuffer[idx+6];
        }
        else
        {
            pos = _agentPosition;
            mom = _agentMomentum;
            energy = _agentEnergy;
        }

        // Zabezpieczenie przed NaN w obserwacjach
        if (float.IsNaN(pos.x)) pos = Vector3.zero;
        if (float.IsNaN(mom.x)) mom = Vector3.right;

        sensor.AddObservation(pos / NORM_POS);
        sensor.AddObservation(mom); 
        sensor.AddObservation(Mathf.Clamp(energy / NORM_ENERGY, 0f, 2f));
    }

    public override void OnActionReceived(ActionBuffers actions)
    {
        if (_currentStep >= _trajectoryLength - 1) { EndEpisode(); return; }

        int nextIdx = (_currentStep + 1) * 7;
        Vector3 truePos = new Vector3(_groundTruthBuffer[nextIdx+0], _groundTruthBuffer[nextIdx+1], _groundTruthBuffer[nextIdx+2]);
        float trueEnergy = _groundTruthBuffer[nextIdx+6];

        float stepDistG4 = Vector3.Distance(_agentPosition, truePos);
        if (stepDistG4 <= 0) stepDistG4 = 0.001f;

        var contActions = actions.ContinuousActions;
        
        // Aktualizacja pędu z zabezpieczeniem
        Vector3 deltaMom = new Vector3(contActions[0], contActions[1], contActions[2]) * 0.15f;
        Vector3 combinedMom = _agentMomentum + deltaMom;
        _agentMomentum = combinedMom.sqrMagnitude > 0.001f ? combinedMom.normalized : _agentMomentum;

        // Aktualizacja energii
        float deltaEnergy = contActions[3] * 0.2f; 
        float predictedEnergy = _agentEnergy + deltaEnergy;

        // Nowa pozycja oparta na dystansie z G4
        Vector3 predictedPos = _agentPosition + (_agentMomentum * stepDistG4);

        if (!IsInferenceMode)
        {
            Vector3 dirToTruePos = (truePos - _agentPosition).normalized;
            float alignment = Vector3.Dot(_agentMomentum, dirToTruePos); 
            
            float posError = Vector3.Distance(predictedPos, truePos);
            float energyError = Mathf.Abs(predictedEnergy - trueEnergy);

            // Nowa, stabilniejsza funkcja nagrody
            float reward = (alignment * 1.0f) - (posError * W_POS) - (energyError * W_ENERGY);
            SetReward(Mathf.Clamp(reward, -1.0f, 1.0f));
        }

        _agentPosition = predictedPos;
        _agentEnergy = predictedEnergy;
        _currentStep++;

        if (_agentEnergy <= 0 || float.IsNaN(_agentPosition.x)) EndEpisode();
    }

    private void SetAgentStateFromBuffer(int stepIndex)
    {
        int idx = stepIndex * 7;
        _agentPosition = new Vector3(_groundTruthBuffer[idx+0], _groundTruthBuffer[idx+1], _groundTruthBuffer[idx+2]);
        Vector3 rawMom = new Vector3(_groundTruthBuffer[idx+3], _groundTruthBuffer[idx+4], _groundTruthBuffer[idx+5]);
        _agentMomentum = rawMom.sqrMagnitude > 0.001f ? rawMom.normalized : Vector3.right;
        _agentEnergy = _groundTruthBuffer[idx+6];
    }
}