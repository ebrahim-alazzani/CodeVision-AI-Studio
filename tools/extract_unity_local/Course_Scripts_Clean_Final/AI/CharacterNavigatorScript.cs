using UnityEngine;
using GTAViceCityClone.Police;

namespace GTAViceCityClone.AI
{
    /// <summary>
    /// CharacterNavigatorScript controls pedestrian AI movement, animator locomotion, health, taking damage, and death.
    /// Reconstructed cleanly from Episodes 22, 23, 33, 34, 39, 44, 46.
    /// </summary>
    public class CharacterNavigatorScript : MonoBehaviour
    {
        [Header("Movement Settings")]
        public float movementSpeed = 2.0f;
        public float rotationSpeed = 5.0f;
        public float stopDistance = 1.0f;
        public Vector3 destination;
        public bool reachedDestination = false;

        [Header("Health & Combat")]
        public float health = 50f;
        public bool isDead = false;

        [Header("Components")]
        private Animator animator;
        private CharacterController characterController;

        private void Awake()
        {
            animator = GetComponent<Animator>();
            characterController = GetComponent<CharacterController>();
        }

        private void Update()
        {
            if (isDead) return;

            Vector3 destinationDirection = destination - transform.position;
            destinationDirection.y = 0f;

            float destinationDistance = destinationDirection.magnitude;

            if (destinationDistance >= stopDistance)
            {
                reachedDestination = false;

                // Rotate towards destination
                Quaternion targetRotation = Quaternion.LookRotation(destinationDirection);
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);

                // Move forward
                Vector3 moveVelocity = transform.forward * movementSpeed;
                if (characterController != null && characterController.enabled)
                {
                    moveVelocity.y = -9.81f; // apply gravity
                    characterController.Move(moveVelocity * Time.deltaTime);
                }
                else
                {
                    transform.position += transform.forward * movementSpeed * Time.deltaTime;
                }

                if (animator != null)
                {
                    animator.SetFloat("Speed", movementSpeed);
                }
            }
            else
            {
                reachedDestination = true;
                if (animator != null)
                {
                    animator.SetFloat("Speed", 0f);
                }
            }
        }

        public void SetDestination(Vector3 target)
        {
            destination = target;
            reachedDestination = false;
        }

        public void TakeDamage(float damage)
        {
            if (isDead) return;

            health -= damage;

            if (animator != null)
            {
                animator.SetTrigger("Hit");
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

            if (characterController != null)
            {
                characterController.enabled = false;
            }

            // Report crime to WantedLevel system (1 star for murdering civilians)
            if (WantedLevel.Instance != null)
            {
                WantedLevel.Instance.ReportCrime(1);
            }

            Destroy(gameObject, 10f); // clean up body after 10s
        }
    }
}
