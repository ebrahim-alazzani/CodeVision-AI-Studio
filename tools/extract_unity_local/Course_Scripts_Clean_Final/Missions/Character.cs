using UnityEngine;

namespace GTAViceCityClone.Missions
{
    /// <summary>
    /// Base class for mission characters and bosses.
    /// Reconstructed cleanly from Episode 60.
    /// </summary>
    public class Character : MonoBehaviour
    {
        [Header("Character Stats")]
        public string characterName = "NPC";
        public float health = 100f;
        public bool isDead = false;

        private Animator animator;

        private void Awake()
        {
            animator = GetComponent<Animator>();
        }

        public virtual void TakeDamage(float damage)
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

        public virtual void Die()
        {
            isDead = true;
            if (animator != null)
            {
                animator.SetBool("isDead", true);
                animator.CrossFade("Die", 0.2f);
            }
        }
    }
}
