using UnityEngine;
using UnityEngine.AI;
using GTAViceCityClone.Player;

namespace GTAViceCityClone.Missions
{
    /// <summary>
    /// Guard AI for mansion security during mission shootouts.
    /// Reconstructed cleanly from Episode 62.
    /// </summary>
    public class Guard : Character
    {
        [Header("Guard AI Settings")]
        public float shootingRadius = 15f;
        public float fireRate = 1f;
        public float damage = 10f;
        private float nextFireTime = 0f;

        private Transform playerTransform;
        private PlayerHealth playerHealth;
        private NavMeshAgent agent;

        private void Start()
        {
            agent = GetComponent<NavMeshAgent>();
            var p = GameObject.FindGameObjectWithTag("Player");
            if (p != null)
            {
                playerTransform = p.transform;
                playerHealth = p.GetComponent<PlayerHealth>();
            }
        }

        private void Update()
        {
            if (isDead || playerTransform == null) return;

            float distance = Vector3.Distance(transform.position, playerTransform.position);
            if (distance <= shootingRadius)
            {
                // Look at player
                Vector3 dir = playerTransform.position - transform.position;
                dir.y = 0;
                if (dir != Vector3.zero)
                {
                    transform.rotation = Quaternion.LookRotation(dir);
                }

                if (Time.time >= nextFireTime)
                {
                    nextFireTime = Time.time + (1f / fireRate);
                    if (playerHealth != null)
                    {
                        playerHealth.TakeDamage(damage);
                    }
                }
            }
        }
    }
}
