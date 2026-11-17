#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using GTAViceCityClone.AI;

namespace GTAViceCityClone.EditorTools
{
    /// <summary>
    /// WaypointManagerWindow is an EditorWindow tool for creating and structuring waypoint tracks in the scene view.
    /// Reconstructed cleanly from Episodes 17, 18, 19, 20.
    /// </summary>
    public class WaypointManagerWindow : EditorWindow
    {
        [MenuItem("Waypoint/Waypoint Manager Window")]
        public static void ShowWindow()
        {
            GetWindow<WaypointManagerWindow>("Waypoint Manager");
        }

        public Transform waypointRoot;

        private void OnGUI()
        {
            SerializedObject obj = new SerializedObject(this);

            EditorGUILayout.PropertyField(obj.FindProperty("waypointRoot"));

            if (waypointRoot == null)
            {
                EditorGUILayout.HelpBox("Please assign a Waypoint Root Transform to organize your waypoints.", MessageType.Warning);
            }
            else
            {
                EditorGUILayout.BeginVertical("box");
                DrawButtons();
                EditorGUILayout.EndVertical();
            }

            obj.ApplyModifiedProperties();
        }

        private void DrawButtons()
        {
            if (GUILayout.Button("Create Waypoint", GUILayout.Height(30)))
            {
                CreateWaypoint();
            }

            if (Selection.activeGameObject != null && Selection.activeGameObject.GetComponent<Waypoint>())
            {
                Waypoint selectedWaypoint = Selection.activeGameObject.GetComponent<Waypoint>();

                if (GUILayout.Button("Create Waypoint Before", GUILayout.Height(25)))
                {
                    CreateWaypointBefore(selectedWaypoint);
                }

                if (GUILayout.Button("Create Waypoint After", GUILayout.Height(25)))
                {
                    CreateWaypointAfter(selectedWaypoint);
                }

                if (GUILayout.Button("Create Waypoint Branch", GUILayout.Height(25)))
                {
                    CreateWaypointBranch(selectedWaypoint);
                }
            }
        }

        private void CreateWaypoint()
        {
            GameObject waypointObj = new GameObject("Waypoint_" + waypointRoot.childCount, typeof(Waypoint));
            waypointObj.transform.SetParent(waypointRoot, false);

            Waypoint waypoint = waypointObj.GetComponent<Waypoint>();

            if (waypointRoot.childCount > 1)
            {
                Waypoint prevWaypoint = waypointRoot.GetChild(waypointRoot.childCount - 2).GetComponent<Waypoint>();
                if (prevWaypoint != null)
                {
                    prevWaypoint.nextWaypoint = waypoint;
                    waypoint.previousWaypoint = prevWaypoint;
                    waypointObj.transform.position = prevWaypoint.transform.position + prevWaypoint.transform.forward * 4f;
                }
            }

            Selection.activeGameObject = waypointObj;
            Undo.RegisterCreatedObjectUndo(waypointObj, "Create Waypoint");
        }

        private void CreateWaypointBefore(Waypoint current)
        {
            GameObject waypointObj = new GameObject("Waypoint_Before", typeof(Waypoint));
            waypointObj.transform.SetParent(waypointRoot, false);

            Waypoint newWaypoint = waypointObj.GetComponent<Waypoint>();
            waypointObj.transform.position = current.transform.position - current.transform.forward * 4f;

            newWaypoint.nextWaypoint = current;
            if (current.previousWaypoint != null)
            {
                newWaypoint.previousWaypoint = current.previousWaypoint;
                current.previousWaypoint.nextWaypoint = newWaypoint;
            }
            current.previousWaypoint = newWaypoint;

            Selection.activeGameObject = waypointObj;
            Undo.RegisterCreatedObjectUndo(waypointObj, "Create Waypoint Before");
        }

        private void CreateWaypointAfter(Waypoint current)
        {
            GameObject waypointObj = new GameObject("Waypoint_After", typeof(Waypoint));
            waypointObj.transform.SetParent(waypointRoot, false);

            Waypoint newWaypoint = waypointObj.GetComponent<Waypoint>();
            waypointObj.transform.position = current.transform.position + current.transform.forward * 4f;

            newWaypoint.previousWaypoint = current;
            if (current.nextWaypoint != null)
            {
                newWaypoint.nextWaypoint = current.nextWaypoint;
                current.nextWaypoint.previousWaypoint = newWaypoint;
            }
            current.nextWaypoint = newWaypoint;

            Selection.activeGameObject = waypointObj;
            Undo.RegisterCreatedObjectUndo(waypointObj, "Create Waypoint After");
        }

        private void CreateWaypointBranch(Waypoint current)
        {
            GameObject waypointObj = new GameObject("Waypoint_Branch", typeof(Waypoint));
            waypointObj.transform.SetParent(waypointRoot, false);

            Waypoint newWaypoint = waypointObj.GetComponent<Waypoint>();
            waypointObj.transform.position = current.transform.position + current.transform.right * 4f;

            newWaypoint.previousWaypoint = current;
            current.branches.Add(newWaypoint);

            Selection.activeGameObject = waypointObj;
            Undo.RegisterCreatedObjectUndo(waypointObj, "Create Waypoint Branch");
        }
    }
}
#endif
