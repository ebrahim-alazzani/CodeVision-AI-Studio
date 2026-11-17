#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using GTAViceCityClone.AI;

namespace GTAViceCityClone.EditorTools
{
    /// <summary>
    /// Custom Inspector for Waypoint component with branch creation and alignment utilities.
    /// Reconstructed cleanly from Episodes 20, 21.
    /// </summary>
    [CustomEditor(typeof(Waypoint))]
    public class WaypointEditor : Editor
    {
        private Waypoint waypoint => target as Waypoint;

        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();

            EditorGUILayout.Space(10);
            EditorGUILayout.LabelField("Waypoint Quick Actions", EditorStyles.boldLabel);

            if (GUILayout.Button("Create Next Waypoint"))
            {
                CreateNextWaypoint();
            }

            if (GUILayout.Button("Create Previous Waypoint"))
            {
                CreatePreviousWaypoint();
            }

            if (GUILayout.Button("Add Branch Waypoint"))
            {
                CreateBranchWaypoint();
            }
        }

        private void CreateNextWaypoint()
        {
            GameObject newWaypointObject = new GameObject("Waypoint_" + waypoint.transform.GetSiblingIndex() + 1, typeof(Waypoint));
            newWaypointObject.transform.SetParent(waypoint.transform.parent, false);

            Waypoint newWaypoint = newWaypointObject.GetComponent<Waypoint>();
            newWaypointObject.transform.position = waypoint.transform.position + waypoint.transform.forward * 4f;

            newWaypoint.previousWaypoint = waypoint;
            if (waypoint.nextWaypoint != null)
            {
                newWaypoint.nextWaypoint = waypoint.nextWaypoint;
                waypoint.nextWaypoint.previousWaypoint = newWaypoint;
            }
            waypoint.nextWaypoint = newWaypoint;

            Selection.activeGameObject = newWaypointObject;
            Undo.RegisterCreatedObjectUndo(newWaypointObject, "Create Next Waypoint");
        }

        private void CreatePreviousWaypoint()
        {
            GameObject newWaypointObject = new GameObject("Waypoint_Prev", typeof(Waypoint));
            newWaypointObject.transform.SetParent(waypoint.transform.parent, false);

            Waypoint newWaypoint = newWaypointObject.GetComponent<Waypoint>();
            newWaypointObject.transform.position = waypoint.transform.position - waypoint.transform.forward * 4f;

            newWaypoint.nextWaypoint = waypoint;
            if (waypoint.previousWaypoint != null)
            {
                newWaypoint.previousWaypoint = waypoint.previousWaypoint;
                waypoint.previousWaypoint.nextWaypoint = newWaypoint;
            }
            waypoint.previousWaypoint = newWaypoint;

            Selection.activeGameObject = newWaypointObject;
            Undo.RegisterCreatedObjectUndo(newWaypointObject, "Create Previous Waypoint");
        }

        private void CreateBranchWaypoint()
        {
            GameObject newWaypointObject = new GameObject("Waypoint_Branch", typeof(Waypoint));
            newWaypointObject.transform.SetParent(waypoint.transform.parent, false);

            Waypoint newWaypoint = newWaypointObject.GetComponent<Waypoint>();
            newWaypointObject.transform.position = waypoint.transform.position + waypoint.transform.right * 4f;

            newWaypoint.previousWaypoint = waypoint;
            waypoint.branches.Add(newWaypoint);

            Selection.activeGameObject = newWaypointObject;
            Undo.RegisterCreatedObjectUndo(newWaypointObject, "Create Branch Waypoint");
        }
    }
}
#endif
