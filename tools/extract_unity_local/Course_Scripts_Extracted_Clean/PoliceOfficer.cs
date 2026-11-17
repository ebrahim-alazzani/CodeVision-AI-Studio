using UnityEngine;

public class PoliceOfficer : MonoBehaviour
{
    public float health = 100f;
    public float moveSpeed = 3.5f;
    public float attackRange = 2.0f;
    public float damageAmount = 10f;
    public float attackRate = 1.5f;

    private Transform playerTarget;
    private Animator animator;
    private float nextAttackTime = 0f;

    private void Start()
    {
        animator = GetComponent<Animator>();
        FindPlayer();
    }

    private void FindPlayer()
    {
        GameObject playerObj = GameObject.FindWithTag("Player");
        if (playerObj != null)
        {
            playerTarget = playerObj.transform;
        }
    }

    private void Update()
    {
        if (health <= 0) return;
        if (playerTarget == null) FindPlayer();
        if (playerTarget == null) return;

        float distance = Vector3.Distance(transform.position, playerTarget.position);

        if (distance > attackRange)
        {
            Vector3 dir = (playerTarget.position - transform.position).normalized;
            dir.y = 0;
            transform.position += dir * moveSpeed * Time.deltaTime;
            transform.rotation = Quaternion.LookRotation(dir);

            if (animator != null) animator.SetBool("isWalking", true);
        }
        else
        {
            if (animator != null) animator.SetBool("isWalking", false);

            if (Time.time >= nextAttackTime)
            {
                nextAttackTime = Time.time + attackRate;
                Attack();
            }
        }
    }

    private void Attack()
    {
        if (animator != null) animator.SetTrigger("Attack");

        PlayerHealth playerHealth = playerTarget.GetComponent<PlayerHealth>();
        if (playerHealth != null)
        {
            playerHealth.TakeDamage(damageAmount);
        }
    }

    public void TakeDamage(float amount)
    {
        health -= amount;
        if (health <= 0)
        {
            Die();
        }
    }

    private void Die()
    {
        if (animator != null) animator.SetTrigger("Die");
        GetComponent<Collider>().enabled = false;
        this.enabled = false;
        Destroy(gameObject, 5.0f);
    }
}
