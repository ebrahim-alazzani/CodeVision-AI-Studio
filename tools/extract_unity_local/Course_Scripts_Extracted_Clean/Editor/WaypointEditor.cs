using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
public class WaypointEditor
{
    [DrawGizmo(GizmoType.NonSelected | GizmoType.Selected | GizmoType.Pickable)]
    public static void OnDrawGizmos(WayPoint waypoint, GizmoType gizmoType)
    {
        if (waypoint == null)
            return;

        if ((gizmoType & GizmoType.Selected) != 0)
        {
            Gizmos.color = Color.cyan;
        }
        else
        {
            Gizmos.color = Color.blue;
        }

        Gizmos.DrawSphere(waypoint.transform.position, 0.35f);

        Vector3 left = waypoint.transform.position + waypoint.transform.right * waypoint.waypointWidth / 2f;
        Vector3 right = waypoint.transform.position - waypoint.transform.right * waypoint.waypointWidth / 2f;

        Gizmos.color = Color.white;
        Gizmos.DrawLine(left, right);

        if (waypoint.previousWaypoint != null)
        {
            Gizmos.color = Color.red;

            Vector3 offset = waypoint.transform.right * waypoint.waypointWidth / 2f;
            Vector3 offsetTo = waypoint.previousWaypoint.transform.right * waypoint.previousWaypoint.waypointWidth / 2f;

            Gizmos.DrawLine(
                waypoint.transform.position + offset,
                waypoint.previousWaypoint.transform.position + offsetTo
            );
        }

        if (waypoint.nextWaypoint != null)
        {
            Gizmos.color = Color.green;

            Vector3 offset = waypoint.transform.right * -waypoint.waypointWidth / 2f;
            Vector3 offsetTo = waypoint.nextWaypoint.transform.right * -waypoint.nextWaypoint.waypointWidth / 2f;

            Gizmos.DrawLine(
                waypoint.transform.position + offset,
                waypoint.nextWaypoint.transform.position + offsetTo
            );
        }
    }
}
