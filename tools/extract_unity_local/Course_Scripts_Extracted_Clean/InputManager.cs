using UnityEngine;

public class InputManager : MonoBehaviour
{
    PlayerControl playerControl;

    AnimatorManager animatorManager;
    PlayerMovement playerMovement;

    public float moveAmount;
    private Vector2 movementInput;
    private Vector2 cameraInput;

    public float verticalInput;
    public float horizontalInput;

    public float cameraInputX;
    public float cameraInputY;
    
    [Header("Input Button Flag")]
    public bool bInput;
    public bool jumpInput;

    private void Awake()
    {
        animatorManager = GetComponent<AnimatorManager>();
        playerMovement = GetComponent<PlayerMovement>();
    }

    private void OnEnable()
    {
        if (playerControl == null)
        {
            playerControl = new PlayerControl();
            playerControl.PlayerMovement.Movement.performed += i => movementInput = i.ReadValue<Vector2>();
            playerControl.PlayerMovement.CameraMovement.performed += i => cameraInput = i.ReadValue<Vector2>();
            playerControl.PlayerAction.B.performed += i => bInput = true;
            playerControl.PlayerAction.B.canceled += i => bInput = false;
            playerControl.PlayerAction.Jump.performed += i => jumpInput = true;
        }
        playerControl.Enable();
    }

    private void OnDisable()
    {
        if (playerControl != null)
        {
            playerControl.Disable();
        }
    }

    public void HandleAllInput()
    {
        HandleMovementInput();
        HandleSprintingInput();
        HandleJumpingInput();
    }

    public void HandleMovementInput()
    {
        verticalInput = movementInput.y;
        horizontalInput = movementInput.x;

        cameraInputX = cameraInput.x;
        cameraInputY = cameraInput.y;
        moveAmount = Mathf.Clamp01(Mathf.Abs(horizontalInput) + Mathf.Abs(verticalInput));

        float targetVertical = verticalInput;
        float targetHorizontal = horizontalInput;

        if (playerMovement != null)
        {
            if (!playerMovement.isSprinting && moveAmount > 0)
            {
                targetVertical *= 0.5f;
                targetHorizontal *= 0.5f;
            }

            if (animatorManager != null)
            {
                animatorManager.UpdateAnimValues(targetHorizontal, targetVertical, playerMovement.isSprinting);
            }
        }
    }

    private void HandleSprintingInput()
    {
        if (playerMovement == null) return;

        if (bInput && moveAmount > 0)
        {
            playerMovement.isSprinting = true;
        }
        else
        {
            playerMovement.isSprinting = false;
        }
    }

    private void HandleJumpingInput()
    {
        if (jumpInput)
        {
            jumpInput = false;
            if (playerMovement != null)
            {
                playerMovement.HandleJumping();
            }
        }
    }
}
