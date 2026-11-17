using UnityEngine;
using UnityEngine.AI;
using GTAViceCityClone.Player;

namespace GTAViceCityClone.Police
{
    /// <summary>
    /// PoliceOfficer controls police behavior: patrolling waypoints, detecting wanted player, chasing, shooting, taking damage, and death.
    /// Reconstructed cleanly from Episodes 43, 44, 45, 46, 47, 48.
    /// </summary>
    public class PoliceOfficer : MonoBehaviour
    {
        [Header("Combat Settings")]
        public float health = 80f;
        public float damagePerShot = 10f;
        public float fireRate = 1.2f;
        private float nextTimeToFire = 0f;

        [Header("Detection Ranges")]
        public float visionRadius = 25f;
        public float shootingRadius = 15f;
        public float stoppingDistance = 6f;

        [Header("State Flags")]
        public bool isChasing = false;
        public bool isDead = false;

        [Header("References")]
        private Transform playerTransform;
        private PlayerHealth playerHealth;
        private NavMeshAgent agent;
        private Animator animator;
        private PoliceWaypointNavigator patrolNavigator;

        [Header("Shooting Effects")]
        public Transform firePoint;
        public ParticleSystem muzzleFlash;

        private void Awake()
        {
            agent = GetComponent<NavMeshAgent>();
            animator = GetComponent<Animator>();
            patrolNavigator = GetComponent<PoliceWaypointNavigator>();
        }

        private void Start()
        {
            var playerObj = GameObject.FindGameObjectWithTag("Player");
            if (playerObj != null)
            {
                playerTransform = playerObj.transform;
                playerHealth = playerObj.GetComponent<PlayerHealth>();
            }
        }

        private void Update()
        {
            if (isDead || playerTransform == null) return;

            int wanted = WantedLevel.Instance != null ? WantedLevel.Instance.currentWantedLevel : 0;
            float distanceToPlayer = Vector3.Distance(transform.position, playerTransform.position);

            if (wanted > 0 && distanceToPlayer <= visionRadius)
            {
                // Player is wanted and in sight
                isChasing = true;
                if (patrolNavigator != null) patrolNavigator.enabled = false;

                if (WantedLevel.Instance != null)
                {
                    WantedLevel.Instance.playerUnderObservation = true;
                }

                if (distanceToPlayer <= shootingRadius)
                {
                    // In shooting range -> stop and engage
                    if (agent != null && agent.isActiveAndEnabled)
                    {
                        agent.SetDestination(transform.position);
                    }

                    LookAtPlayer();

                    if (Time.time >= nextTimeToFire)
                    {
                        nextTimeToFire = Time.time + (1f / fireRate);
                        ShootPlayer();
                    }

                    if (animator != null)
                    {
                        animator.SetFloat("Speed", 0f);
                        animator.SetBool("isShooting", true);
                    }
                }
                else
                {
                    // Out of shooting range -> chase player
                    if (agent != null && agent.isActiveAndEnabled)
                    {
                        agent.SetDestination(playerTransform.position);
                    }

                    if (animator != null)
                    {
                        animator.SetFloat("Speed", agent.speed);
                        animator.SetBool("isShooting", false);
                    }
                }
            }
            else
            {
                // Return to patrol
                isChasing = false;
                if (patrolNavigator != null) patrolNavigator.enabled = true;

                if (animator != null)
                {
                    animator.SetBool("isShooting", false);
                }
            }
        }

        private void LookAtPlayer()
        {
            Vector3 direction = playerTransform.position - transform.position;
            direction.y = 0f;
            if (direction != Vector3.zero)
            {
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 10f * Time.deltaTime);
            }
        }

        private void ShootPlayer()
        {
            if (muzzleFlash != null)
            {
                muzzleFlash.Play();
            }

            if (animator != null)
            {
                animator.SetTrigger("Fire");
            }

            if (playerHealth != null)
            {
                playerHealth.TakeDamage(damagePerShot);
            }
        }

        public void TakeDamage(float damage)
        {
            if (isDead) return;

            health -= damage;

            if (animator != null)
            {
                animator.SetTrigger("Hit");
            }

            // Immediately engage attacker
            isChasing = true;
            if (WantedLevel.Instance != null && WantedLevel.Instance.currentWantedLevel == 0)
            {
                WantedLevel.Instance.ReportCrime(2); // attacking a cop gives 2 stars
            }

            if (health <= 0f)
            {
                Die();
            }
        }

        private void Die()
        {
            isDead = true;

            if (animator != null)
            {
                animator.SetBool("isDead", true);
                animator.CrossFade("Die", 0.2f);
            }

            if (agent != null && agent.isActiveAndEnabled)
            {
                agent.isStopped = true;
                agent.enabled = false;
            }

            if (patrolNavigator != null)
            {
                patrolNavigator.enabled = false;
            }

            // Killing an officer increases wanted level
            if (WantedLevel.Instance != null)
            {
                WantedLevel.Instance.ReportCrime(1);
            }

            Destroy(gameObject, 12f);
        }
    }
}
