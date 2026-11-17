using UnityEngine;

public class PlayerManager : MonoBehaviour
{
    InputManager inputManager;
    PlayerMovement playerMovement;
    AnimatorManager animatorManager;
    Animator animator;

    public bool isInteracting;

    private void Awake()
    {
        inputManager = GetComponent<InputManager>();
        playerMovement = GetComponent<PlayerMovement>();
        animatorManager = GetComponent<AnimatorManager>();
        animator = GetComponent<Animator>();
    }

    private void Update()
    {
        if (inputManager != null)
        {
            inputManager.HandleAllInput();
        }
    }

    private void FixedUpdate()
    {
        if (playerMovement != null)
        {
            playerMovement.HandleAllMovement();
        }
    }

    private void LateUpdate()
    {
        if (animator != null)
        {
            isInteracting = animator.GetBool("isInteracting");
        }
    }
}
