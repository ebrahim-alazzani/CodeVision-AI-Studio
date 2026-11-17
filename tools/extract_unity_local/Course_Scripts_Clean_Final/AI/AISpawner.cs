using UnityEngine;

namespace GTAViceCityClone.AI
{
    /// <summary>
    /// AISpawner instantiates pedestrian AI prefabs across the waypoint network at startup.
    /// Reconstructed cleanly from Episodes 24, 25, 48.
    /// </summary>
    public class AISpawner : MonoBehaviour
    {
        [Header("Prefabs & Count")]
        public GameObject[] aiPrefabs;
        public int countToSpawn = 15;

        private void Start()
        {
            SpawnAll();
        }

        public void SpawnAll()
        {
            if (aiPrefabs == null || aiPrefabs.Length == 0) return;

            Waypoint[] allWaypoints = FindObjectsByType<Waypoint>(FindObjectsSortMode.None);
            if (allWaypoints == null || allWaypoints.Length == 0) return;

            for (int i = 0; i < countToSpawn; i++)
            {
                int randomPrefabIndex = Random.Range(0, aiPrefabs.Length);
                int randomWaypointIndex = Random.Range(0, allWaypoints.Length);

                Waypoint spawnWaypoint = allWaypoints[randomWaypointIndex];
                GameObject spawnedObj = Instantiate(aiPrefabs[randomPrefabIndex], spawnWaypoint.GetPosition(), Quaternion.identity);

                var navigator = spawnedObj.GetComponent<WaypointNavigator>();
                if (navigator != null)
                {
                    navigator.currentWaypoint = spawnWaypoint;
                }
            }
        }
    }
}
