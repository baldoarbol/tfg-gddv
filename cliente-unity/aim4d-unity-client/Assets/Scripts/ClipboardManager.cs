using UnityEngine;

public class ClipboardManager : MonoBehaviour
{
    // Texto que quieres copiar al portapapeles
    public string textToCopy = "TEXTO A COPIAR";

    void Start()
    {
        CopyToClipboard(textToCopy);
    }

    // Método para copiar al portapapeles
    public void CopyToClipboard(string text)
    {
        TextEditor editor = new TextEditor();
        editor.text = text;
        editor.SelectAll();
        editor.Copy();
    }
}
