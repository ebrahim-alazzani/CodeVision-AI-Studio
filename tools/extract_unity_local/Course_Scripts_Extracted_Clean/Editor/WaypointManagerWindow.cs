using UnityEditor;
using UnityEngine;

public class WaypointManagerWindow : EditorWindow
{
    [MenuItem("Waypoint/Waypoints Editor Tools")]
    public static void ShowWindow()
    {
        GetWindow<WaypointManagerWindow>("Waypoints Editor Tools");
    }

    public Transform waypointOrigin;

    void OnGUI()
    {
        SerializedObject obj = new SerializedObject(this);
        EditorGUILayout.PropertyField(obj.FindProperty("waypointOrigin"));

        if (waypointOrigin == null)
        {
            EditorGUILayout.HelpBox("Please assign a Waypoint Origin Transform.", MessageType.Warning);
        }
        else
        {
            EditorGUILayout.BeginVertical("box");
            CreateButton();
            EditorGUILayout.EndVertical();
        }
        obj.ApplyModifiedProperties();
    }

    void CreateButton()
    {
        if (GUILayout.Button("Create Waypoint"))
        {
            CreateWaypoint();
        }
    }

    void CreateWaypoint()
    {
        int currentCount = waypointOrigin.childCount;
        GameObject waypointObject = new GameObject("Waypoint" + currentCount, typeof(WayPoint));
        waypointObject.transform.SetParent(waypointOrigin, false);

        WayPoint waypoint = waypointObject.GetComponent<WayPoint>();

        if (currentCount > 0)
        {
            WayPoint prevWaypoint = waypointOrigin.GetChild(currentCount - 1).GetComponent<WayPoint>();
            if (prevWaypoint != null)
            {
                waypoint.previousWaypoint = prevWaypoint;
                prevWaypoint.nextWaypoint = waypoint;

                waypoint.transform.position = prevWaypoint.transform.position;
                waypoint.transform.forward = prevWaypoint.transform.forward;
            }
        }

        Selection.activeGameObject = waypoint.gameObject;
    }
}
