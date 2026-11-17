using System.Collections;
using UnityEngine;

public class PoliceSpawner : MonoBehaviour
{
    public GameObject policePrefab;
    public Transform[] spawnPoints;
    public float spawnInterval = 10f;
    public int maxPoliceCount = 10;

    private int currentPoliceCount = 0;

    private void Start()
    {
        StartCoroutine(SpawnPoliceRoutine());
    }

    private IEnumerator SpawnPoliceRoutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(spawnInterval);

            if (WantedLevel.Instance != null && WantedLevel.Instance.currentWantedLevel > 0)
            {
                if (currentPoliceCount < maxPoliceCount && spawnPoints.Length > 0 && policePrefab != null)
                {
                    Transform spawnPoint = spawnPoints[Random.Range(0, spawnPoints.Length)];
                    Instantiate(policePrefab, spawnPoint.position, spawnPoint.rotation);
                    currentPoliceCount++;
                }
            }
        }
    }
}
