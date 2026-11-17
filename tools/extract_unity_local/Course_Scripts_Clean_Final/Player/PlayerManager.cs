using UnityEngine;
using GTAViceCityClone.CameraSystem;

namespace GTAViceCityClone.Player
{
    /// <summary>
    /// PlayerManager coordinates lifecycle updates for Input, Movement, Animation, and Camera systems.
    /// Reconstructed cleanly from Episodes 7, 11, 14, 15, 39, 71.
    /// </summary>
    public class PlayerManager : MonoBehaviour
    {
        [Header("Script References")]
        private InputManager inputManager;
        private PlayerMovement playerMovement;
        private CameraManager cameraManager;
        private Animator animator;

        [Header("Player Status")]
        public bool isInteracting;
        public bool isDriving;

        private void Awake()
        {
            inputManager = GetComponent<InputManager>();
            playerMovement = GetComponent<PlayerMovement>();
            animator = GetComponent<Animator>();
            cameraManager = FindFirstObjectByType<CameraManager>();
        }

        private void Update()
        {
            if (isDriving) return;

            if (inputManager != null)
            {
                inputManager.HandleAllInput();
            }
        }

        private void FixedUpdate()
        {
            if (isDriving) return;

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

            if (isDriving) return;

            if (cameraManager != null)
            {
                cameraManager.HandleAllCameraMovement();
            }
        }

        public void SetDrivingState(bool driving)
        {
            isDriving = driving;
            if (animator != null)
            {
                animator.enabled = !driving;
            }
        }
    }
}
