using System.Collections;
using UnityEngine;

public class AISpawner : MonoBehaviour
{
    public GameObject[] AIPrefabs;
    public int AiToSpawn;
    public int Timer = 3;

    void Start()
    {
        StartCoroutine(Spawn());
    }

    IEnumerator Spawn()
    {
        int count = 0;

        while (count < AiToSpawn)
        {
            if (AIPrefabs == null || AIPrefabs.Length == 0) yield break;

            int randomIndex = Random.Range(0, AIPrefabs.Length);
            GameObject obj = Instantiate(AIPrefabs[randomIndex]);

            if (transform.childCount > 0)
            {
                Transform child = transform.GetChild(Random.Range(0, transform.childCount));
                WaypointNavigator navigator = obj.GetComponent<WaypointNavigator>();
                if (navigator != null)
                {
                    navigator.currentWaypoint = child.GetComponent<WayPoint>();
                }
                obj.transform.position = child.position;
            }

            yield return new WaitForSeconds(Timer);
            count++;
        }
    }
}
