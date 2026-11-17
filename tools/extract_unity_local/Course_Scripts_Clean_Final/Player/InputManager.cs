using UnityEngine;
using UnityEngine.InputSystem;
using GTAViceCityClone.Shooting;
using GTAViceCityClone.CameraSystem;
using GTAViceCityClone.Vehicles;

namespace GTAViceCityClone.Player
{
    /// <summary>
    /// InputManager coordinates input from Unity's Input System, Keyboard, Mouse, and Mobile Touch/Joysticks.
    /// Reconstructed cleanly from Episodes 5, 6, 7, 8, 9, 11, 13, 15, 27, 28, 29, 30, 31, 39, 56, 57, 68, 69, 71, 73.
    /// </summary>
    public class InputManager : MonoBehaviour
    {
        [Header("Script References")]
        private AnimatorManager animatorManager;
        private PlayerMovement playerMovement;
        private ShootingController shootingController;
        private CameraManager cameraManager;

        [Header("Movement Input Values")]
        public float moveAmount;
        public Vector2 movementInput;
        public Vector2 cameraInput;
        public float verticalInput;
        public float horizontalInput;
        public float cameraInputX;
        public float cameraInputY;

        [Header("Action Flags")]
        public bool sprintInput;
        public bool jumpInput;
        public bool shootInput;
        public bool aimInput;
        public bool reloadInput;
        public bool scopeInput;
        public bool interactInput; // Enter/Exit Vehicle & Shop
        public bool pauseInput;

        [Header("Mobile Joystick (Optional)")]
        [SerializeField] private Joystick movementJoystick;
        [SerializeField] private Joystick cameraJoystick;

        private void Awake()
        {
            animatorManager = GetComponent<AnimatorManager>();
            playerMovement = GetComponent<PlayerMovement>();
            shootingController = GetComponent<ShootingController>();
            cameraManager = FindFirstObjectByType<CameraManager>();
        }

        private void Update()
        {
            // Legacy / standalone fallback input checks if not using new Input System asset
            HandleKeyboardMouseInputs();
        }

        private void HandleKeyboardMouseInputs()
        {
            // Keyboard movement
            float h = Input.GetAxisRaw("Horizontal");
            float v = Input.GetAxisRaw("Vertical");

            // Mobile joystick override if present and dragged
            if (movementJoystick != null && (Mathf.Abs(movementJoystick.Horizontal) > 0.1f || Mathf.Abs(movementJoystick.Vertical) > 0.1f))
            {
                h = movementJoystick.Horizontal;
                v = movementJoystick.Vertical;
            }

            movementInput = new Vector2(h, v);

            // Mouse look / Mobile camera joystick
            float mouseX = Input.GetAxis("Mouse X");
            float mouseY = Input.GetAxis("Mouse Y");

            if (cameraJoystick != null && (Mathf.Abs(cameraJoystick.Horizontal) > 0.1f || Mathf.Abs(cameraJoystick.Vertical) > 0.1f))
            {
                mouseX = cameraJoystick.Horizontal;
                mouseY = cameraJoystick.Vertical;
            }

            cameraInput = new Vector2(mouseX, mouseY);

            // Button inputs
            sprintInput = Input.GetKey(KeyCode.LeftShift);
            
            if (Input.GetKeyDown(KeyCode.Space))
            {
                jumpInput = true;
            }

            // Shooting & Aiming inputs
            shootInput = Input.GetMouseButton(0);
            aimInput = Input.GetMouseButton(1);

            if (Input.GetKeyDown(KeyCode.R))
            {
                reloadInput = true;
            }

            if (Input.GetKeyDown(KeyCode.E) || Input.GetKeyDown(KeyCode.F))
            {
                interactInput = true;
            }

            if (Input.GetKeyDown(KeyCode.Escape))
            {
                pauseInput = true;
            }

            // Weapon slot switching (1, 2, 3)
            if (Input.GetKeyDown(KeyCode.Alpha1) && shootingController != null)
            {
                shootingController.SelectWeapon(0);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha2) && shootingController != null)
            {
                shootingController.SelectWeapon(1);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha3) && shootingController != null)
            {
                shootingController.SelectWeapon(2);
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
                if (!playerMovement.isSprinting && moveAmount > 0f)
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

            playerMovement.isSprinting = sprintInput && moveAmount > 0f;
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

        #region Mobile UI Button Callbacks
        public void OnSprintButtonDown() => sprintInput = true;
        public void OnSprintButtonUp() => sprintInput = false;
        public void OnJumpButtonDown() => jumpInput = true;
        public void OnShootButtonDown() => shootInput = true;
        public void OnShootButtonUp() => shootInput = false;
        public void OnAimButtonDown() => aimInput = true;
        public void OnAimButtonUp() => aimInput = false;
        public void OnReloadButtonDown()
        {
            if (shootingController != null)
            {
                shootingController.TriggerReload();
            }
        }
        public void OnScopeButtonDown()
        {
            if (cameraManager != null)
            {
                cameraManager.ToggleScope();
            }
        }
        public void OnInteractButtonDown() => interactInput = true;
        public void OnSelectWeaponSlot(int slot)
        {
            if (shootingController != null)
            {
                shootingController.SelectWeapon(slot);
            }
        }
        #endregion
    }

    /// <summary>
    /// Lightweight base joystick class for mobile touch inputs
    /// </summary>
    public class Joystick : MonoBehaviour
    {
        public virtual float Horizontal => 0f;
        public virtual float Vertical => 0f;
    }
}
