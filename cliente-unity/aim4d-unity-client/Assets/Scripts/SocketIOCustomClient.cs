using System;
using System.IO;
using System.Collections.Generic;
using SocketIOClient;
using SocketIOClient.Newtonsoft.Json;
using UnityEngine;
using UnityEngine.UI;
using Newtonsoft.Json.Linq;
using TMPro;
using System.Globalization;
using Newtonsoft.Json;

public class SocketIOCustomClient: MonoBehaviour
{
    public GameManager gameManager;

    private SocketIOUnity socket;

    public void SendMsg(string msg)
    {
        socket.EmitAsync("message", msg);
        Debug.Log("Sending message: " + msg);
        gameManager.SetWaitingPanel(true);
    }

    void Start()
    {
    }

    public void StartClient(string serverIP, string serverPort)
    {
        string serverUrlLink = "http://" + serverIP + ":" + serverPort;


        var uri = new Uri(serverUrlLink);
        socket = new SocketIOUnity(uri);


        socket.OnConnected += (sender, e) =>
        {
            Debug.Log("socket.OnConnected");
        };


        socket.On("reply", response =>
        {
            Debug.Log("MENSAJE RECIBIDO " + response.ToString());
            gameManager.AddMsg(response.ToString());
        });

        socket.Connect();
    }

    public static float[] ParseFloatsFromString(string input)
    {
        input = input.Trim(new char[] { '[', ']' });

        string[] tokens = input.Split(',');

        float[] numbers = new float[tokens.Length];

        for (int i = 0; i < tokens.Length; i++)
        {
            if (float.TryParse(tokens[i], NumberStyles.Any, CultureInfo.InvariantCulture, out float number))
            {
                numbers[i] = number;
            }
        }

        return numbers;
    }

    public string TrimString(string input)
    {
        // Verificar que la cadena tenga al menos 4 caracteres para evitar errores
        if (input.Length > 4)
        {
            return input.Substring(2, input.Length - 4);
        }
        else
        {
            Debug.LogError("La cadena es demasiado corta para eliminar los dos primeros y dos últimos caracteres.");
            return input;
        }
    }

    void OnDestroy()
    {
        socket.Dispose();
    }
}
