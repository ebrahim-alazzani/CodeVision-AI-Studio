using UnityEngine;
using GTAViceCityClone.UI;

namespace GTAViceCityClone.Player
{
    /// <summary>
    /// PlayerHealth manages the player's health points, damage reception, UI health bar, and death logic.
    /// Reconstructed cleanly from Episode 49.
    /// </summary>
    public class PlayerHealth : MonoBehaviour
    {
        [Header("Health Settings")]
        public float maxHealth = 100f;
        public float currentHealth;
        public bool isDead;

        [Header("UI Reference")]
        public HealthBar healthBar;

        [Header("Components")]
        private Animator animator;
        private PlayerMovement playerMovement;
        private PlayerManager playerManager;

        private void Awake()
        {
            animator = GetComponent<Animator>();
            playerMovement = GetComponent<PlayerMovement>();
            playerManager = GetComponent<PlayerManager>();
        }

        private void Start()
        {
            currentHealth = maxHealth;
            if (healthBar != null)
            {
                healthBar.SetMaxHealth(maxHealth);
            }
        }

        public void TakeDamage(float damage)
        {
            if (isDead) return;

            currentHealth -= damage;
            currentHealth = Mathf.Clamp(currentHealth, 0f, maxHealth);

            if (healthBar != null)
            {
                healthBar.SetHealth(currentHealth);
            }

            if (currentHealth <= 0f)
            {
                Die();
            }
        }

        private void Die()
        {
            isDead = true;

            if (animator != null)
            {
                animator.SetBool("isInteracting", true);
                animator.CrossFade("Die", 0.2f);
            }

            if (playerMovement != null)
            {
                playerMovement.enabled = false;
            }

            if (playerManager != null)
            {
                playerManager.enabled = false;
            }

            // Notify GameManager
            if (GameManager.Instance != null)
            {
                GameManager.Instance.OnPlayerDied();
            }
        }

        public void Heal(float amount)
        {
            if (isDead) return;

            currentHealth += amount;
            currentHealth = Mathf.Min(currentHealth, maxHealth);

            if (healthBar != null)
            {
                healthBar.SetHealth(currentHealth);
            }
        }

        public void SetHealthDirect(float health)
        {
            currentHealth = Mathf.Clamp(health, 0f, maxHealth);
            if (healthBar != null)
            {
                healthBar.SetHealth(currentHealth);
            }
            if (currentHealth <= 0f)
            {
                Die();
            }
        }
    }
}
