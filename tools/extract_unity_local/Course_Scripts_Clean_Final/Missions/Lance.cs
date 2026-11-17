using UnityEngine;
using UnityEngine.AI;

namespace GTAViceCityClone.Missions
{
    /// <summary>
    /// Lance Vance companion AI who follows Tommy Vercetti during missions.
    /// Reconstructed cleanly from Episode 62.
    /// </summary>
    public class Lance : Character
    {
        [Header("Follow Settings")]
        public Transform playerTransform;
        public float followDistance = 3.5f;

        private NavMeshAgent agent;

        private void Start()
        {
            agent = GetComponent<NavMeshAgent>();
            if (playerTransform == null)
            {
                var p = GameObject.FindGameObjectWithTag("Player");
                if (p != null) playerTransform = p.transform;
            }
        }

        private void Update()
        {
            if (isDead || playerTransform == null || agent == null || !agent.isActiveAndEnabled) return;

            float distance = Vector3.Distance(transform.position, playerTransform.position);
            if (distance > followDistance)
            {
                agent.SetDestination(playerTransform.position);
            }
        }
    }
}
