using System;
using System.IO;
using System.Net.Sockets;
using UnityEngine;

public class Geant4NetworkClient : MonoBehaviour
{
    public static Geant4NetworkClient Instance { get; private set; }

    [Header("Network Settings")]
    public string serverAddress = "127.0.0.1";
    public int serverPort = 5000;

    private TcpClient _client;
    private NetworkStream _stream;
    private BinaryReader _reader;
    private BinaryWriter _writer;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        DontDestroyOnLoad(gameObject);

        ConnectToGeant();
    }

    private void OnDestroy()
    {
        CloseConnection();
    }

    private void ConnectToGeant()
    {
        try
        {
            Debug.Log($"[Client] Connecting to Geant4 at {serverAddress}:{serverPort}...");

            _client = new TcpClient();
            _client.Connect(serverAddress, serverPort);

            _stream = _client.GetStream();
            _reader = new BinaryReader(_stream);
            _writer = new BinaryWriter(_stream);

            Debug.Log("<color=green>[Client] Connected to Geant4 Server!</color>");
        }
        catch (Exception ex)
        {
            Debug.LogError("[Client] Connection failed: " + ex.Message + ". Is the C++ app running?");
        }
    }

    private void CloseConnection()
    {
        if (_client != null)
        {
            _client.Close();
            _client = null;
        }
    }

    public int RunSimulationBatch(float[] outData, int maxSteps)
    {
        if (_client == null || !_client.Connected)
        {
            Debug.LogWarning("[Client] Reconnecting...");
            ConnectToGeant();

            if (_client == null || !_client.Connected)
                return 0;
        }

        try
        {
            _writer.Write(1);

            int steps = _reader.ReadInt32();
            if (steps > maxSteps)
                steps = maxSteps;

            if (steps > 0)
            {
                int floatsPerStep = 7;
                int byteCount = steps * floatsPerStep * sizeof(float);

                byte[] raw = _reader.ReadBytes(byteCount);
                Buffer.BlockCopy(raw, 0, outData, 0, raw.Length);

                for (int i = 0; i < outData.Length; i++)
                {
                    if (float.IsNaN(outData[i]) || float.IsInfinity(outData[i]))
                    {
                        outData[i] = 0.0f; 
                    }
                }
            }

            return steps;
        }
        catch (Exception ex)
        {
            Debug.LogError("[Client] Data transfer error: " + ex.Message);
            CloseConnection();
            return 0;
        }
    }
}
