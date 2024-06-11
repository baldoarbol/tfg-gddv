using System.IO;
using System.Text;
using UnityEngine;

public class ObjExporter : MonoBehaviour
{
    public void ExportMeshToOBJ()
    {
        Mesh mesh = null;
        string objectName = gameObject.name;

        MeshFilter meshFilter = GetComponent<MeshFilter>();
        if (meshFilter != null)
        {
            mesh = meshFilter.mesh;
        }
        else
        {
            SkinnedMeshRenderer skinnedMeshRenderer = GetComponent<SkinnedMeshRenderer>();
            if (skinnedMeshRenderer != null)
            {
                mesh = new Mesh();
                skinnedMeshRenderer.BakeMesh(mesh);
                objectName = skinnedMeshRenderer.gameObject.name;
            }
        }

        if (mesh == null)
        {
            Debug.LogError("No mesh found on this GameObject.");
            return;
        }

        StringBuilder sb = new StringBuilder();

        sb.Append("g ").Append(objectName).Append("\n");
        foreach (Vector3 v in mesh.vertices)
        {
            sb.Append(string.Format("v {0} {1} {2}\n", v.x, v.y, v.z));
        }
        sb.Append("\n");

        foreach (Vector3 v in mesh.normals)
        {
            sb.Append(string.Format("vn {0} {1} {2}\n", v.x, v.y, v.z));
        }
        sb.Append("\n");

        foreach (Vector3 v in mesh.uv)
        {
            sb.Append(string.Format("vt {0} {1}\n", v.x, v.y));
        }
        /*
        for (int material = 0; material < mesh.subMeshCount; material++)
        {
            sb.Append("\n");
            int[] triangles = mesh.GetTriangles(material);
            for (int i = 0; i < triangles.Length; i += 3)
            {
                sb.Append(string.Format("f {0}/{0}/{0} {1}/{1}/{1} {2}/{2}/{2}\n",
                    triangles[i] + 1, triangles[i + 1] + 1, triangles[i + 2] + 1));
            }
        }
        */
        SaveToFile(sb.ToString(), objectName);
    }

    void SaveToFile(string objContent, string filename)
    {
        string filePath = Path.Combine(Application.persistentDataPath, filename + ".obj");
        File.WriteAllText(filePath, objContent);
        Debug.Log("File saved to " + filePath);
    }
}
