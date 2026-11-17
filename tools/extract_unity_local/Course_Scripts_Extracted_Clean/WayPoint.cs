using System.Collections.Generic;
using UnityEngine;

public class WayPoint : MonoBehaviour
{
    [Header("Waypoint Connections")]
    public WayPoint nextWaypoint;
    public WayPoint previousWaypoint;
    public List<WayPoint> branches = new List<WayPoint>();

    [Range(0f, 15f)]
    public float waypointWidth = 4f;

    [Range(0f, 1f)]
    public float branchRatio = 0.5f;

    public Vector3 GetPosition()
    {
        Vector3 minBound = transform.position + (transform.right * waypointWidth) / 2f;
        Vector3 maxBound = transform.position - (transform.right * waypointWidth) / 2f;
        return Vector3.Lerp(minBound, maxBound, Random.Range(0f, 1f));
    }

    public WayPoint GetNextWaypoint()
    {
        if (branches != null && branches.Count > 0 && Random.Range(0f, 1f) <= branchRatio)
        {
            int randomIndex = Random.Range(0, branches.Count);
            if (branches[randomIndex] != null) return branches[randomIndex];
        }

        return nextWaypoint;
    }

    private void OnDrawGizmos()
    {
        Gizmos.color = Color.cyan;
        Gizmos.DrawWireSphere(transform.position, 0.5f);

        Vector3 minBound = transform.position + (transform.right * waypointWidth) / 2f;
        Vector3 maxBound = transform.position - (transform.right * waypointWidth) / 2f;
        Gizmos.color = Color.yellow;
        Gizmos.DrawLine(minBound, maxBound);

        if (nextWaypoint != null)
        {
            Gizmos.color = Color.green;
            Gizmos.DrawLine(transform.position, nextWaypoint.transform.position);
        }

        if (branches != null)
        {
            foreach (var branch in branches)
            {
                if (branch != null)
                {
                    Gizmos.color = Color.blue;
                    Gizmos.DrawLine(transform.position, branch.transform.position);
                }
            }
        }
    }
}
