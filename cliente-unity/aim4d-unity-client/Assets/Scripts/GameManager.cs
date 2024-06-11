using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;
using System.Globalization;
using UnityEngine.EventSystems;
using System;
using System.IO;
using Newtonsoft.Json;
using UnityEditor;

public class GameManager : MonoBehaviour
{
    public GameObject inputWindow, serverSettingsWindow;

    public string defaultServerIp;
    public string defaultServerPort;

    public TMP_InputField serverIpInput;
    public TMP_InputField serverPortInput;

    private string smpllmHeader = "smpllm";
    private string smplitexHeader = "smplitex";

    private string current_msg;
    public Texture2D base_texture_asset;

    public TextMeshProUGUI avatarShapeText, avatarTextureText;
    public GameObject generatedBetasGrid;
    public SMPLX smplxBody;
    public SocketIOCustomClient socketIOClient;
    public GameObject waitingPanel;

    public Text[] generatedBetasTextArray = new Text[10];

    public bool refresh = false;

    public float[] betas = new float[10];

    public string imageBase64 = null;

    void Start()
    {
        for (int i = 0; i < generatedBetasGrid.transform.childCount; i++)
        {
            Transform child = generatedBetasGrid.transform.GetChild(i).GetChild(0);

            Text textComponent = child.GetComponent<Text>();

            if (textComponent != null)
            {
                generatedBetasTextArray[i] = textComponent;
            }
            else
            {
                Debug.LogError("No se encontró un componente Text en el hijo: " + child.name);
            }
        }

        inputWindow.SetActive(false);
        serverSettingsWindow.SetActive(true);
        serverIpInput.text = defaultServerIp;
        serverPortInput.text = defaultServerPort;
    }

    void Update()
    {
        if (refresh)
        {
            Debug.Log(current_msg);

            List<ResponseList> responseList = JsonConvert.DeserializeObject<List<ResponseList>>(current_msg);

            Debug.Log(responseList);
            
            foreach (Response response in responseList[0].Responses)
            {
                if (response.Output == "INVALID_RESPONSE")
                {
                    Debug.Log("INVALID RESPONSE RECEIVED FROM SERVER");
                }
                else
                {
                    if (response.Header == smpllmHeader)
                    {
                        betas = ParseFloatsFromString(response.Output);
                    }
                    else if (response.Header == smplitexHeader)
                    {
                        imageBase64 = response.Output;
                    }
                }  
            }

            for (int i = 0; i < betas.Length; i++)
            {
                smplxBody.betas[i] = betas[i];
                generatedBetasTextArray[i].text = betas[i].ToString();
            }

            smplxBody.SetBetaShapes();
            smplxBody.SnapToGroundPlane();

            if (imageBase64 != null)
            {
                SaveImage(imageBase64);
            }

            SetWaitingPanel(false);

            refresh = false;
        }
        TurnModel();
    }

    public float rotationSpeed = 30.0f;
    private bool dragging = false;
    private float startPoint;
    public GameObject bodyModel;

    private void TurnModel()
    {
        if (Input.GetMouseButtonDown(0) && !EventSystem.current.IsPointerOverGameObject())
        {
            startPoint = Input.mousePosition.x;
            dragging = true;
        }

        if (Input.GetMouseButtonUp(0))
        {
            dragging = false;
        }

        if (dragging)
        {
            float delta = Input.mousePosition.x - startPoint;
            startPoint = Input.mousePosition.x;

            bodyModel.transform.Rotate(Vector3.up, -delta * rotationSpeed * Time.deltaTime);
        }
    }

    public void ConnectButtonClicked()
    {
        socketIOClient.StartClient(serverIpInput.text, serverPortInput.text);
        inputWindow.SetActive(true);
        serverSettingsWindow.SetActive(false);
    }

    public void SendShapeDescriptionButton()
    {
        Message msg = new Message();

        msg.AddRequest(smpllmHeader, avatarShapeText.text);

        string msg_json = msg.ToJson();
        socketIOClient.SendMsg(msg_json);
    }

    public void SendTextureDescriptionButton()
    {
        Message msg = new Message();

        msg.AddRequest(smplitexHeader, avatarTextureText.text);

        string msg_json = msg.ToJson();
        socketIOClient.SendMsg(msg_json);
    }

    public void SendBothDescriptionsButton()
    {
        Message msg = new Message();

        msg.AddRequest(smpllmHeader, avatarShapeText.text);
        msg.AddRequest(smplitexHeader, avatarTextureText.text);

        string msg_json = msg.ToJson();
        socketIOClient.SendMsg(msg_json);
    }

    public void UpdateBetas(float[] newBetas)
    {
        betas = newBetas;
        refresh = true;
    }

    public void CopyBetasButton()
    {
        string betasString = "[" + string.Join(", ", betas) + "]";
        TextEditor editor = new TextEditor();
        editor.text = betasString;
        editor.SelectAll();
        editor.Copy();
    }

    public void AddMsg(string json_msg)
    {
        current_msg = json_msg;
        refresh = true;
    }

    public void SaveImage(string base64Image)
    {
        byte[] imageBytes = Convert.FromBase64String(base64Image);

        string path = Path.Combine(Application.dataPath, "tex.png");

        File.WriteAllBytes(path, imageBytes);

        Debug.Log("Imagen guardada en: " + path);

#if UNITY_EDITOR
        UnityEditor.AssetDatabase.Refresh();
#endif
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

    public void SetWaitingPanel(bool set)
    {
        waitingPanel.SetActive(set);
    }

    private void OnDestroy()
    {
        ResetTexture();
    }

    private void ResetTexture()
    {
        string path = AssetDatabase.GetAssetPath(base_texture_asset);
        byte[] imageData = File.ReadAllBytes(path);

        string destinationPath = Path.Combine(Application.dataPath, "tex.png");
        File.WriteAllBytes(destinationPath, imageData);
        AssetDatabase.Refresh();
    }
}

public class Request
{
    public string Header { get; set; }
    public string Prompt { get; set; }
}

public class Message
{
    public List<Request> Requests { get; set; }

    public Message()
    {
        Requests = new List<Request>();
    }

    public void AddRequest(string header, string prompt)
    {
        Request newRequest = new Request { Header = header, Prompt = prompt};
        Requests.Add(newRequest);
    }

    public string ToJson()
    {
        return JsonConvert.SerializeObject(this);
    }
}

[System.Serializable]
public class Response
{
    public string Header;
    public string Output;
}

[System.Serializable]
public class ResponseList
{
    public List<Response> Responses;
}
