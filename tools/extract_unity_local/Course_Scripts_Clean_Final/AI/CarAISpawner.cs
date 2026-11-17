using UnityEngine;

namespace GTAViceCityClone.AI
{
    /// <summary>
    /// CarAISpawner instantiates traffic AI vehicles on road waypoints.
    /// Reconstructed cleanly from Episodes 36, 37.
    /// </summary>
    public class CarAISpawner : MonoBehaviour
    {
        [Header("Traffic Car Prefabs")]
        public GameObject[] carPrefabs;
        public int numberOfCarsToSpawn = 8;
        public LayerMask roadLayer;

        private void Start()
        {
            SpawnCars();
        }

        public void SpawnCars()
        {
            if (carPrefabs == null || carPrefabs.Length == 0) return;

            Waypoint[] roadWaypoints = FindObjectsByType<Waypoint>(FindObjectsSortMode.None);
            if (roadWaypoints == null || roadWaypoints.Length == 0) return;

            for (int i = 0; i < numberOfCarsToSpawn; i++)
            {
                int randomCarIndex = Random.Range(0, carPrefabs.Length);
                int randomWpIndex = Random.Range(0, roadWaypoints.Length);

                Waypoint chosenWp = roadWaypoints[randomWpIndex];
                GameObject spawnedCar = Instantiate(carPrefabs[randomCarIndex], chosenWp.transform.position, chosenWp.transform.rotation);

                var carNav = spawnedCar.GetComponent<CarNavigatorScript>();
                if (carNav != null)
                {
                    carNav.currentWaypoint = chosenWp;
                }
            }
        }
    }
}
