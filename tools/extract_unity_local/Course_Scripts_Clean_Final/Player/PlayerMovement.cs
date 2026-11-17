using UnityEngine;

namespace GTAViceCityClone.Player
{
    /// <summary>
    /// PlayerMovement handles walking, running, sprinting, jumping, falling, and landing physics.
    /// Reconstructed cleanly from Episodes 6, 7, 8, 13, 14, 15, 39, 46, 49, 71.
    /// </summary>
    [RequireComponent(typeof(Rigidbody))]
    public class PlayerMovement : MonoBehaviour
    {
        [Header("Scripts Reference")]
        [SerializeField] private InputManager inputManager;
        [SerializeField] private PlayerManager playerManager;
        [SerializeField] private AnimatorManager animatorManager;

        [Header("Movement Settings")]
        [SerializeField] public Transform camObject;
        private Rigidbody playerRigidbody;
        private Vector3 moveDirection;

        [Header("Movement Flags")]
        public bool isMoving;
        public bool isSprinting;
        public bool isGrounded;
        public bool isJumping;

        [Header("Movement Speeds")]
        public float walkingSpeed = 1.5f;
        public float runningSpeed = 5f;
        public float sprintingSpeed = 7f;
        public float rotationSpeed = 12f;

        [Header("Falling & Landing Settings")]
        public float inAirTimer;
        public float leapingVelocity = 3f;
        public float fallingVelocity = 33f;
        public float rayCastHeightOffset = 0.5f;
        public LayerMask groundLayer;

        [Header("Jump Settings")]
        public float jumpHeight = 3.5f;
        public float gravityIntensity = -15f;

        private void Awake()
        {
            inputManager = GetComponent<InputManager>();
            playerRigidbody = GetComponent<Rigidbody>();
            playerManager = GetComponent<PlayerManager>();
            animatorManager = GetComponent<AnimatorManager>();

            if (camObject == null && Camera.main != null)
            {
                camObject = Camera.main.transform;
            }
        }

        public void HandleAllMovement()
        {
            HandleFallingAndLanding();

            if (playerManager != null && playerManager.isInteracting)
                return;

            if (isJumping)
                return;

            HandleMovement();
            HandleRotation();
        }

        private void HandleMovement()
        {
            if (isJumping || inputManager == null || camObject == null)
                return;

            // Calculate movement vector aligned with camera view
            moveDirection = camObject.forward * inputManager.verticalInput;
            moveDirection += camObject.right * inputManager.horizontalInput;
            moveDirection.Normalize();
            moveDirection.y = 0f;

            if (isSprinting)
            {
                moveDirection *= sprintingSpeed;
                isMoving = inputManager.moveAmount > 0f;
            }
            else
            {
                if (inputManager.moveAmount > 0.5f)
                {
                    moveDirection *= runningSpeed;
                    isMoving = true;
                }
                else if (inputManager.moveAmount > 0f)
                {
                    moveDirection *= walkingSpeed;
                    isMoving = true;
                }
                else
                {
                    isMoving = false;
                }
            }

            Vector3 movementVelocity = moveDirection;
            movementVelocity.y = playerRigidbody.linearVelocity.y;
            playerRigidbody.linearVelocity = movementVelocity;
        }

        private void HandleRotation()
        {
            if (isJumping || inputManager == null || camObject == null)
                return;

            Vector3 targetDirection = camObject.forward * inputManager.verticalInput;
            targetDirection += camObject.right * inputManager.horizontalInput;
            targetDirection.Normalize();
            targetDirection.y = 0f;

            if (targetDirection == Vector3.zero)
            {
                targetDirection = transform.forward;
            }

            Quaternion targetRotation = Quaternion.LookRotation(targetDirection);
            Quaternion playerRotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
            transform.rotation = playerRotation;
        }

        private void HandleFallingAndLanding()
        {
            RaycastHit hit;
            Vector3 rayCastOrigin = transform.position;
            Vector3 targetPosition = transform.position;
            rayCastOrigin.y += rayCastHeightOffset;

            bool isAscendingJump = isJumping && playerRigidbody.linearVelocity.y > 0f;

            if (!isGrounded && !isJumping)
            {
                if (playerManager != null && !playerManager.isInteracting && animatorManager != null)
                {
                    animatorManager.PlayTargetAnim("Falling", true);
                }
                inAirTimer += Time.deltaTime;
                playerRigidbody.AddForce(transform.forward * leapingVelocity, ForceMode.Force);
                playerRigidbody.AddForce(-Vector3.up * fallingVelocity * inAirTimer, ForceMode.Acceleration);
            }

            if (!isAscendingJump && Physics.SphereCast(rayCastOrigin, 0.2f, -Vector3.up, out hit, rayCastHeightOffset + 0.1f, groundLayer))
            {
                if (!isGrounded && playerManager != null && !playerManager.isInteracting && animatorManager != null)
                {
                    animatorManager.PlayTargetAnim("Landing", true);
                }

                targetPosition.y = hit.point.y;
                inAirTimer = 0f;
                isGrounded = true;

                if (isJumping)
                {
                    isJumping = false;
                    if (animatorManager != null && animatorManager.animator != null)
                    {
                        animatorManager.animator.SetBool("isJumping", false);
                    }
                }
            }
            else
            {
                isGrounded = false;
            }

            if (isGrounded && !isJumping)
            {
                if ((playerManager != null && playerManager.isInteracting) || (inputManager != null && inputManager.moveAmount > 0f))
                {
                    transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime / 0.1f);
                }
                else
                {
                    transform.position = targetPosition;
                }
            }
        }

        public void HandleJumping()
        {
            if (isGrounded && !isJumping)
            {
                if (animatorManager != null)
                {
                    if (animatorManager.animator != null)
                    {
                        animatorManager.animator.SetBool("isJumping", true);
                    }
                    animatorManager.PlayTargetAnim("Jump", true);
                }

                float jumpingVelocity = Mathf.Sqrt(-2f * gravityIntensity * jumpHeight);
                Vector3 playVelocity = moveDirection;
                playVelocity.y = jumpingVelocity;
                playerRigidbody.linearVelocity = playVelocity;
                isJumping = true;
            }
        }

        public void SetIsJumping(bool jumping)
        {
            isJumping = jumping;
        }
    }
}
