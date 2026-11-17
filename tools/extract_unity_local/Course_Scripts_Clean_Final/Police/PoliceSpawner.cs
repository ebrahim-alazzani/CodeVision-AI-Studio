using System.Collections.Generic;
using UnityEngine;
using GTAViceCityClone.AI;

namespace GTAViceCityClone.Police
{
    /// <summary>
    /// PoliceSpawner spawns police officer units near the player when wanted level is active.
    /// Reconstructed cleanly from Episode 48.
    /// </summary>
    public class PoliceSpawner : MonoBehaviour
    {
        [Header("Spawn Settings")]
        public GameObject policePrefab;
        public float spawnInterval = 8f;
        public int maxActivePolice = 4;
        public float minSpawnRadius = 25f;
        public float maxSpawnRadius = 45f;

        private float spawnTimer = 0f;
        private Transform playerTransform;
        private List<GameObject> activeOfficers = new List<GameObject>();

        private void Start()
        {
            var player = GameObject.FindGameObjectWithTag("Player");
            if (player != null)
            {
                playerTransform = player.transform;
            }
        }

        private void Update()
        {
            if (policePrefab == null || playerTransform == null) return;

            // Clean up nulls in active list
            activeOfficers.RemoveAll(officer => officer == null);

            int wanted = WantedLevel.Instance != null ? WantedLevel.Instance.currentWantedLevel : 0;

            if (wanted > 0 && activeOfficers.Count < maxActivePolice)
            {
                spawnTimer += Time.deltaTime;
                if (spawnTimer >= spawnInterval)
                {
                    spawnTimer = 0f;
                    SpawnOfficerNearPlayer();
                }
            }
            else
            {
                spawnTimer = 0f;
            }
        }

        private void SpawnOfficerNearPlayer()
        {
            Vector2 randomCircle = Random.insideUnitCircle.normalized * Random.Range(minSpawnRadius, maxSpawnRadius);
            Vector3 spawnPosition = playerTransform.position + new Vector3(randomCircle.x, 0f, randomCircle.y);

            GameObject officer = Instantiate(policePrefab, spawnPosition, Quaternion.identity);
            activeOfficers.Add(officer);
        }
    }
}
