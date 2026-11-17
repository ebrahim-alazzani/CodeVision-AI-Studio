using System.Collections.Generic;
using UnityEngine;

namespace GTAViceCityClone.AI
{
    /// <summary>
    /// Waypoint represents a node in the navigation path network with branching support and width variation.
    /// Reconstructed cleanly from Episodes 17, 18, 19, 20.
    /// </summary>
    public class Waypoint : MonoBehaviour
    {
        [Header("Waypoint Connections")]
        public Waypoint previousWaypoint;
        public Waypoint nextWaypoint;

        [Header("Branching Settings")]
        [Range(0f, 1f)] public float branchRatio = 0.5f;
        public List<Waypoint> branches = new List<Waypoint>();

        [Header("Path Width")]
        [Range(0f, 10f)] public float width = 1f;

        /// <summary>
        /// Returns a position along the width line of the waypoint for natural dispersion.
        /// </summary>
        public Vector3 GetPosition()
        {
            Vector3 minBound = transform.position + transform.right * (width / 2f);
            Vector3 maxBound = transform.position - transform.right * (width / 2f);

            return Vector3.Lerp(minBound, maxBound, Random.Range(0f, 1f));
        }

        private void OnDrawGizmos()
        {
            Gizmos.color = Color.blue;
            Gizmos.DrawSphere(transform.position, 0.3f);

            // Draw line across width
            Gizmos.color = Color.yellow;
            Vector3 left = transform.position + transform.right * (width / 2f);
            Vector3 right = transform.position - transform.right * (width / 2f);
            Gizmos.DrawLine(left, right);

            // Draw line to next waypoint
            if (nextWaypoint != null)
            {
                Gizmos.color = Color.green;
                Gizmos.DrawLine(transform.position, nextWaypoint.transform.position);
            }

            // Draw lines to branches
            if (branches != null && branches.Count > 0)
            {
                Gizmos.color = Color.cyan;
                foreach (var branch in branches)
                {
                    if (branch != null)
                    {
                        Gizmos.DrawLine(transform.position, branch.transform.position);
                    }
                }
            }
        }
    }
}
