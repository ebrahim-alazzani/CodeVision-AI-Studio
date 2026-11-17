using UnityEngine;

namespace GTAViceCityClone.AI
{
    /// <summary>
    /// CarNavigatorScript steers AI traffic vehicles along waypoints and performs raycast obstacle avoidance.
    /// Reconstructed cleanly from Episodes 35, 36, 37.
    /// </summary>
    public class CarNavigatorScript : MonoBehaviour
    {
        [Header("Waypoint Navigation")]
        public Waypoint currentWaypoint;
        public float driveSpeed = 10f;
        public float steeringSpeed = 5f;
        public float waypointStopDistance = 3f;

        [Header("Obstacle Detection (Raycast)")]
        public float raycastLength = 6f;
        public Vector3 raycastOffset = new Vector3(0f, 0.5f, 1f);
        public LayerMask obstacleLayers;
        public bool isObstacleAhead = false;

        private void Update()
        {
            if (currentWaypoint == null) return;

            CheckForObstacles();

            if (isObstacleAhead)
            {
                // Brake / stop
                return;
            }

            DriveTowardsWaypoint();
        }

        private void CheckForObstacles()
        {
            Vector3 rayOrigin = transform.position + transform.TransformDirection(raycastOffset);
            RaycastHit hit;

            if (Physics.Raycast(rayOrigin, transform.forward, out hit, raycastLength, obstacleLayers))
            {
                isObstacleAhead = true;
            }
            else
            {
                isObstacleAhead = false;
            }
        }

        private void DriveTowardsWaypoint()
        {
            Vector3 targetPosition = currentWaypoint.transform.position;
            Vector3 directionToTarget = targetPosition - transform.position;
            directionToTarget.y = 0f;

            if (directionToTarget.magnitude < waypointStopDistance)
            {
                // Select next waypoint or branch
                if (currentWaypoint.branches != null && currentWaypoint.branches.Count > 0 && Random.Range(0f, 1f) <= currentWaypoint.branchRatio)
                {
                    int randomIndex = Random.Range(0, currentWaypoint.branches.Count);
                    currentWaypoint = currentWaypoint.branches[randomIndex];
                }
                else if (currentWaypoint.nextWaypoint != null)
                {
                    currentWaypoint = currentWaypoint.nextWaypoint;
                }
                else if (currentWaypoint.previousWaypoint != null)
                {
                    currentWaypoint = currentWaypoint.previousWaypoint;
                }
            }

            // Rotate towards target
            if (directionToTarget != Vector3.zero)
            {
                Quaternion targetRotation = Quaternion.LookRotation(directionToTarget);
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, steeringSpeed * Time.deltaTime);
            }

            // Move forward
            transform.position += transform.forward * driveSpeed * Time.deltaTime;
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = isObstacleAhead ? Color.red : Color.green;
            Vector3 rayOrigin = transform.position + transform.TransformDirection(raycastOffset);
            Gizmos.DrawRay(rayOrigin, transform.forward * raycastLength);
        }
    }
}
