using UnityEngine;
using UnityEngine.AI;
using GTAViceCityClone.AI;

namespace GTAViceCityClone.Police
{
    /// <summary>
    /// PoliceWaypointNavigator guides patrolling police officers along waypoint networks using NavMeshAgent.
    /// Reconstructed cleanly from Episodes 44, 47, 48.
    /// </summary>
    public class PoliceWaypointNavigator : MonoBehaviour
    {
        [Header("Patrol Waypoint")]
        public Waypoint currentWaypoint;
        public float reachDistance = 1.5f;

        private NavMeshAgent agent;

        private void Awake()
        {
            agent = GetComponent<NavMeshAgent>();
        }

        private void Start()
        {
            if (currentWaypoint != null && agent != null)
            {
                agent.SetDestination(currentWaypoint.transform.position);
            }
        }

        private void Update()
        {
            if (agent == null || currentWaypoint == null || !agent.isActiveAndEnabled) return;

            if (!agent.pathPending && agent.remainingDistance <= reachDistance)
            {
                // Advance to next waypoint
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

                if (currentWaypoint != null)
                {
                    agent.SetDestination(currentWaypoint.transform.position);
                }
            }
        }
    }
}
