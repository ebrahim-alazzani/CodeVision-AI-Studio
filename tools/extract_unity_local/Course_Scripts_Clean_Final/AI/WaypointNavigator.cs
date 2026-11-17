using UnityEngine;

namespace GTAViceCityClone.AI
{
    /// <summary>
    /// WaypointNavigator steers an AI agent along a chain of waypoints with branch decision making.
    /// Reconstructed cleanly from Episodes 22, 35, 36, 37, 39, 44, 48.
    /// </summary>
    public class WaypointNavigator : MonoBehaviour
    {
        [Header("References")]
        private CharacterNavigatorScript character;

        [Header("Navigation State")]
        public Waypoint currentWaypoint;
        public int direction = 0; // 0 = forward, 1 = reverse
        public float stopDistance = 1.2f;

        private void Awake()
        {
            character = GetComponent<CharacterNavigatorScript>();
        }

        private void Start()
        {
            if (currentWaypoint != null && character != null)
            {
                character.SetDestination(currentWaypoint.GetPosition());
            }
        }

        private void Update()
        {
            if (character == null || currentWaypoint == null) return;

            // Check if agent reached the current waypoint target
            if (character.reachedDestination || Vector3.Distance(transform.position, currentWaypoint.transform.position) < stopDistance)
            {
                bool shouldBranch = false;

                if (currentWaypoint.branches != null && currentWaypoint.branches.Count > 0)
                {
                    shouldBranch = Random.Range(0f, 1f) <= currentWaypoint.branchRatio;
                }

                if (shouldBranch)
                {
                    int randomIndex = Random.Range(0, currentWaypoint.branches.Count);
                    currentWaypoint = currentWaypoint.branches[randomIndex];
                }
                else
                {
                    if (direction == 0)
                    {
                        if (currentWaypoint.nextWaypoint != null)
                        {
                            currentWaypoint = currentWaypoint.nextWaypoint;
                        }
                        else
                        {
                            direction = 1;
                            currentWaypoint = currentWaypoint.previousWaypoint;
                        }
                    }
                    else if (direction == 1)
                    {
                        if (currentWaypoint.previousWaypoint != null)
                        {
                            currentWaypoint = currentWaypoint.previousWaypoint;
                        }
                        else
                        {
                            direction = 0;
                            currentWaypoint = currentWaypoint.nextWaypoint;
                        }
                    }
                }

                if (currentWaypoint != null)
                {
                    character.SetDestination(currentWaypoint.GetPosition());
                }
            }
        }
    }
}
